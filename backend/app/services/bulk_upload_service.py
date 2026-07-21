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
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.unit import Unit


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

def _read_csv(csv_bytes: bytes) -> csv.DictReader:
    """Decode CSV bytes and return a DictReader with normalised headers.
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
    return reader


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


def parse_and_import_properties(
    db: Session,
    organization_id: str,
    csv_bytes: bytes,
) -> BulkUploadResult:
    reader = _read_csv(csv_bytes)
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


def parse_and_import_units(
    db: Session,
    organization_id: str,
    csv_bytes: bytes,
) -> BulkUploadResult:
    reader = _read_csv(csv_bytes)
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
