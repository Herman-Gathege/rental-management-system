"""Tests for payment reconciliation financial integrity.

Verifies:
  - WhatsApp processing does NOT increase Payment count
  - apply_review_item() creates Payment exactly once
  - Duplicate reference protection works
"""
import uuid
from datetime import datetime
from unittest.mock import patch

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
from app.models.message import Message
from app.models.ticket import Ticket
from app.services.messaging.inbound_handler import handle_inbound_message
from app.services.payment_reconciliation_service import apply_review_item, save_review_items


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


class TestFinancialIntegrity:
    def test_whatsapp_does_not_create_payment(self, db: Session, org, tenant_record):
        initial_count = db.query(Payment).count()
        parsed = {
            "provider_message_id": f"wamid.{uuid.uuid4().hex}",
            "from_phone": "254725123456",
            "sender_name": "Test",
            "message_type": "text",
            "body": "MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            "timestamp": datetime.utcnow(),
        }
        handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert db.query(Payment).count() == initial_count

    def test_apply_review_item_creates_exactly_one_payment(self, db: Session, org, tenant_record, active_lease, landlord_membership):
        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="csv",
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference="TEST-REF-001",
            payer_phone="+254725123456",
            payer_name="Test Tenant",
            raw_transaction="test",
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            status="pending_review",
            flag_reason="manual_flag",
            created_by_user_id=landlord_membership.user_id,
        )
        db.add(review_item)
        db.flush()

        initial_count = db.query(Payment).count()
        apply_review_item(
            db=db,
            organization_id=org.id,
            user_id=landlord_membership.user_id,
            item_id=review_item.id,
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference="TEST-REF-001",
            payment_method="mpesa",
            payment_type="rent",
        )
        db.commit()

        assert db.query(Payment).count() == initial_count + 1

        payment = db.query(Payment).filter(Payment.reference == "TEST-REF-001").first()
        assert payment is not None
        assert payment.tenant_id == tenant_record.id
        assert payment.amount == 25000

    def test_duplicate_reference_prevents_double_payment(self, db: Session, org, tenant_record, active_lease, landlord_membership):
        ref = "DUPLICATE-REF-001"
        review_items = []
        for _ in range(2):
            review_item = PaymentReviewItem(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                source="csv",
                amount=25000,
                payment_date=datetime(2026, 1, 15).date(),
                reference=ref,
                payer_phone="+254725123456",
                payer_name="Test Tenant",
                raw_transaction="test",
                tenant_id=tenant_record.id,
                lease_id=active_lease.id,
                status="pending_review",
                flag_reason="manual_flag",
                created_by_user_id=landlord_membership.user_id,
            )
            db.add(review_item)
            db.flush()
            review_items.append(review_item)

        # Apply the first review item — should succeed.
        apply_review_item(
            db=db,
            organization_id=org.id,
            user_id=landlord_membership.user_id,
            item_id=review_items[0].id,
            tenant_id=tenant_record.id,
            lease_id=active_lease.id,
            amount=25000,
            payment_date=datetime(2026, 1, 15).date(),
            reference=ref,
            payment_method="mpesa",
            payment_type="rent",
        )
        db.commit()

        # Applying the second review item with the same reference must fail.
        with pytest.raises(Exception):
            apply_review_item(
                db=db,
                organization_id=org.id,
                user_id=landlord_membership.user_id,
                item_id=review_items[1].id,
                tenant_id=tenant_record.id,
                lease_id=active_lease.id,
                amount=25000,
                payment_date=datetime(2026, 1, 15).date(),
                reference=ref,
                payment_method="mpesa",
                payment_type="rent",
            )
        db.commit()

        payment_count = db.query(Payment).filter(Payment.reference == ref).count()
        assert payment_count == 1

    def test_save_review_items_skips_duplicate_refs(self, db: Session, org, landlord_membership):
        ref = "SAVE-DUP-REF"
        item1 = {
            "amount": 25000,
            "payment_date": datetime(2026, 1, 15).date(),
            "reference": ref,
            "payer_phone": "+254725123456",
            "payer_name": "Test",
            "raw_transaction": "test",
            "tenant_id": None,
            "lease_id": None,
            "flag_reason": "manual_flag",
        }
        saved1, skipped1 = save_review_items(db, org.id, landlord_membership.user_id, [item1])
        assert len(saved1) == 1
        assert len(skipped1) == 0

        saved2, skipped2 = save_review_items(db, org.id, landlord_membership.user_id, [item1])
        assert len(saved2) == 0
        assert len(skipped2) == 1
        assert skipped2[0]["reason"] == "already in review queue"
