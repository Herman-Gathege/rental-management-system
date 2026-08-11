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
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.encryption import blind_index
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


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
                {"row_number": r.row_number, "identifier": r.identifier}
                for r in self.imported
            ],
            "skipped": [
                {
                    "row_number": r.row_number,
                    "identifier": r.identifier,
                    "reason": r.reason,
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


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _parse_int(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"'{value}' is not a valid whole number")


def _parse_float(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"'{value}' is not a valid number")


def _parse_decimal_required(value: str, field_name: str) -> Decimal:
    if not value:
        raise ValueError(f"{field_name} is required")
    try:
        return Decimal(value)
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
]
TENANT_REQUIRED_HEADERS = {"full_name", "phone"}


def get_tenants_template_csv() -> str:
    """Header + example rows for the downloadable tenant template."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(TENANT_TEMPLATE_HEADERS)
    writer.writerow([
        "Alice Wanjiku", "0712345678", "alice@example.com",
        "0722333444", "12345678", "Bob Wanjiku — +254 722 000 111",
    ])
    writer.writerow([
        "James Karanja", "0733444555", "james@example.com",
        "", "", "",
    ])
    return out.getvalue()


def get_tenants_template_xlsx() -> bytes:
    """Header + example rows for the downloadable tenant Excel template."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(TENANT_TEMPLATE_HEADERS)
    ws.append(["Alice Wanjiku", "0712345678", "alice@example.com", "0722333444", "12345678", "Bob Wanjiku — +254 722 000 111"])
    ws.append(["James Karanja", "0733444555", "james@example.com", "", "", ""])
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


def parse_and_import_tenants(
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

    missing = TENANT_REQUIRED_HEADERS - set(reader.fieldnames)
    if missing:
        result.skipped.append(RowResult(
            1, "",
            f"Missing required column(s): {', '.join(sorted(missing))}",
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

    # ── Duplicates within the CSV ──────────────────────────────────────
    seen_phone_in_csv: set[str] = set()
    seen_alt_phone_in_csv: set[str] = set()
    seen_email_in_csv: set[str] = set()
    seen_id_in_csv: set[str] = set()

    for i, row in enumerate(reader, start=2):
        full_name = _clean(row.get("full_name"))
        phone = _clean(row.get("phone"))
        email = _clean(row.get("email")) or None
        alternative_phone = _clean(row.get("alternative_phone")) or None
        id_number = _clean(row.get("id_number")) or None
        emergency_contact = _clean(row.get("emergency_contact")) or None

        identifier = full_name or phone or f"(row {i})"
        result.total_rows += 1

        if not full_name:
            result.skipped.append(RowResult(i, identifier, "full_name is required"))
            continue
        if not phone:
            result.skipped.append(RowResult(i, identifier, "phone is required"))
            continue

        phone_hash = blind_index(phone)
        alt_phone_hash = blind_index(alternative_phone) if alternative_phone else None
        email_hash = blind_index(email) if email else None
        id_hash = blind_index(id_number) if id_number else None

        # ── Required field checks ──────────────────────────────────────
        if not phone_hash:
            result.skipped.append(RowResult(i, identifier, "phone is required"))
            continue

        # ── Landlord phone rejection ───────────────────────────────────
        if _normalize_phone(phone) in landlord_normalized_phones:
            result.skipped.append(RowResult(
                i, identifier,
                "This phone number belongs to a landlord in this organization",
            ))
            continue
        if alternative_phone and _normalize_phone(alternative_phone) in landlord_normalized_phones:
            result.skipped.append(RowResult(
                i, identifier,
                "This alternative phone number belongs to a landlord in this organization",
            ))
            continue

        # ── Uniqueness checks ──────────────────────────────────────────
        if phone_hash in existing_phone_hashes or phone_hash in existing_alt_phone_hashes:
            result.skipped.append(RowResult(
                i, identifier,
                "phone is already used by another tenant in this organization",
            ))
            continue
        if alt_phone_hash and (alt_phone_hash in existing_phone_hashes or alt_phone_hash in existing_alt_phone_hashes):
            result.skipped.append(RowResult(
                i, identifier,
                "alternative_phone is already used by another tenant in this organization",
            ))
            continue
        if email_hash and email_hash in existing_email_hashes:
            result.skipped.append(RowResult(
                i, identifier,
                "email is already used by another tenant in this organization",
            ))
            continue
        if id_hash and id_hash in existing_id_hashes:
            result.skipped.append(RowResult(
                i, identifier,
                "id_number is already used by another tenant in this organization",
            ))
            continue

        # ── Duplicate within CSV ───────────────────────────────────────
        if phone_hash in seen_phone_in_csv or phone_hash in seen_alt_phone_in_csv:
            result.skipped.append(RowResult(
                i, identifier, "duplicate phone within this file",
            ))
            continue
        if alt_phone_hash and (alt_phone_hash in seen_phone_in_csv or alt_phone_hash in seen_alt_phone_in_csv):
            result.skipped.append(RowResult(
                i, identifier, "duplicate alternative_phone within this file",
            ))
            continue
        if email_hash and email_hash in seen_email_in_csv:
            result.skipped.append(RowResult(
                i, identifier, "duplicate email within this file",
            ))
            continue
        if id_hash and id_hash in seen_id_in_csv:
            result.skipped.append(RowResult(
                i, identifier, "duplicate id_number within this file",
            ))
            continue

        # ── Build tenant ───────────────────────────────────────────────
        tenant = Tenant(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            full_name=full_name,
            email=email,
            phone=phone,
            alternative_phone=alternative_phone,
            id_number=id_number,
            emergency_contact=emergency_contact,
        )

        db.add(tenant)
        seen_phone_in_csv.add(phone_hash)
        if alt_phone_hash:
            seen_alt_phone_in_csv.add(alt_phone_hash)
        if email_hash:
            seen_email_in_csv.add(email_hash)
        if id_hash:
            seen_id_in_csv.add(id_hash)
        result.imported.append(RowResult(i, identifier))

    return result
