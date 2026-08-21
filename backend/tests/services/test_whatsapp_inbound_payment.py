"""Tests for WhatsApp inbound payment-evidence handling.

Covers:
  - Message created
  - Ticket still created
  - PaymentReviewItem created for payment evidence
  - ordinary message does not create payment evidence
  - duplicate webhook does not create duplicate evidence
  - parser failure does not break inbound message handling
  - tenant resolution via phone_hash
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
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.payment_review_item import PaymentReviewItem
from app.services.messaging.inbound_handler import handle_inbound_message
from app.services.messaging import inbound_handler as ih_module
from app.core.encryption import blind_index


# ── Fixtures ────────────────────────────────────────────────────────────────

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
def tenant_user(db: Session, org, landlord_role):
    user = User(id=str(uuid.uuid4()), email="tenant@test.com", full_name="Tenant User", password_hash="test-hash")
    db.add(user)
    db.flush()
    member = OrganizationMember(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=org.id,
        role_id=landlord_role.id,
    )
    db.add(member)
    db.flush()
    return user


@pytest.fixture
def tenant_record(db: Session, org, tenant_user):
    phone = "+254725123456"
    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        full_name="Test Tenant",
        phone=phone,
        alternative_phone=None,
        email=None,
        id_number=None,
        user_id=tenant_user.id,
    )
    db.add(tenant)
    db.flush()
    return tenant


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parsed_message(body="Hello", from_phone="254725123456", provider_message_id=None):
    return {
        "provider_message_id": provider_message_id or f"wamid.{uuid.uuid4().hex}",
        "from_phone": from_phone,
        "sender_name": "Test Sender",
        "message_type": "text",
        "body": body,
        "timestamp": datetime.utcnow(),
    }


# ── Tests ───────────────────────────────────────────────────────────────────

class TestWhatsAppInboundPayment:
    def test_creates_message_and_ticket(self, db: Session, org, tenant_record):
        parsed = _parsed_message(body="Hello, when is maintenance?", from_phone="254725123456")
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert result["message_id"]
        assert result["ticket_id"]
        assert result["tenant_id"] == tenant_record.id
        assert result["duplicate"] is False

        msg = db.query(Message).filter(Message.id == result["message_id"]).first()
        assert msg is not None
        assert msg.direction == "incoming"
        assert msg.channel == "whatsapp"

        ticket = db.query(Ticket).filter(Ticket.id == result["ticket_id"]).first()
        assert ticket is not None
        assert ticket.source == "whatsapp"

    def test_creates_payment_review_item_for_payment_evidence(self, db: Session, org, tenant_record):
        parsed = _parsed_message(
            body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            from_phone="254725123456",
        )
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert result["message_id"]
        assert result["ticket_id"]
        assert result["payment_review_item_id"] is not None

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert review_item is not None
        assert review_item.source == "whatsapp"
        assert review_item.source_message_id == result["message_id"]
        assert review_item.tenant_id == tenant_record.id
        assert review_item.reference == "UB31M5J6YF"
        assert review_item.status == "pending_review"

    def test_ordinary_message_does_not_create_payment_evidence(self, db: Session, org, tenant_record):
        parsed = _parsed_message(body="Hello, when is maintenance?", from_phone="254725123456")
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert result["message_id"]
        assert result["ticket_id"]
        assert result.get("payment_review_item_id") is None

        review_items = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.source_message_id == result["message_id"]
        ).all()
        assert len(review_items) == 0

    def test_duplicate_webhook_does_not_create_duplicate_evidence(self, db: Session, org, tenant_record):
        parsed = _parsed_message(
            body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            from_phone="254725123456",
        )
        result1 = handle_inbound_message(db, org.id, parsed)
        db.commit()

        result2 = handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert result1["message_id"] == result2["message_id"]
        assert result1["ticket_id"] == result2["ticket_id"]
        assert result2.get("payment_review_item_id") is None

        review_items = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.source == "whatsapp",
            PaymentReviewItem.organization_id == org.id,
        ).all()
        assert len(review_items) == 1

    def test_parser_failure_does_not_break_inbound(self, db: Session, org, tenant_record):
        parsed = _parsed_message(body="Some message", from_phone="254725123456")
        with patch.object(ih_module, "parse_whatsapp_payment", side_effect=Exception("parser boom")):
            result = handle_inbound_message(db, org.id, parsed)
            db.commit()

        assert result["message_id"]
        assert result["ticket_id"]
        assert result["duplicate"] is False

    def test_tenant_resolution_via_phone_hash(self, db: Session, org, tenant_record):
        parsed = _parsed_message(body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900", from_phone="254725123456")
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()
        assert result["tenant_id"] == tenant_record.id

    def test_unknown_phone_creates_ticket_without_tenant(self, db: Session, org):
        parsed = _parsed_message(body="Hello", from_phone="254799999999")
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert result["message_id"]
        assert result["ticket_id"]
        assert result["tenant_id"] is None

        ticket = db.query(Ticket).filter(Ticket.id == result["ticket_id"]).first()
        assert ticket.tenant_id is None

    def test_whatsapp_review_item_has_correct_relationships(self, db: Session, org, tenant_record):
        parsed = _parsed_message(
            body="UAVO15EI8G 25479****032 - TIMOTHY **",
            from_phone="254725123456",
        )
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.source_message_id == result["message_id"]
        ).first()
        assert review_item is not None
        assert review_item.source_message is not None
        assert review_item.tenant == tenant_record
