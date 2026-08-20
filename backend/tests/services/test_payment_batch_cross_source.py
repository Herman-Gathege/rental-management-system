"""Tests for CSV ↔ WhatsApp cross-source matching."""
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.tenant import Tenant
from app.models.users import User
from app.models.role import Role
from app.models.organization_member import OrganizationMember
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.payment_review_item import PaymentReviewItem
from app.services.payment_reconciliation_service import find_whatsapp_match, save_review_items
from app.services.messaging.inbound_handler import handle_inbound_message
from app.services import payment_batch_service


@pytest.fixture
def org(db: Session, landlord_user):
    org = Organization(id=str(uuid.uuid4()), name="Test Org", owner_id=landlord_user.id)
    db.add(org)
    db.flush()
    return org


@pytest.fixture
def landlord_role(db: Session):
    role = Role(id=str(uuid.uuid4()), name="landlord")
    db.add(role)
    db.flush()
    return role


@pytest.fixture
def landlord_user(db: Session):
    user = User(id=str(uuid.uuid4()), email="landlord@test.com", full_name="Landlord", password_hash="test-hash")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def landlord_membership(db: Session, org, landlord_user, landlord_role):
    member = OrganizationMember(
        id=str(uuid.uuid4()),
        user_id=landlord_user.id,
        organization_id=org.id,
        role_id=landlord_role.id,
    )
    db.add(member)
    db.flush()
    return member


@pytest.fixture
def tenant_record(db: Session, org):
    phone = "+254725123456"
    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        full_name="Test Tenant",
        phone=phone,
        alternative_phone=None,
        email=None,
        id_number=None,
    )
    db.add(tenant)
    db.flush()
    return tenant


@pytest.fixture
def active_lease(db: Session, org, tenant_record):
    lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        unit_id=str(uuid.uuid4()),
        tenant_id=tenant_record.id,
        start_date=datetime(2026, 1, 1).date(),
        end_date=None,
        rent_amount=25000,
        status="active",
    )
    db.add(lease)
    db.flush()
    return lease


class TestCrossSourceMatching:
    def test_reference_match_finds_whatsapp_evidence(self, db: Session, org, tenant_record, landlord_membership):
        ref = "MATCH-REF-001"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=None,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_membership.user_id,
        )
        db.add(review_item)
        db.flush()

        matches = find_whatsapp_match(
            db=db,
            organization_id=org.id,
            reference=ref,
            tenant_id=tenant_record.id,
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
        )
        assert len(matches) == 1
        assert matches[0].id == review_item.id

    def test_no_match_when_reference_differs(self, db: Session, org, tenant_record, landlord_membership):
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference="OTHER-REF",
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference="OTHER-REF",
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=None,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_membership.user_id,
        )
        db.add(review_item)
        db.flush()

        matches = find_whatsapp_match(
            db=db,
            organization_id=org.id,
            reference="DIFFERENT-REF",
            tenant_id=tenant_record.id,
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
        )
        assert len(matches) == 0

    def test_amount_mismatch_does_not_auto_match(self, db: Session, org, tenant_record, landlord_membership):
        ref = "AMT-MISMATCH-REF"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=None,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_membership.user_id,
        )
        db.add(review_item)
        db.flush()

        # Different amount — should not match because we filter by exact amount.
        matches = find_whatsapp_match(
            db=db,
            organization_id=org.id,
            reference=ref,
            tenant_id=tenant_record.id,
            amount=30000,
            payment_date=datetime(2026, 1, 15).date(),
        )
        assert len(matches) == 0

    def test_date_tolerance_allows_match(self, db: Session, org, tenant_record, landlord_membership):
        ref = "DATE-TOL-REF"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 18).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 18, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=None,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_membership.user_id,
        )
        db.add(review_item)
        db.flush()

        # CSV date is 3 days later — should still match within tolerance.
        matches = find_whatsapp_match(
            db=db,
            organization_id=org.id,
            reference=ref,
            tenant_id=tenant_record.id,
            amount=25000,
            payment_date=datetime(2026, 1, 18).date(),
        )
        assert len(matches) == 1

    def test_whatsapp_evidence_created_before_csv(self, db: Session, org, tenant_record):
        wa_msg = {
            "provider_message_id": f"wamid.{uuid.uuid4().hex}",
            "from_phone": "254725123456",
            "sender_name": "Test",
            "message_type": "text",
            "body": "UAVO15EI8G 25479****032 - TIMOTHY **",
            "timestamp": datetime.utcnow(),
        }
        result = handle_inbound_message(db, org.id, wa_msg)
        db.commit()

        assert result["payment_review_item_id"] is not None

        wa_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert wa_item is not None
        assert wa_item.source == "whatsapp"
        assert wa_item.reference == "UAVO15EI8G"


class TestBatchPreviewReviewItemMatching:
    def test_reference_match_uses_review_item_tenant(self, db: Session, org, tenant_record, active_lease, landlord_user):
        ref = "BATCH-REF-001"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_user.id,
        )
        db.add(review_item)
        db.flush()

        csv_content = (
            "Date,Transaction,Currency,Deposit\n"
            "15/01/2026,MPESA TO ACC 0100316372900 BATCH-REF-001 TIMESTAMP: 254725123456 TO 0100316372900,KES,25000.00\n"
        ).encode("utf-8")
        parsed = payment_batch_service.parse_statement(csv_content)
        preview = payment_batch_service.build_preview(db, org.id, parsed)

        assert preview["total_rows"] == 1
        row = preview["rows"][0]
        assert row["status"] == "matched"
        assert row["tenant_id"] == tenant_record.id
        assert row["tenant_name"] == "Test Tenant"
        assert row["lease_id"] == active_lease.id
        assert row["amount"] == 25000.0
        assert len(row["whatsapp_matches"]) == 1
        assert row["whatsapp_matches"][0]["review_item_id"] == review_item.id

    def test_reference_match_falls_back_to_phone_when_no_review_item(self, db: Session, org, tenant_record, active_lease):
        csv_content = (
            "Date,Transaction,Currency,Deposit\n"
            "15/01/2026,MPESA TO ACC 0100316372900 UNKNOWN-REF TIMESTAMP: 254725123456 TO 0100316372900,KES,25000.00\n"
        ).encode("utf-8")
        parsed = payment_batch_service.parse_statement(csv_content)
        preview = payment_batch_service.build_preview(db, org.id, parsed)

        assert preview["total_rows"] == 1
        row = preview["rows"][0]
        assert row["status"] == "matched"
        assert row["tenant_id"] == tenant_record.id
        assert row["tenant_name"] == "Test Tenant"
        assert row["lease_id"] == active_lease.id

    def test_reference_match_without_lease_falls_through_to_active_lease_lookup(
        self, db: Session, org, tenant_record, active_lease, landlord_user
    ):
        ref = "BATCH-REF-LEASE-LOOKUP"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=None,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_user.id,
        )
        db.add(review_item)
        db.flush()

        csv_content = (
            "Date,Transaction,Currency,Deposit\n"
            "15/01/2026,MPESA TO ACC 0100316372900 BATCH-REF-LEASE-LOOKUP TIMESTAMP: 254725123456 TO 0100316372900,KES,25000.00\n"
        ).encode("utf-8")
        parsed = payment_batch_service.parse_statement(csv_content)
        preview = payment_batch_service.build_preview(db, org.id, parsed)

        assert preview["total_rows"] == 1
        row = preview["rows"][0]
        assert row["status"] == "matched"
        assert row["tenant_id"] == tenant_record.id
        assert row["lease_id"] == active_lease.id

    def test_reference_duplicate_still_flagged(self, db: Session, org, tenant_record, active_lease, landlord_user):
        ref = "BATCH-DUP-REF"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_user.id,
        )
        db.add(review_item)
        db.flush()

        existing_payment = Payment(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            amount=25000,
            payment_method="mpesa",
            reference=ref,
            payment_date=datetime(2026, 1, 15).date(),
        )
        db.add(existing_payment)
        db.flush()

        csv_content = (
            "Date,Transaction,Currency,Deposit\n"
            "15/01/2026,MPESA TO ACC 0100316372900 BATCH-DUP-REF TIMESTAMP: 254725123456 TO 0100316372900,KES,25000.00\n"
        ).encode("utf-8")
        parsed = payment_batch_service.parse_statement(csv_content)
        preview = payment_batch_service.build_preview(db, org.id, parsed)

        assert preview["total_rows"] == 1
        row = preview["rows"][0]
        assert row["status"] == "duplicate"
        assert row["tenant_id"] == tenant_record.id

    def test_missing_amount_still_parse_error(self, db: Session, org):
        csv_content = (
            "Date,Transaction,Currency,Deposit\n"
            "15/01/2026,MPESA TO ACC 0100316372900 NO-AMT TIMESTAMP: 254725123456 TO 0100316372900,KES,\n"
        ).encode("utf-8")
        parsed = payment_batch_service.parse_statement(csv_content)
        preview = payment_batch_service.build_preview(db, org.id, parsed)

        assert preview["total_rows"] == 1
        row = preview["rows"][0]
        assert row["status"] == "parse_error"

    def test_review_item_different_org_not_matched(self, db: Session, org, tenant_record, active_lease, landlord_user):
        other_org = Organization(id=str(uuid.uuid4()), name="Other Org", owner_id=landlord_user.id)
        db.add(other_org)
        db.flush()

        ref = "BATCH-REF-OTHER-ORG"
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=other_org.id,
            source="whatsapp",
            source_message_id=str(uuid.uuid4()),
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payer_phone="+254725123456",
            payer_phone_hash=None,
            payer_name="Test Tenant",
            raw_transaction="MPESA ...",
            extracted_reference=ref,
            extracted_amount=25000,
            message_timestamp=datetime(2026, 1, 15, 10, 0, 0),
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_user.id,
        )
        db.add(review_item)
        db.flush()

        csv_content = (
            "Date,Transaction,Currency,Deposit\n"
            "15/01/2026,MPESA TO ACC 0100316372900 BATCH-REF-OTHER-ORG TIMESTAMP: 254725123456 TO 0100316372900,KES,25000.00\n"
        ).encode("utf-8")
        parsed = payment_batch_service.parse_statement(csv_content)
        preview = payment_batch_service.build_preview(db, org.id, parsed)

        assert preview["total_rows"] == 1
        row = preview["rows"][0]
        assert row["status"] == "matched"
        assert row["tenant_id"] == tenant_record.id
        assert row["tenant_name"] == "Test Tenant"
        assert row["lease_id"] == active_lease.id
        assert len(row["whatsapp_matches"]) == 0
