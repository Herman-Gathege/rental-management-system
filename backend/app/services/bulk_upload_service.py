#backend\app\services\bulk_upload_service.py
"""
Bulk upload service — Sprint 7 cleanup (Batch 2).

Parses CSV files and creates rows with per-row validation. Invalid rows are
skipped (not fatal) — the caller gets a report of what was imported and
what was skipped, with row numbers and reasons.

Supported entities:
  - Properties (name, address, city, country)
  - Units (property_name → property_id lookup, name, description,
    bedrooms, bathrooms, size_sqm, rent_amount)
  - Tenants (full_name, phone, email, alternative_phone, id_number,
    emergency_contact)

Design decisions:
  - CSV only (universal, plays nicely with M-Pesa / bank exports later).
  - Duplicate detection is case-insensitive on the identifying name field,
    scoped to the calling organization.
  - Header row must be present. Headers are normalised (lowercased,
    trimmed, spaces → underscores) so users can be a little sloppy.
  - The service does NOT commit — callers (route handlers) do, so that
    audit logs and imports go in one transaction.
"""
from __future__ import annotations

import csv
import io
import openpyxl
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.encryption import blind_index
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.charge import Charge
from app.services.inspection_service import create_inspection_for_lease
from app.services.billing_service import recompute_lease_settlement


class _SpreadsheetReader:
    def __init__(self, fieldnames: list[str], rows: list[dict]):
        self.fieldnames = fieldnames
        self._rows = rows
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._rows):
            raise StopIteration
        row = self._rows[self._index]
        self._index += 1
        return row


# ─── Result types ─────────────────────────────────────────────────────────

@dataclass
class RowResult:
    row_number: int   # 1-based; row 1 is the header, first data row is 2
    identifier: str   # user-friendly label for reporting ("Silverleaf Apartments")
    reason: str = ""  # populated when skipped

    # Lease preview / result fields
    tenant_name: str = ""
    unit_name: str = ""
    rent_amount: str = ""
    deposit_amount: str = ""
    start_date: str = ""
    end_date: str = ""
    billing_day: str = ""
    lease_status: str = ""
    status: str = ""  # "ready" or "error"


@dataclass
class BulkUploadResult:
    imported: List[RowResult] = field(default_factory=list)
    skipped: List[RowResult] = field(default_factory=list)
    total_rows: int = 0

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "imported_count": len(self.imported),
            "skipped_count": len(self.skipped),
            "imported": [
                {
                    "row_number": r.row_number,
                    "identifier": r.identifier,
                    "tenant_name": r.tenant_name,
                    "unit_name": r.unit_name,
                    "rent_amount": r.rent_amount,
                    "deposit_amount": r.deposit_amount,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "billing_day": r.billing_day,
                    "lease_status": r.lease_status,
                    "status": r.status,
                }
                for r in self.imported
            ],
            "skipped": [
                {
                    "row_number": r.row_number,
                    "identifier": r.identifier,
                    "reason": r.reason,
                    "tenant_name": r.tenant_name,
                    "unit_name": r.unit_name,
                    "rent_amount": r.rent_amount,
                    "deposit_amount": r.deposit_amount,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "billing_day": r.billing_day,
                    "lease_status": r.lease_status,
                    "status": r.status,
                }
                for r in self.skipped
            ],
        }


# ─── Shared helpers ───────────────────────────────────────────────────────

def _read_csv(csv_bytes: bytes) -> _SpreadsheetReader:
    """Decode CSV bytes and return a SpreadsheetReader with normalised headers.
    utf-8-sig handles the Excel BOM without leaving a leading \ufeff in the
    first column name (a subtle footgun if not caught)."""
    try:
        text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = csv_bytes.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [
            (f or "").strip().lower().replace(" ", "_")
            for f in reader.fieldnames
        ]
    rows = list(reader)
    return _SpreadsheetReader(reader.fieldnames, rows)


def _read_excel(csv_bytes: bytes) -> _SpreadsheetReader:
    """Read an .xlsx file and return a SpreadsheetReader with normalised headers."""
    wb = openpyxl.load_workbook(io.BytesIO(csv_bytes))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return _SpreadsheetReader([], [])
    headers = [
        (str(h or "").strip().lower().replace(" ", "_"))
        for h in rows[0]
    ]
    data = []
    for row in rows[1:]:
        data.append(dict(zip(headers, row)))
    return _SpreadsheetReader(headers, data)


def _read_spreadsheet(csv_bytes: bytes) -> _SpreadsheetReader:
    """Auto-detect format (CSV or XLSX) and return a SpreadsheetReader."""
    if csv_bytes.startswith(b"PK"):
        return _read_excel(csv_bytes)
    return _read_csv(csv_bytes)


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_int(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value.replace(",", "").replace(" ", ""))
    except ValueError:
        raise ValueError(f"'{value}' is not a valid whole number")


def _parse_float(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value.replace(",", "").replace(" ", ""))
    except ValueError:
        raise ValueError(f"'{value}' is not a valid number")


def _parse_decimal_required(value: str, field_name: str) -> Decimal:
    if not value:
        raise ValueError(f"{field_name} is required")
    try:
        return Decimal(value.replace(",", "").replace(" ", ""))
    except InvalidOperation:
        raise ValueError(f"'{value}' is not a valid amount for {field_name}")


# ─── Properties ───────────────────────────────────────────────────────────

PROPERTY_TEMPLATE_HEADERS = ["name", "address", "city", "country"]


def get_properties_template_csv() -> str:
    """Header + a couple of example rows for the downloadable template."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(PROPERTY_TEMPLATE_HEADERS)
    writer.writerow(
        ["Silverleaf Apartments", "123 Riverside Drive", "Nairobi", "Kenya"]
    )
    writer.writerow(
        ["Baobab Court", "45 Ngong Road", "Nairobi", "Kenya"]
    )
    return out.getvalue()


def get_properties_template_xlsx() -> bytes:
    """Header + a couple of example rows for the downloadable Excel template."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(PROPERTY_TEMPLATE_HEADERS)
    ws.append(["Silverleaf Apartments", "123 Riverside Drive", "Nairobi", "Kenya"])
    ws.append(["Baobab Court", "45 Ngong Road", "Nairobi", "Kenya"])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def parse_and_import_properties(
    db: Session,
    organization_id: str,
    csv_bytes: bytes,
) -> BulkUploadResult:
    reader = _read_spreadsheet(csv_bytes)
    result = BulkUploadResult()

    if not reader.fieldnames:
        result.skipped.append(
            RowResult(1, "", "CSV is empty or has no header row")
        )
        return result

    missing = set(PROPERTY_TEMPLATE_HEADERS) - set(reader.fieldnames)
    if missing:
        result.skipped.append(RowResult(
            1, "",
            f"Missing required column(s): {', '.join(sorted(missing))}",
        ))
        return result

    # Existing property names in this org (case-insensitive) for duplicate check.
    existing_names = {
        (name or "").strip().lower()
        for (name,) in db.query(Property.name)
        .filter(Property.organization_id == organization_id)
        .all()
    }

    # Duplicates WITHIN the CSV itself (e.g. two rows named "Silverleaf").
    seen_in_csv: set[str] = set()

    for i, row in enumerate(reader, start=2):  # row 1 is the header
        name = _clean(row.get("name"))
        address = _clean(row.get("address"))
        city = _clean(row.get("city"))
        country = _clean(row.get("country"))

        identifier = name or f"(row {i})"
        result.total_rows += 1

        if not name:
            result.skipped.append(RowResult(i, identifier, "name is required"))
            continue
        if not address:
            result.skipped.append(RowResult(i, identifier, "address is required"))
            continue
        if not city:
            result.skipped.append(RowResult(i, identifier, "city is required"))
            continue
        if not country:
            result.skipped.append(RowResult(i, identifier, "country is required"))
            continue

        name_key = name.lower()
        if name_key in existing_names:
            result.skipped.append(RowResult(
                i, identifier,
                "a property with this name already exists in your organization",
            ))
            continue
        if name_key in seen_in_csv:
            result.skipped.append(RowResult(
                i, identifier, "duplicate name within this file",
            ))
            continue

        prop = Property(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=name,
            address=address,
            city=city,
            country=country,
        )
        db.add(prop)
        seen_in_csv.add(name_key)
        result.imported.append(RowResult(i, name))

    return result


# ─── Units ────────────────────────────────────────────────────────────────

UNIT_TEMPLATE_HEADERS = [
    "property_name",
    "name",
    "description",
    "bedrooms",
    "bathrooms",
    "size_sqm",
    "rent_amount",
]
UNIT_REQUIRED_HEADERS = {"property_name", "name", "rent_amount"}


def get_units_template_csv() -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(UNIT_TEMPLATE_HEADERS)
    writer.writerow([
        "Silverleaf Apartments", "A1",
        "Corner unit, ground floor",
        "2", "1", "65.5", "35000",
    ])
    writer.writerow([
        "Silverleaf Apartments", "A2",
        "",
        "1", "1", "45", "25000",
    ])
    writer.writerow([
        "Baobab Court", "House 3",
        "",
        "3", "2", "120", "60000",
    ])
    return out.getvalue()


def get_units_template_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(UNIT_TEMPLATE_HEADERS)
    ws.append(["Silverleaf Apartments", "A1", "Corner unit, ground floor", 2, 1, 65.5, 35000])
    ws.append(["Silverleaf Apartments", "A2", "", 1, 1, 45, 25000])
    ws.append(["Baobab Court", "House 3", "", 3, 2, 120, 60000])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def parse_and_import_units(
    db: Session,
    organization_id: str,
    csv_bytes: bytes,
) -> BulkUploadResult:
    reader = _read_spreadsheet(csv_bytes)
    result = BulkUploadResult()

    if not reader.fieldnames:
        result.skipped.append(
            RowResult(1, "", "CSV is empty or has no header row")
        )
        return result

    missing = UNIT_REQUIRED_HEADERS - set(reader.fieldnames)
    if missing:
        result.skipped.append(RowResult(
            1, "",
            f"Missing required column(s): {', '.join(sorted(missing))}",
        ))
        return result

    # Build a property lookup for this org: normalised_name -> property_id.
    property_lookup = {
        (name or "").strip().lower(): pid
        for (pid, name) in db.query(Property.id, Property.name)
        .filter(Property.organization_id == organization_id)
        .all()
    }

    # Existing (property_id, unit_name_lower) pairs — used for duplicate checks.
    # Scoped to units whose property is in this org.
    existing_unit_keys: set[tuple[str, str]] = set()
    for (pid, uname) in (
        db.query(Unit.property_id, Unit.name)
        .join(Property, Property.id == Unit.property_id)
        .filter(Property.organization_id == organization_id)
        .all()
    ):
        existing_unit_keys.add((pid, (uname or "").strip().lower()))

    # Duplicates WITHIN the CSV itself.
    seen_in_csv: set[tuple[str, str]] = set()

    for i, row in enumerate(reader, start=2):
        property_name = _clean(row.get("property_name"))
        name = _clean(row.get("name"))
        description = _clean(row.get("description")) or None

        # User-friendly identifier for error rows.
        if name and property_name:
            identifier = f"{name} @ {property_name}"
        else:
            identifier = name or property_name or f"(row {i})"

        result.total_rows += 1

        if not property_name:
            result.skipped.append(RowResult(i, identifier, "property_name is required"))
            continue
        if not name:
            result.skipped.append(RowResult(i, identifier, "name is required"))
            continue

        property_id = property_lookup.get(property_name.lower())
        if not property_id:
            result.skipped.append(RowResult(
                i, identifier,
                f"no property named '{property_name}' in your organization",
            ))
            continue

        # Parse numeric fields — collect errors as skips, don't abort the file.
        try:
            bedrooms = _parse_int(_clean(row.get("bedrooms")))
            bathrooms = _parse_int(_clean(row.get("bathrooms")))
            size_sqm = _parse_float(_clean(row.get("size_sqm")))
            rent_amount = _parse_decimal_required(_clean(row.get("rent_amount")), "rent_amount")
        except ValueError as e:
            result.skipped.append(RowResult(i, identifier, str(e)))
            continue

        unit_key = (property_id, name.lower())
        if unit_key in existing_unit_keys:
            result.skipped.append(RowResult(
                i, identifier,
                "a unit with this name already exists in this property",
            ))
            continue
        if unit_key in seen_in_csv:
            result.skipped.append(RowResult(
                i, identifier, "duplicate unit within this file",
            ))
            continue

        unit = Unit(
            id=str(uuid.uuid4()),
            property_id=property_id,
            name=name,
            description=description,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            size_sqm=size_sqm,
            rent_amount=rent_amount,
            is_active=True,
        )
        db.add(unit)
        seen_in_csv.add(unit_key)
        result.imported.append(RowResult(i, identifier))

    return result


# ─── Tenants ────────────────────────────────────────────────────────────────

TENANT_TEMPLATE_HEADERS = [
    "full_name",
    "phone",
    "email",
    "alternative_phone",
    "id_number",
    "emergency_contact",
    # Lease onboarding columns (optional — tenant-only imports still work)
    "property_name",
    "unit",
    "rent_amount",
    "deposit_amount",
    "start_date",
    "end_date",
    "billing_day",
    "lease_status",
]
TENANT_REQUIRED_HEADERS = {"full_name", "phone"}
LEASE_REQUIRED_HEADERS = {"property_name", "unit", "rent_amount", "start_date"}
LEASE_COLUMNS = set(TENANT_TEMPLATE_HEADERS[len(TENANT_REQUIRED_HEADERS):])


def get_tenants_template_csv() -> str:
    """Header + example rows for the downloadable tenant template."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(TENANT_TEMPLATE_HEADERS)
    writer.writerow([
        "Alice Wanjiku", "0712345678", "alice@example.com",
        "0722333444", "12345678", "Bob Wanjiku — +254 722 000 111",
        "Silverleaf Apartments", "A1", "35000", "35000", "2026-09-01", "2027-08-31", "1", "active",
    ])
    writer.writerow([
        "James Karanja", "0733444555", "james@example.com",
        "", "", "",
        "", "", "", "", "", "", "", "",
    ])
    return out.getvalue()


def get_tenants_template_xlsx() -> bytes:
    """Header + example rows for the downloadable tenant Excel template."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(TENANT_TEMPLATE_HEADERS)
    ws.append(["Alice Wanjiku", "0712345678", "alice@example.com", "0722333444", "12345678", "Bob Wanjiku — +254 722 000 111", "Silverleaf Apartments", "A1", 35000, 35000, "2026-09-01", "2027-08-31", 1, "active"])
    ws.append(["James Karanja", "0733444555", "james@example.com", "", "", "", "", "", "", "", "", "", "", ""])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _normalize_phone(phone: str) -> str:
    """Reduce a phone to its canonical subscriber form for equality comparison.
    Mirrors the tenant route helper so bulk upload enforces the same rule."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("254"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
    return digits


def _parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"'{value}' is not a valid date (expected YYYY-MM-DD)")


def _has_lease_columns(fieldnames: list[str]) -> bool:
    return bool(set(fieldnames) & LEASE_COLUMNS)


def _validate_tenant_row(
    row: dict,
    row_number: int,
    existing_hashes: dict[str, set[str]],
    landlord_phones: set[str],
    seen_in_csv: dict[str, set[str]],
) -> tuple[Optional[dict], str, str]:
    full_name = _clean(row.get("full_name"))
    phone = _clean(row.get("phone"))
    email = _clean(row.get("email")) or None
    alternative_phone = _clean(row.get("alternative_phone")) or None
    id_number = _clean(row.get("id_number")) or None
    emergency_contact = _clean(row.get("emergency_contact")) or None

    identifier = full_name or phone or f"(row {row_number})"

    if not full_name:
        return None, identifier, "full_name is required"
    if not phone:
        return None, identifier, "phone is required"

    phone_hash = blind_index(phone)
    alt_phone_hash = blind_index(alternative_phone) if alternative_phone else None
    email_hash = blind_index(email) if email else None
    id_hash = blind_index(id_number) if id_number else None

    if not phone_hash:
        return None, identifier, "phone is required"

    if _normalize_phone(phone) in landlord_phones:
        return None, identifier, "This phone number belongs to a landlord in this organization"
    if alternative_phone and _normalize_phone(alternative_phone) in landlord_phones:
        return None, identifier, "This alternative phone number belongs to a landlord in this organization"

    if phone_hash in existing_hashes["phone"] or phone_hash in existing_hashes["alt_phone"]:
        return None, identifier, "phone is already used by another tenant in this organization"
    if alt_phone_hash and (alt_phone_hash in existing_hashes["phone"] or alt_phone_hash in existing_hashes["alt_phone"]):
        return None, identifier, "alternative_phone is already used by another tenant in this organization"
    if email_hash and email_hash in existing_hashes["email"]:
        return None, identifier, "email is already used by another tenant in this organization"
    if id_hash and id_hash in existing_hashes["id_number"]:
        return None, identifier, "id_number is already used by another tenant in this organization"

    if phone_hash in seen_in_csv["phone"] or phone_hash in seen_in_csv["alt_phone"]:
        return None, identifier, "duplicate phone within this file"
    if alt_phone_hash and (alt_phone_hash in seen_in_csv["phone"] or alt_phone_hash in seen_in_csv["alt_phone"]):
        return None, identifier, "duplicate alternative_phone within this file"
    if email_hash and email_hash in seen_in_csv["email"]:
        return None, identifier, "duplicate email within this file"
    if id_hash and id_hash in seen_in_csv["id_number"]:
        return None, identifier, "duplicate id_number within this file"

    return {
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "alternative_phone": alternative_phone,
        "id_number": id_number,
        "emergency_contact": emergency_contact,
    }, identifier, ""


def _validate_lease_row(
    row: dict,
    row_number: int,
    property_name_to_id: dict[str, str],
    unit_lookup: dict[tuple[str, str], str],
    active_lease_unit_ids: set[str],
    seen_lease_unit_ids_in_csv: set[str],
) -> tuple[Optional[dict], str, str]:
    property_name = _clean(row.get("property_name"))
    unit_name = _clean(row.get("unit"))
    rent_amount_raw = _clean(row.get("rent_amount"))
    deposit_amount_raw = _clean(row.get("deposit_amount"))
    start_date_raw = _clean(row.get("start_date"))
    end_date_raw = _clean(row.get("end_date"))
    billing_day_raw = _clean(row.get("billing_day"))
    lease_status_raw = _clean(row.get("lease_status"))

    identifier = f"{unit_name} @ {property_name}" if unit_name and property_name else (unit_name or property_name or f"(row {row_number})")

    lease_fields = [property_name, unit_name, rent_amount_raw, deposit_amount_raw, start_date_raw, end_date_raw, billing_day_raw, lease_status_raw]
    if not any(lease_fields):
        return None, identifier, ""

    if not property_name:
        return None, identifier, "property_name is required for lease"
    if not unit_name:
        return None, identifier, "unit is required for lease"

    try:
        rent_amount = _parse_decimal_required(rent_amount_raw, "rent_amount")
    except ValueError as e:
        return None, identifier, str(e)

    deposit_amount = None
    if deposit_amount_raw:
        try:
            deposit_amount = Decimal(deposit_amount_raw.replace(",", "").replace(" ", ""))
        except InvalidOperation:
            return None, identifier, f"'{deposit_amount_raw}' is not a valid amount for deposit_amount"

    start_date = None
    if start_date_raw:
        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        except ValueError:
            return None, identifier, f"'{start_date_raw}' is not a valid date for start_date (expected YYYY-MM-DD)"

    end_date = None
    if end_date_raw:
        try:
            end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
        except ValueError:
            return None, identifier, f"'{end_date_raw}' is not a valid date for end_date (expected YYYY-MM-DD)"

    if start_date and end_date and start_date >= end_date:
        return None, identifier, "start_date must be before end_date"

    if not start_date:
        return None, identifier, "start_date is required for lease"

    billing_day = 1
    if billing_day_raw:
        try:
            billing_day = int(billing_day_raw)
            if billing_day < 1 or billing_day > 31:
                return None, identifier, "billing_day must be between 1 and 31"
        except ValueError:
            return None, identifier, f"'{billing_day_raw}' is not a valid whole number for billing_day"

    lease_status = "active"
    if lease_status_raw:
        lease_status = lease_status_raw.lower()
        valid_statuses = {"active", "ended", "terminated", "pending_inspection"}
        if lease_status not in valid_statuses:
            return None, identifier, f"lease_status must be one of: {', '.join(sorted(valid_statuses))}"

    property_id = property_name_to_id.get(property_name.lower())
    if not property_id:
        return None, identifier, f"no property named '{property_name}' in your organization"

    unit_key = (property_id, unit_name.lower())
    unit_id = unit_lookup.get(unit_key)
    if not unit_id:
        return None, identifier, f"no unit named '{unit_name}' in property '{property_name}'"

    if unit_id in active_lease_unit_ids or unit_id in seen_lease_unit_ids_in_csv:
        return None, identifier, f"Unit {unit_name} already has an active lease"

    return {
        "unit_id": unit_id,
        "unit_name": f"{unit_name} @ {property_name}",
        "rent_amount": rent_amount,
        "deposit_amount": deposit_amount,
        "start_date": start_date,
        "end_date": end_date,
        "billing_day": billing_day,
        "status": lease_status,
    }, identifier, ""


def _create_lease_for_row(
    db: Session,
    organization_id: str,
    tenant: Tenant,
    lease_data: dict,
    inspector_user_id: Optional[str] = None,
) -> Lease:
    lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        unit_id=lease_data["unit_id"],
        tenant_id=tenant.id,
        start_date=lease_data["start_date"],
        end_date=lease_data["end_date"],
        move_in_date=lease_data["start_date"],
        rent_amount=lease_data["rent_amount"],
        deposit_amount=lease_data["deposit_amount"] or 0,
        billing_day=lease_data["billing_day"],
        status=lease_data["status"],
    )
    db.add(lease)
    db.flush()

    deposit_amt = float(lease_data["deposit_amount"] or 0)
    if deposit_amt > 0:
        today = date.today()
        deposit_charge = Charge(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            lease_id=lease.id,
            amount=deposit_amt,
            amount_paid=0,
            charge_type="deposit",
            due_date=today,
            billing_month=today,
            status="pending",
        )
        db.add(deposit_charge)
        db.flush()
        recompute_lease_settlement(db, lease.id)

    create_inspection_for_lease(
        db=db,
        lease_id=lease.id,
        organization_id=organization_id,
        inspection_type="move_in",
        inspector_user_id=inspector_user_id,
    )

    return lease


def parse_and_import_tenants(
    db: Session,
    organization_id: str,
    csv_bytes: bytes,
    inspector_user_id: Optional[str] = None,
) -> BulkUploadResult:
    reader = _read_spreadsheet(csv_bytes)
    result = BulkUploadResult()

    if not reader.fieldnames:
        result.skipped.append(
            RowResult(1, "", "CSV is empty or has no header row")
        )
        return result

    missing = TENANT_REQUIRED_HEADERS - set(reader.fieldnames)
    if missing:
        result.skipped.append(RowResult(
            1, "",
            f"Missing required column(s): {', '.join(sorted(missing))}",
        ))
        return result

    lease_mode = _has_lease_columns(reader.fieldnames)
    if lease_mode:
        missing_lease = LEASE_REQUIRED_HEADERS - set(reader.fieldnames)
        if missing_lease:
            result.skipped.append(RowResult(
                1, "",
                f"Lease columns detected but missing required column(s): {', '.join(sorted(missing_lease))}",
            ))
            return result

    # ── Pre-fetch existing tenant hashes for uniqueness checks ──────────
    existing_phone_hashes: set[str] = set()
    existing_alt_phone_hashes: set[str] = set()
    existing_email_hashes: set[str] = set()
    existing_id_hashes: set[str] = set()

    for row in (
        db.query(Tenant.phone_hash, Tenant.alternative_phone_hash,
                 Tenant.email_hash, Tenant.id_number_hash)
        .filter(Tenant.organization_id == organization_id)
        .all()
    ):
        if row[0]:
            existing_phone_hashes.add(row[0])
        if row[1]:
            existing_alt_phone_hashes.add(row[1])
        if row[2]:
            existing_email_hashes.add(row[2])
        if row[3]:
            existing_id_hashes.add(row[3])

    existing_hashes = {
        "phone": existing_phone_hashes,
        "alt_phone": existing_alt_phone_hashes,
        "email": existing_email_hashes,
        "id_number": existing_id_hashes,
    }

    # ── Pre-fetch landlord phone hashes for rejection check ─────────────
    from app.models.users import User
    from app.models.role import Role
    from app.models.organization_member import OrganizationMember
    from app.core.roles import LANDLORD

    landlord_normalized_phones: set[str] = set()
    for (raw_phone,) in (
        db.query(User.phone)
        .join(OrganizationMember, OrganizationMember.user_id == User.id)
        .join(Role, Role.id == OrganizationMember.role_id)
        .filter(
            OrganizationMember.organization_id == organization_id,
            Role.name == LANDLORD,
            User.phone.isnot(None),
        )
        .all()
    ):
        landlord_normalized_phones.add(_normalize_phone(raw_phone))

    # ── Pre-fetch units / properties for lease resolution ───────────────
    unit_lookup: dict[tuple[str, str], str] = {}
    property_name_to_id: dict[str, str] = {}
    if lease_mode:
        for (pid, pname) in (
            db.query(Property.id, Property.name)
            .filter(Property.organization_id == organization_id)
            .all()
        ):
            property_name_to_id[(pname or "").strip().lower()] = pid

        for (uid, pid, uname) in (
            db.query(Unit.id, Unit.property_id, Unit.name)
            .join(Property, Property.id == Unit.property_id)
            .filter(Property.organization_id == organization_id)
            .all()
        ):
            unit_lookup[(pid, (uname or "").strip().lower())] = uid

        active_lease_unit_ids = {
            unit_id for (unit_id,) in
            db.query(Lease.unit_id).filter(Lease.status == "active").all()
        }

    # ── Duplicates within the CSV ──────────────────────────────────────
    seen_phone_in_csv: set[str] = set()
    seen_alt_phone_in_csv: set[str] = set()
    seen_email_in_csv: set[str] = set()
    seen_id_in_csv: set[str] = set()
    seen_lease_unit_ids_in_csv: set[str] = set()

    for i, row in enumerate(reader, start=2):
        full_name = _clean(row.get("full_name"))
        phone = _clean(row.get("phone"))
        email = _clean(row.get("email")) or None
        alternative_phone = _clean(row.get("alternative_phone")) or None
        id_number = _clean(row.get("id_number")) or None
        emergency_contact = _clean(row.get("emergency_contact")) or None

        identifier = full_name or phone or f"(row {i})"
        result.total_rows += 1

        # ── Validate tenant ─────────────────────────────────────────────
        tenant_data, tenant_identifier, tenant_error = _validate_tenant_row(
            row, i, existing_hashes, landlord_normalized_phones,
            {
                "phone": seen_phone_in_csv,
                "alt_phone": seen_alt_phone_in_csv,
                "email": seen_email_in_csv,
                "id_number": seen_id_in_csv,
            },
        )
        if tenant_error:
            result.skipped.append(RowResult(i, identifier, tenant_error))
            continue

        # ── Validate lease (if lease columns present) ───────────────────
        lease_data = None
        lease_error = ""
        if lease_mode:
            lease_data, lease_identifier, lease_error = _validate_lease_row(
                row, i, property_name_to_id, unit_lookup,
                active_lease_unit_ids, seen_lease_unit_ids_in_csv,
            )
            if lease_error:
                result.skipped.append(RowResult(i, identifier, lease_error))
                # Track tenant hashes so a later row with the same tenant info
                # is still flagged as duplicate within the CSV.
                phone_hash = blind_index(phone)
                alt_phone_hash = blind_index(alternative_phone) if alternative_phone else None
                email_hash = blind_index(email) if email else None
                id_hash = blind_index(id_number) if id_number else None
                seen_phone_in_csv.add(phone_hash)
                if alt_phone_hash:
                    seen_alt_phone_in_csv.add(alt_phone_hash)
                if email_hash:
                    seen_email_in_csv.add(email_hash)
                if id_hash:
                    seen_id_in_csv.add(id_hash)
                continue

        # ── Build tenant ───────────────────────────────────────────────
        tenant = Tenant(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            full_name=tenant_data["full_name"],
            email=tenant_data["email"],
            phone=tenant_data["phone"],
            alternative_phone=tenant_data["alternative_phone"],
            id_number=tenant_data["id_number"],
            emergency_contact=tenant_data["emergency_contact"],
        )
        db.add(tenant)

        phone_hash = blind_index(phone)
        alt_phone_hash = blind_index(alternative_phone) if alternative_phone else None
        email_hash = blind_index(email) if email else None
        id_hash = blind_index(id_number) if id_number else None
        seen_phone_in_csv.add(phone_hash)
        if alt_phone_hash:
            seen_alt_phone_in_csv.add(alt_phone_hash)
        if email_hash:
            seen_email_in_csv.add(email_hash)
        if id_hash:
            seen_id_in_csv.add(id_hash)

        # ── Build lease (if lease data present) ─────────────────────────
        if lease_data:
            lease = _create_lease_for_row(
                db, organization_id, tenant, lease_data, inspector_user_id
            )
            seen_lease_unit_ids_in_csv.add(lease_data["unit_id"])
            result.imported.append(RowResult(
                i, identifier,
                tenant_name=tenant_data["full_name"],
                unit_name=lease_data["unit_name"],
                rent_amount=str(lease_data["rent_amount"]),
                deposit_amount=str(lease_data["deposit_amount"]) if lease_data["deposit_amount"] else "",
                start_date=lease_data["start_date"].isoformat() if lease_data["start_date"] else "",
                end_date=lease_data["end_date"].isoformat() if lease_data["end_date"] else "",
                billing_day=str(lease_data["billing_day"]),
                lease_status=lease_data["status"],
                status="ready",
            ))
        else:
            result.imported.append(RowResult(
                i, identifier,
                tenant_name=tenant_data["full_name"],
                status="ready",
            ))

    return result


def build_tenant_preview(
    db: Session,
    organization_id: str,
    csv_bytes: bytes,
) -> dict:
    """Validate a tenant CSV and return a preview of what would be imported.
    
    Read-only: no DB writes. Returns per-row tenant + lease preview data.
    """
    reader = _read_spreadsheet(csv_bytes)

    if not reader.fieldnames:
        return {
            "total_rows": 0,
            "ready_count": 0,
            "error_count": 0,
            "rows": [
                {
                    "row_number": 1,
                    "identifier": "",
                    "status": "error",
                    "reason": "CSV is empty or has no header row",
                    "tenant_name": "",
                    "unit_name": "",
                    "rent_amount": "",
                    "deposit_amount": "",
                    "start_date": "",
                    "end_date": "",
                    "billing_day": "",
                    "lease_status": "",
                }
            ],
        }

    missing = TENANT_REQUIRED_HEADERS - set(reader.fieldnames)
    if missing:
        return {
            "total_rows": 0,
            "ready_count": 0,
            "error_count": 0,
            "rows": [
                {
                    "row_number": 1,
                    "identifier": "",
                    "status": "error",
                    "reason": f"Missing required column(s): {', '.join(sorted(missing))}",
                    "tenant_name": "",
                    "unit_name": "",
                    "rent_amount": "",
                    "deposit_amount": "",
                    "start_date": "",
                    "end_date": "",
                    "billing_day": "",
                    "lease_status": "",
                }
            ],
        }

    lease_mode = _has_lease_columns(reader.fieldnames)
    if lease_mode:
        missing_lease = LEASE_REQUIRED_HEADERS - set(reader.fieldnames)
        if missing_lease:
            return {
                "total_rows": 0,
                "ready_count": 0,
                "error_count": 0,
                "rows": [
                    {
                        "row_number": 1,
                        "identifier": "",
                        "status": "error",
                        "reason": f"Lease columns detected but missing required column(s): {', '.join(sorted(missing_lease))}",
                        "tenant_name": "",
                        "unit_name": "",
                        "rent_amount": "",
                        "deposit_amount": "",
                        "start_date": "",
                        "end_date": "",
                        "billing_day": "",
                        "lease_status": "",
                    }
                ],
            }

    # ── Pre-fetch existing tenant hashes ──────────────────────────────
    existing_phone_hashes: set[str] = set()
    existing_alt_phone_hashes: set[str] = set()
    existing_email_hashes: set[str] = set()
    existing_id_hashes: set[str] = set()

    for row in (
        db.query(Tenant.phone_hash, Tenant.alternative_phone_hash,
                 Tenant.email_hash, Tenant.id_number_hash)
        .filter(Tenant.organization_id == organization_id)
        .all()
    ):
        if row[0]:
            existing_phone_hashes.add(row[0])
        if row[1]:
            existing_alt_phone_hashes.add(row[1])
        if row[2]:
            existing_email_hashes.add(row[2])
        if row[3]:
            existing_id_hashes.add(row[3])

    existing_hashes = {
        "phone": existing_phone_hashes,
        "alt_phone": existing_alt_phone_hashes,
        "email": existing_email_hashes,
        "id_number": existing_id_hashes,
    }

    # ── Pre-fetch landlord phones ─────────────────────────────────────
    from app.models.users import User
    from app.models.role import Role
    from app.models.organization_member import OrganizationMember
    from app.core.roles import LANDLORD

    landlord_normalized_phones: set[str] = set()
    for (raw_phone,) in (
        db.query(User.phone)
        .join(OrganizationMember, OrganizationMember.user_id == User.id)
        .join(Role, Role.id == OrganizationMember.role_id)
        .filter(
            OrganizationMember.organization_id == organization_id,
            Role.name == LANDLORD,
            User.phone.isnot(None),
        )
        .all()
    ):
        landlord_normalized_phones.add(_normalize_phone(raw_phone))

    # ── Pre-fetch units / properties / active leases ──────────────────
    unit_lookup: dict[tuple[str, str], str] = {}
    property_name_to_id: dict[str, str] = {}
    active_lease_unit_ids: set[str] = set()
    if lease_mode:
        for (pid, pname) in (
            db.query(Property.id, Property.name)
            .filter(Property.organization_id == organization_id)
            .all()
        ):
            property_name_to_id[(pname or "").strip().lower()] = pid

        for (uid, pid, uname) in (
            db.query(Unit.id, Unit.property_id, Unit.name)
            .join(Property, Property.id == Unit.property_id)
            .filter(Property.organization_id == organization_id)
            .all()
        ):
            unit_lookup[(pid, (uname or "").strip().lower())] = uid

        active_lease_unit_ids = {
            unit_id for (unit_id,) in
            db.query(Lease.unit_id).filter(Lease.status == "active").all()
        }

    # ── Validate each row ─────────────────────────────────────────────
    seen_phone_in_csv: set[str] = set()
    seen_alt_phone_in_csv: set[str] = set()
    seen_email_in_csv: set[str] = set()
    seen_id_in_csv: set[str] = set()
    seen_lease_unit_ids_in_csv: set[str] = set()

    rows = []
    for i, row in enumerate(reader, start=2):
        full_name = _clean(row.get("full_name"))
        phone = _clean(row.get("phone"))

        identifier = full_name or phone or f"(row {i})"

        tenant_data, tenant_identifier, tenant_error = _validate_tenant_row(
            row, i, existing_hashes, landlord_normalized_phones,
            {
                "phone": seen_phone_in_csv,
                "alt_phone": seen_alt_phone_in_csv,
                "email": seen_email_in_csv,
                "id_number": seen_id_in_csv,
            },
        )
        if tenant_error:
            rows.append({
                "row_number": i,
                "identifier": identifier,
                "status": "error",
                "reason": tenant_error,
                "tenant_name": "",
                "unit_name": "",
                "rent_amount": "",
                "deposit_amount": "",
                "start_date": "",
                "end_date": "",
                "billing_day": "",
                "lease_status": "",
            })
            continue

        lease_data = None
        lease_error = ""
        if lease_mode:
            lease_data, lease_identifier, lease_error = _validate_lease_row(
                row, i, property_name_to_id, unit_lookup,
                active_lease_unit_ids, seen_lease_unit_ids_in_csv,
            )
            if lease_error:
                rows.append({
                    "row_number": i,
                    "identifier": identifier,
                    "status": "error",
                    "reason": lease_error,
                    "tenant_name": tenant_data["full_name"],
                    "unit_name": "",
                    "rent_amount": "",
                    "deposit_amount": "",
                    "start_date": "",
                    "end_date": "",
                    "billing_day": "",
                    "lease_status": "",
                })
                phone_hash = blind_index(phone)
                alt_phone_hash = blind_index(tenant_data["alternative_phone"]) if tenant_data["alternative_phone"] else None
                email_hash = blind_index(tenant_data["email"]) if tenant_data["email"] else None
                id_hash = blind_index(tenant_data["id_number"]) if tenant_data["id_number"] else None
                seen_phone_in_csv.add(phone_hash)
                if alt_phone_hash:
                    seen_alt_phone_in_csv.add(alt_phone_hash)
                if email_hash:
                    seen_email_in_csv.add(email_hash)
                if id_hash:
                    seen_id_in_csv.add(id_hash)
                continue

        phone_hash = blind_index(phone)
        alt_phone_hash = blind_index(tenant_data["alternative_phone"]) if tenant_data["alternative_phone"] else None
        email_hash = blind_index(tenant_data["email"]) if tenant_data["email"] else None
        id_hash = blind_index(tenant_data["id_number"]) if tenant_data["id_number"] else None
        seen_phone_in_csv.add(phone_hash)
        if alt_phone_hash:
            seen_alt_phone_in_csv.add(alt_phone_hash)
        if email_hash:
            seen_email_in_csv.add(email_hash)
        if id_hash:
            seen_id_in_csv.add(id_hash)

        if lease_data:
            seen_lease_unit_ids_in_csv.add(lease_data["unit_id"])

        rows.append({
            "row_number": i,
            "identifier": identifier,
            "status": "ready",
            "reason": "",
            "tenant_name": tenant_data["full_name"],
            "unit_name": lease_data["unit_name"] if lease_data else "",
            "rent_amount": str(lease_data["rent_amount"]) if lease_data else "",
            "deposit_amount": str(lease_data["deposit_amount"]) if lease_data and lease_data["deposit_amount"] else "",
            "start_date": lease_data["start_date"].isoformat() if lease_data and lease_data["start_date"] else "",
            "end_date": lease_data["end_date"].isoformat() if lease_data and lease_data["end_date"] else "",
            "billing_day": str(lease_data["billing_day"]) if lease_data else "",
            "lease_status": lease_data["status"] if lease_data else "",
        })

    ready_count = sum(1 for r in rows if r["status"] == "ready")
    error_count = sum(1 for r in rows if r["status"] == "error")
    return {
        "total_rows": len(rows),
        "ready_count": ready_count,
        "error_count": error_count,
        "rows": rows,
    }
