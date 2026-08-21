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

Matching strategy (Sprint 7.1 — review-item-first):
  1. Reference lookup: the M-Pesa reference from the statement is matched
     against payment_review_items (created from WhatsApp payment evidence).
     If a review item with a tenant_id is found, the tenant, phone, and lease
     are taken from that record.
  2. Phone fallback: if no review-item match is found, the payer phone
     (after "TIMESTAMP:") identifies the tenant -> tenant.phone,
     compared on the last 9 local digits so 0724…/254724…/+254724… all match.

The M-Pesa code (the token after the ACC number) is the transaction
reference, stored on the payment and used for duplicate detection.

Sprint 6.2 (#7) — deposit awareness in preview:
  When a matched row lands on a lease with an outstanding deposit charge, we
  compare row.amount against the remaining deposit balance. If the row can't
  cover the deposit in full, it's flagged as `insufficient_first_payment`
  instead of `matched`. Rule from spec:
    - New tenant, first payment MUST cover at least the full deposit.
    - Partial deposits are not allowed.
  Commit-time also enforces this — preview is a heads-up so the landlord
  doesn't waste a click on Record. Split (deposit + rent) happens at commit.
"""
import csv
import io
import re
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.charge import Charge
from app.models.payment_review_item import PaymentReviewItem
from app.core.encryption import blind_index, decrypt_value

# "MPESA TO ACC 0100316372900 UDTQS2OHFR TIMESTAMP: 254724735509 TO 0100316372900"
_CODE_RE = re.compile(r"ACC\s+\d+\s+([A-Z0-9-]+)\s+TIMESTAMP", re.IGNORECASE)
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


def _deposit_outstanding_by_lease(db: Session, org_id: str) -> dict:
    """Return {lease_id: remaining_deposit_balance} for every lease in the org
    whose deposit charge(s) aren't fully paid. Sums across deposit charges in
    case a lease somehow has multiple (data drift). Excludes leases whose
    deposit is fully paid so the caller can do a simple `if lease_id in dict`.
    """
    balances = {}
    rows = (
        db.query(
            Charge.lease_id,
            func.coalesce(func.sum(Charge.amount - Charge.amount_paid), 0).label("remaining"),
        )
        .filter(
            Charge.organization_id == org_id,
            Charge.charge_type == "deposit",
        )
        .group_by(Charge.lease_id)
        .all()
    )
    for lease_id, remaining in rows:
        remaining = float(remaining or 0)
        # Small tolerance for float noise around 0.
        if remaining > 0.01:
            balances[lease_id] = remaining
    return balances


def build_preview(db: Session, org_id: str, parsed: list) -> dict:
    """Match parsed rows to tenants (review-item-first) + active leases. No DB writes.

    Per-row status:
      matched                       -> tenant + single active lease, amount OK
      insufficient_first_payment    -> matched lease has outstanding deposit and
                                       row.amount < deposit balance
      multiple_leases               -> tenant found, >1 active lease (needs pick)
      no_active_lease               -> tenant found, no active lease
      unmatched                     -> no tenant found
      duplicate                     -> M-Pesa reference already recorded
      parse_error                   -> couldn't read amount from the row

    Matching strategy:
      1. Reference lookup: match the M-Pesa reference against payment_review_items
         in the same org. If a review item with tenant_id is found, the tenant,
         phone, and lease are taken from that record.
      2. Phone fallback: if no review-item match, fall back to the existing
         phone-based tenant lookup.
    """
    tenants = db.query(Tenant).filter(Tenant.organization_id == org_id).all()
    by_hash = {}
    for t in tenants:
        for raw in (t.phone, t.alternative_phone):
            if not raw:
                continue
            plain = decrypt_value(raw)
            if not plain:
                continue
            h = blind_index(plain)
            if h:
                by_hash[h] = t
            digits = re.sub(r"[^\d]", "", plain)
            if digits:
                h2 = blind_index(digits)
                if h2:
                    by_hash[h2] = t

    review_items_by_ref = {
        ri.reference: ri
        for ri in (
            db.query(PaymentReviewItem)
            .filter(
                PaymentReviewItem.organization_id == org_id,
                PaymentReviewItem.tenant_id.isnot(None),
            )
            .all()
        )
        if ri.reference
    }

    # Load deposit-outstanding map once for the whole preview.
    deposit_outstanding = _deposit_outstanding_by_lease(db, org_id)

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
            "deposit_outstanding": None,  # populated for insufficient_first_payment
        }

        if not p["amount"]:
            item["status"] = "parse_error"
            results.append(item)
            continue

        tenant = None
        phone = p["phone"]

        # ─── Step 1: reference -> payment_review_items ───
        review_item = None
        if p["reference"]:
            review_item = review_items_by_ref.get(p["reference"])
            if review_item:
                phone = review_item.payer_phone or phone
                if review_item.tenant_id:
                    tenant = next(
                        (t for t in tenants if t.id == review_item.tenant_id),
                        None,
                    )
                    item["whatsapp_matches"].append({
                        "review_item_id": review_item.id,
                        "source": review_item.source,
                        "message_timestamp": review_item.message_timestamp.isoformat() if review_item.message_timestamp else None,
                        "payer_name": review_item.payer_name,
                    })

        # ─── Step 2: phone fallback if no review-item match ───
        if not tenant and phone:
            phone_hash = blind_index(phone)
            tenant = by_hash.get(phone_hash)
            if not tenant:
                digits_only = re.sub(r"[^\d]", "", phone or "")
                if digits_only:
                    tenant = by_hash.get(blind_index(digits_only))

        if tenant:
            item["tenant_id"] = tenant.id
            item["tenant_name"] = tenant.full_name
            item["phone"] = phone or item["phone"]

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

        # Determine lease: prefer review-item lease, then active leases for tenant.
        lease_id = None
        if review_item and review_item.lease_id:
            lease_id = review_item.lease_id
        else:
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
                lease_id = active_leases[0].id
            elif len(active_leases) > 1:
                item["status"] = "multiple_leases"
                item["lease_options"] = [
                    {
                        "lease_id": l.id,
                        "unit_id": l.unit_id,
                        "rent_amount": float(l.rent_amount) if l.rent_amount is not None else None,
                        # Include deposit-outstanding per option so the frontend
                        # can render an inline warning against the specific
                        # lease the landlord picks.
                        "deposit_outstanding": deposit_outstanding.get(l.id),
                    }
                    for l in active_leases
                ]
                results.append(item)
                continue

        if lease_id:
            # ─── Sprint 6.2 (#7): first-payment-must-cover-deposit check ───
            # If this lease still owes on its deposit and the row can't cover
            # the balance, flag it. Commit-time enforces this too — preview
            # is a heads-up.
            deposit_remaining = deposit_outstanding.get(lease_id)
            if deposit_remaining and float(p["amount"]) < deposit_remaining:
                item["status"] = "insufficient_first_payment"
                item["lease_id"] = lease_id
                item["deposit_outstanding"] = deposit_remaining
                results.append(item)
                continue

            item["status"] = "matched"
            item["lease_id"] = lease_id
            # Attach deposit_outstanding on matched rows too so the frontend
            # can hint "Will be split: KES X to deposit, KES Y to rent" in the
            # preview row. Optional to display.
            if deposit_remaining:
                item["deposit_outstanding"] = deposit_remaining
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
