# backend/app/services/payment_batch_service.py
"""
CSV batch payment ingestion — parsing + matching (Sprint 4.5 spinoff).

This module is the read-only half: parse a bank / M-Pesa statement CSV and
match each row to a tenant + active lease, producing a review report. It writes
NOTHING to the database — committing matched rows into payments is a separate
step (payment_batch service.commit_batch / the /commit route) so the user can
review and fix flagged rows before any money is recorded.

Expected statement format (headers: Date, Transaction, Currency, Deposit):
    29/04/2026,"MPESA TO ACC 0100316372900 UDTQS2OHFR TIMESTAMP: 254724735509 TO 0100316372900","KES","26,000.00"

Matching strategy:
  - The payer phone (after "TIMESTAMP:") identifies the tenant -> tenant.phone,
    compared on the last 9 local digits so 0724…/254724…/+254724… all match.
  - The M-Pesa code (the token after the ACC number) is the transaction
    reference, stored on the payment and used for duplicate detection.

Sprint 7 cleanup: tenant lookup now runs BEFORE the duplicate check so
duplicates still surface the tenant name — previously the early `continue`
on duplicate rows meant a row we KNEW belonged to a specific tenant showed
their column as blank, which made the review UI look broken.
"""
import csv
import io
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.payment import Payment
from app.core.encryption import blind_index, decrypt_value

# "MPESA TO ACC 0100316372900 UDTQS2OHFR TIMESTAMP: 254724735509 TO 0100316372900"
_CODE_RE = re.compile(r"ACC\s+\d+\s+([A-Z0-9]+)\s+TIMESTAMP", re.IGNORECASE)
_PHONE_RE = re.compile(r"TIMESTAMP:\s*(\d+)")


def _norm_phone(raw):
    """Reduce any phone format to its last 9 local digits for matching.
    254724735509 / 0724735509 / +254 724 735509 -> 724735509"""
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None
    return digits[-9:] if len(digits) >= 9 else digits


def _parse_amount(raw):
    if raw is None:
        return None
    cleaned = str(raw).replace(",", "").strip().strip('"')
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_date(raw):
    raw = (raw or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_statement(content: bytes) -> list:
    """Parse the statement CSV into raw row dicts. Tolerant of a header row and
    blank lines; extracts date / amount / M-Pesa code / payer phone per row."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader]
    if not rows:
        return []

    # Skip a header row if the first row looks like headers.
    start = 0
    header = [str(c).strip().lower() for c in rows[0]]
    if "date" in header and ("transaction" in header or "deposit" in header):
        start = 1

    parsed = []
    line_no = start
    for row in rows[start:]:
        line_no += 1
        if not row or all(not str(c).strip() for c in row):
            continue

        date_raw = row[0] if len(row) > 0 else ""
        txn = row[1] if len(row) > 1 else ""
        # Deposit is column index 3; fall back to the last column.
        amount_raw = row[3] if len(row) > 3 else (row[-1] if row else "")

        code_m = _CODE_RE.search(txn or "")
        phone_m = _PHONE_RE.search(txn or "")

        parsed.append({
            "row": line_no,
            "date": _parse_date(date_raw),
            "amount": _parse_amount(amount_raw),
            "reference": code_m.group(1) if code_m else None,
            "phone": phone_m.group(1) if phone_m else None,
            "raw": (txn or "").strip(),
        })
    return parsed


def build_preview(db: Session, org_id: str, parsed: list) -> dict:
    """Match parsed rows to tenants (by phone) + active leases. No DB writes.

    Per-row status:
      matched         -> tenant found, exactly one active lease (ready to record)
      multiple_leases  -> tenant found, >1 active lease (needs manual lease pick)
      no_active_lease  -> tenant found, no active lease (needs review)
      unmatched       -> no tenant for that phone (needs review)
      duplicate       -> M-Pesa reference already recorded (skip)
      parse_error     -> couldn't read amount/phone from the row

    Sprint 7 cleanup: tenant lookup runs first so duplicates and other
    non-terminal statuses still surface the tenant name.
    """
    tenants = db.query(Tenant).filter(Tenant.organization_id == org_id).all()
    # Build a lookup by normalized phone hash. We hash both the raw phone
    # string and the digits-only variant so "+254725123456" and "254725123456"
    # both resolve to the same tenant.
    by_hash = {}
    for t in tenants:
        for raw in (t.phone, t.alternative_phone):
            if not raw:
                continue
            # raw is Fernet ciphertext; decrypt to get the stored form.
            plain = decrypt_value(raw)
            if not plain:
                continue
            h = blind_index(plain)
            if h:
                by_hash[h] = t
            # Also index the digits-only form.
            digits = re.sub(r"[^\d]", "", plain)
            if digits:
                h2 = blind_index(digits)
                if h2:
                    by_hash[h2] = t

    results = []
    for p in parsed:
        item = {
            "row": p["row"],
            "date": p["date"].isoformat() if p["date"] else None,
            "amount": p["amount"],
            "reference": p["reference"],
            "phone": p["phone"],
            "raw": p["raw"],
            "status": None,
            "tenant_id": None,
            "tenant_name": None,
            "lease_id": None,
            "lease_options": [],
            "whatsapp_matches": [],
        }

        if not p["amount"] or not p["phone"]:
            item["status"] = "parse_error"
            results.append(item)
            continue

        # ─── Sprint 7 cleanup: tenant lookup FIRST ───
        # Populate tenant on the item BEFORE any early-return on duplicate,
        # so duplicates still show who the CSV belongs to. If phone doesn't
        # match anyone in the org, tenant stays None and status will fall
        # through to 'unmatched' below.
        phone_hash = blind_index(p["phone"])
        tenant = by_hash.get(phone_hash)
        if not tenant:
            digits_only = re.sub(r"[^\d]", "", p["phone"] or "")
            if digits_only:
                tenant = by_hash.get(blind_index(digits_only))
        if tenant:
            item["tenant_id"] = tenant.id
            item["tenant_name"] = tenant.full_name

        # Duplicate reference check — takes precedence over unmatched /
        # multi-lease / etc. since a payment already exists.
        if p["reference"]:
            already = (
                db.query(Payment.id)
                .filter(
                    Payment.organization_id == org_id,
                    Payment.reference == p["reference"],
                )
                .first()
            )
            if already:
                item["status"] = "duplicate"
                results.append(item)
                continue

        # No tenant matched → nothing else to say.
        if not tenant:
            item["status"] = "unmatched"
            results.append(item)
            continue

        # Tenant matched, no duplicate — decide on lease.
        active_leases = (
            db.query(Lease)
            .filter(
                Lease.tenant_id == tenant.id,
                Lease.organization_id == org_id,
                Lease.status == "active",
            )
            .all()
        )

        if len(active_leases) == 1:
            item["status"] = "matched"
            item["lease_id"] = active_leases[0].id
        elif len(active_leases) > 1:
            item["status"] = "multiple_leases"
            item["lease_options"] = [
                {
                    "lease_id": l.id,
                    "unit_id": l.unit_id,
                    "rent_amount": float(l.rent_amount) if l.rent_amount is not None else None,
                }
                for l in active_leases
            ]
        else:
            item["status"] = "no_active_lease"

        results.append(item)

    summary = {}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1

    return {
        "total_rows": len(results),
        "summary": summary,
        "rows": results,
    }


# ─── Sprint 7 cleanup: downloadable template ─────────────────────────────

def get_batch_payment_template_csv() -> str:
    """Return the M-Pesa statement CSV template as a string.

    Mirrors the exact format the parser expects — Date, Transaction, Currency,
    Deposit columns; Transaction contains the ACC/reference/TIMESTAMP payload
    with the payer phone. The sample rows are illustrative so a user opening
    the file in Excel sees what a real row looks like; delete them before
    uploading a real statement.
    """
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Date", "Transaction", "Currency", "Deposit"])
    writer.writerow([
        "29/04/2026",
        "MPESA TO ACC 0100316372900 UDTQS2OHFR TIMESTAMP: 254724735509 TO 0100316372900",
        "KES",
        "26,000.00",
    ])
    writer.writerow([
        "30/04/2026",
        "MPESA TO ACC 0100316372900 UDTQS2OHG1 TIMESTAMP: 254711223344 TO 0100316372900",
        "KES",
        "15,500.00",
    ])
    writer.writerow([
        "01/05/2026",
        "MPESA TO ACC 0100316372900 UDTQS2OHG5 TIMESTAMP: 254799887766 TO 0100316372900",
        "KES",
        "32,000.00",
    ])
    return out.getvalue()
