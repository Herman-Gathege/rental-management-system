"""Tests for tenant bulk upload with lease creation."""
from __future__ import annotations

import csv
import io

import pytest
from datetime import date

from app.services import bulk_upload_service
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.charge import Charge
from app.models.lease_inspection import LeaseInspection
from app.models.property import Property
from app.models.unit import Unit
from app.models.organization import Organization


def _to_csv_bytes(rows: list[dict], headers: list[str]) -> bytes:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({h: row.get(h, "") for h in headers})
    return out.getvalue().encode("utf-8")


class TestTenantBulkUploadLeaseCreation:
    HEADERS = [
        "full_name", "phone", "email", "alternative_phone",
        "id_number", "emergency_contact",
        "property_name", "unit", "rent_amount",
        "deposit_amount", "start_date", "end_date",
        "billing_day", "lease_status",
    ]

    def test_successful_tenant_and_lease_creation(self, db, org, property, unit, landlord_user):
        rows = [
            {
                "full_name": "John Doe",
                "phone": "0712345678",
                "email": "john@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "2027-08-31",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )
        db.commit()

        assert len(result.imported) == 1
        assert len(result.skipped) == 0

        tenant = db.query(Tenant).filter(Tenant.full_name == "John Doe").first()
        assert tenant is not None
        assert tenant.organization_id == org.id
        assert tenant.phone == "0712345678"
        assert tenant.email == "john@example.com"

        lease = db.query(Lease).filter(Lease.tenant_id == tenant.id).first()
        assert lease is not None
        assert lease.unit_id == unit.id
        assert lease.rent_amount == 35000
        assert lease.deposit_amount == 35000
        assert lease.start_date == date(2026, 9, 1)
        assert lease.end_date == date(2027, 8, 31)
        assert lease.billing_day == 1
        assert lease.status == "active"

        deposit_charge = db.query(Charge).filter(
            Charge.lease_id == lease.id, Charge.charge_type == "deposit"
        ).first()
        assert deposit_charge is not None
        assert deposit_charge.amount == 35000

        inspection = db.query(LeaseInspection).filter(
            LeaseInspection.lease_id == lease.id,
            LeaseInspection.inspection_type == "move_in",
        ).first()
        assert inspection is not None
        assert inspection.status == "draft"

    def test_multiple_tenants_with_leases(self, db, org, landlord_user):
        prop = Property(
            id="prop-1", organization_id=org.id, name="Silverleaf",
            address="123 Main", city="Nairobi", country="Kenya",
        )
        unit1 = Unit(id="unit-1", property_id="prop-1", name="A1", rent_amount=35000, is_active=True)
        unit2 = Unit(id="unit-2", property_id="prop-1", name="A2", rent_amount=25000, is_active=True)
        db.add_all([prop, unit1, unit2])
        db.flush()

        rows = [
            {
                "full_name": "Tenant One", "phone": "0711000001", "email": "t1@example.com",
                "alternative_phone": "", "id_number": "", "emergency_contact": "",
                "property_name": "Silverleaf", "unit": "A1",
                "rent_amount": "35000", "deposit_amount": "35000",
                "start_date": "2026-09-01", "end_date": "",
                "billing_day": "1", "lease_status": "active",
            },
            {
                "full_name": "Tenant Two", "phone": "0711000002", "email": "t2@example.com",
                "alternative_phone": "", "id_number": "", "emergency_contact": "",
                "property_name": "Silverleaf", "unit": "A2",
                "rent_amount": "25000", "deposit_amount": "25000",
                "start_date": "2026-09-01", "end_date": "2027-08-31",
                "billing_day": "5", "lease_status": "active",
            },
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )
        db.commit()

        assert len(result.imported) == 2
        assert len(result.skipped) == 0

        tenants = db.query(Tenant).order_by(Tenant.full_name).all()
        assert len(tenants) == 2

        leases = db.query(Lease).all()
        assert len(leases) == 2

    def test_invalid_unit_skips_row_no_tenant_created(self, db, org, landlord_user):
        rows = [
            {
                "full_name": "Bad Tenant",
                "phone": "0712999999",
                "email": "bad@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Nonexistent Property",
                "unit": "Z1",
                "rent_amount": "50000",
                "deposit_amount": "50000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "no property named" in result.skipped[0].reason.lower()

        tenant = db.query(Tenant).filter(Tenant.full_name == "Bad Tenant").first()
        assert tenant is None

    def test_duplicate_tenant_rejected(self, db, org, landlord_user):
        existing = Tenant(
            id="tenant-1", organization_id=org.id,
            full_name="Existing", phone="0712000000", email="existing@example.com",
        )
        db.add(existing)
        db.flush()

        rows = [
            {
                "full_name": "Existing",
                "phone": "0712000000",
                "email": "existing@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "already used" in result.skipped[0].reason.lower()

    def test_active_lease_conflict_rejected(self, db, org, landlord_user):
        prop = Property(
            id="prop-1", organization_id=org.id, name="Silverleaf",
            address="123 Main", city="Nairobi", country="Kenya",
        )
        unit = Unit(id="unit-1", property_id="prop-1", name="A1", rent_amount=35000, is_active=True)
        existing_tenant = Tenant(
            id="tenant-1", organization_id=org.id,
            full_name="Existing Tenant", phone="0712000000",
        )
        existing_lease = Lease(
            id="lease-1", organization_id=org.id, unit_id="unit-1",
            tenant_id="tenant-1", start_date=date(2026, 1, 1),
            rent_amount=35000, status="active",
        )
        db.add_all([prop, unit, existing_tenant, existing_lease])
        db.flush()

        rows = [
            {
                "full_name": "New Tenant",
                "phone": "0712000001",
                "email": "new@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "already has an active lease" in result.skipped[0].reason.lower()

    def test_invalid_dates_rejected(self, db, org, property, unit, landlord_user):
        rows = [
            {
                "full_name": "Date Error",
                "phone": "0712000002",
                "email": "date@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2027-01-01",
                "end_date": "2026-12-31",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "start_date must be before end_date" in result.skipped[0].reason

    def test_invalid_amounts_rejected(self, db, org, property, unit, landlord_user):
        rows = [
            {
                "full_name": "Amount Error",
                "phone": "0712000003",
                "email": "amt@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "not-a-number",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "not a valid amount" in result.skipped[0].reason.lower()

    def test_missing_required_columns_rejected(self, db, org, landlord_user):
        rows = [
            {
                "full_name": "Missing Cols",
                "phone": "0712000004",
                "email": "missing@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        bad_headers = [h for h in self.HEADERS if h != "start_date"]
        csv_bytes = _to_csv_bytes(rows, bad_headers)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "missing required column" in result.skipped[0].reason.lower()

    def test_tenant_only_backward_compatibility(self, db, org, landlord_user):
        rows = [
            {
                "full_name": "Tenant Only",
                "phone": "0712000005",
                "email": "only@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "",
                "unit": "",
                "rent_amount": "",
                "deposit_amount": "",
                "start_date": "",
                "end_date": "",
                "billing_day": "",
                "lease_status": "",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )
        db.commit()

        assert len(result.imported) == 1
        assert len(result.skipped) == 0

        tenant = db.query(Tenant).filter(Tenant.full_name == "Tenant Only").first()
        assert tenant is not None

        lease = db.query(Lease).filter(Lease.tenant_id == tenant.id).first()
        assert lease is None

    def test_organization_isolation(self, db, org, landlord_user):
        other_org = Organization(id="other-org", name="Other Org", owner_id=landlord_user.id)
        db.add(other_org)
        db.flush()

        prop = Property(
            id="prop-1", organization_id=other_org.id, name="Other Property",
            address="456 Other", city="Nairobi", country="Kenya",
        )
        unit = Unit(id="unit-1", property_id="prop-1", name="B1", rent_amount=30000, is_active=True)
        db.add_all([prop, unit])
        db.flush()

        rows = [
            {
                "full_name": "Cross Org",
                "phone": "0712000006",
                "email": "cross@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Other Property",
                "unit": "B1",
                "rent_amount": "30000",
                "deposit_amount": "30000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            }
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 0
        assert len(result.skipped) == 1
        assert "no property named" in result.skipped[0].reason.lower()

    def test_preview_returns_ready_and_error_rows(self, db, org, property, unit, landlord_user):
        rows = [
            {
                "full_name": "Good Tenant",
                "phone": "0712000007",
                "email": "good@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "2027-08-31",
                "billing_day": "1",
                "lease_status": "active",
            },
            {
                "full_name": "Bad Tenant",
                "phone": "0712000008",
                "email": "bad@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            },
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        preview = bulk_upload_service.build_tenant_preview(db, org.id, csv_bytes)

        assert preview["total_rows"] == 2
        assert preview["ready_count"] == 1
        assert preview["error_count"] == 1

        ready_row = next(r for r in preview["rows"] if r["status"] == "ready")
        assert ready_row["tenant_name"] == "Good Tenant"
        assert ready_row["unit_name"] == "A1 @ Silverleaf Apartments"
        assert ready_row["rent_amount"] == "35000"

        error_row = next(r for r in preview["rows"] if r["status"] == "error")
        assert error_row["tenant_name"] == "Bad Tenant"
        assert "already has an active lease" in error_row["reason"].lower()

    def test_csv_template_download(self):
        csv_text = bulk_upload_service.get_tenants_template_csv()
        assert "full_name" in csv_text
        assert "property_name" in csv_text
        assert "rent_amount" in csv_text

    def test_rollback_on_failure_leaves_no_partial_records(self, db, org, property, unit, landlord_user):
        rows = [
            {
                "full_name": "Good Tenant",
                "phone": "0712000009",
                "email": "good2@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            },
            {
                "full_name": "Bad Tenant",
                "phone": "0712000010",
                "email": "bad2@example.com",
                "alternative_phone": "",
                "id_number": "",
                "emergency_contact": "",
                "property_name": "Silverleaf Apartments",
                "unit": "A1",
                "rent_amount": "35000",
                "deposit_amount": "35000",
                "start_date": "2026-09-01",
                "end_date": "",
                "billing_day": "1",
                "lease_status": "active",
            },
        ]
        csv_bytes = _to_csv_bytes(rows, self.HEADERS)
        result = bulk_upload_service.parse_and_import_tenants(
            db, org.id, csv_bytes, inspector_user_id=landlord_user.id
        )

        assert len(result.imported) == 1
        assert len(result.skipped) == 1

        tenants = db.query(Tenant).all()
        assert len(tenants) == 1
        assert tenants[0].full_name == "Good Tenant"

        leases = db.query(Lease).all()
        assert len(leases) == 1
