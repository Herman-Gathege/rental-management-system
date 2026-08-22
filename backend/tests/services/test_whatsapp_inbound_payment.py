"""Tests for WhatsApp inbound payment-evidence handling.

Covers:
  - Message created
  - Ticket still created
  - PaymentReviewItem created for payment evidence
  - ordinary message does not create payment evidence
  - duplicate webhook does not create duplicate evidence
  - parser failure does not break inbound message handling
  - tenant resolution via phone_hash
  - phone_number_id extracted from Meta payload
  - duplicate webhook continues payment processing (retry)
  - confirmation failure does not delete PaymentReviewItem
  - duplicate webhook does not duplicate ticket
"""
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

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
from app.services.messaging.inbound_handler import (
    handle_inbound_message,
    parse_message_payload,
    _create_payment_review_item,
)
from app.services.messaging import inbound_handler as ih_module
from app.services.messaging import inbound_handler
from app.services.messaging.base_provider import MessagingProviderError
from app.services.messaging.whatsapp_provider import WhatsAppProvider
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

def _parsed_message(body="Hello", from_phone="254725123456", provider_message_id=None, phone_number_id="1100453449823727"):
    return {
        "provider_message_id": provider_message_id or f"wamid.{uuid.uuid4().hex}",
        "from_phone": from_phone,
        "sender_name": "Test Sender",
        "message_type": "text",
        "body": body,
        "timestamp": datetime.utcnow(),
        "phone_number_id": phone_number_id,
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
        assert result2["duplicate"] is True
        assert result2.get("payment_review_item_id") is None

        review_items = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.source == "whatsapp",
            PaymentReviewItem.organization_id == org.id,
        ).all()
        assert len(review_items) == 1

    def test_duplicate_webhook_continues_payment_processing(self, db: Session, org, tenant_record):
        """When a duplicate webhook arrives AND the first attempt did not complete
        payment processing (e.g. review item was never created), the duplicate
        should still create the review item — not skip it entirely."""
        parsed = _parsed_message(
            body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            from_phone="254725123456",
            provider_message_id="wamid.retrymessage123",
        )

        # Simulate: first webhook created message+token but payment processing
        # was interrupted before the review item was committed.  We simulate
        # this by creating the message only (not the review item) before the
        # duplicate webhook arrives.
        from app.models.message import Message as MsgModel
        from app.core.encryption import blind_index as _bl
        msg = MsgModel(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            phone_number="+254725123456",
            direction="incoming",
            message_type="ticket",
            content=parsed["body"],
            status="received",
            channel="whatsapp",
            provider_message_id=parsed["provider_message_id"],
            tenant_id=tenant_record.id,
        )
        db.add(msg)
        db.flush()

        ticket = Ticket(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            tenant_id=tenant_record.id,
            source_phone="+254725123456",
            source_message_id=msg.id,
            title=parsed["body"][:80],
            description=parsed["body"],
            status="open",
            source="whatsapp",
        )
        db.add(ticket)
        msg.ticket_id = ticket.id
        db.commit()

        # Now the "duplicate" webhook arrives — message already exists
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        # The duplicate should still process payment evidence
        assert result["duplicate"] is True
        assert result["payment_review_item_id"] is not None

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert review_item is not None
        assert review_item.reference == "UB31M5J6YF"

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


# ── phone_number_id extraction ────────────────────────────────────────────────

class TestPhoneNumberIdExtraction:
    def test_parse_message_payload_extracts_phone_number_id(self):
        """parse_message_payload should retain phone_number_id from value.metadata."""
        value = {
            "metadata": {
                "phone_number_id": "123456789012345",
                "display_phone_number": "+15551234567",
            },
            "contacts": [],
            "messages": [
                {
                    "from": "254725123456",
                    "id": "wamid.test123",
                    "timestamp": "1716123456",
                    "type": "text",
                    "text": {"body": "Hello"},
                }
            ],
        }
        parsed = parse_message_payload(value)
        assert len(parsed) == 1
        assert parsed[0]["phone_number_id"] == "123456789012345"

    def test_parse_message_payload_phone_number_id_none_when_missing(self):
        """When metadata has no phone_number_id, parsed value should be None."""
        value = {
            "messages": [
                {
                    "from": "254725123456",
                    "id": "wamid.test456",
                    "timestamp": "1716123456",
                    "type": "text",
                    "text": {"body": "Hello"},
                }
            ],
        }
        parsed = parse_message_payload(value)
        assert len(parsed) == 1
        assert parsed[0]["phone_number_id"] is None

    def test_parse_message_payload_extracts_amount_payment_with_phone_number_id(self):
        value = {
            "metadata": {"phone_number_id": "999999999"},
            "messages": [
                {
                    "from": "254725123456",
                    "id": "wamid.pay999",
                    "timestamp": "1716123456",
                    "type": "text",
                    "text": {
                        "body": "MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900"
                    },
                }
            ],
        }
        parsed = parse_message_payload(value)
        assert parsed[0]["phone_number_id"] == "999999999"
        assert parsed[0]["provider_message_id"] == "wamid.pay999"


# ── PaymentReviewItem transaction isolation ───────────────────────────────────

class TestPaymentReviewItemTransactionIsolation:
    def test_confirmation_failure_does_not_delete_payment_review_item(
        self, db: Session, org, tenant_record
    ):
        """A failed confirmation send must NOT roll back the PaymentReviewItem.

        The review item is committed BEFORE the confirmation send, so that
        a provider error leaves the review item intact in the database.
        """
        parsed = _parsed_message(
            body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            from_phone="254725123456",
        )

        # Mock the provider to fail so send_notification catches the
        # MessagingProviderError internally — the outgoing message gets
        # marked "failed" and committed, while the review item (already
        # committed upstream) is untouched.
        with patch.object(
            WhatsAppProvider,
            "send_freeform_text",
            side_effect=MessagingProviderError("Meta API unavailable"),
        ):
            result = handle_inbound_message(db, org.id, parsed)

        # The review item should still exist despite the confirmation failure
        assert result["payment_review_item_id"] is not None

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert review_item is not None
        assert review_item.status == "pending_review"
        assert review_item.source == "whatsapp"
        assert review_item.reference == "UB31M5J6YF"

        db.commit()

    def test_confirmation_failure_with_amount_does_not_delete_review_item(
        self, db: Session, org, tenant_record
    ):
        """Same as above but with a payment message that has both reference
        and amount, so the payment_evidence_received ack is attempted."""
        parsed = _parsed_message(
            body="UAVO15EI8G 25479****032 - TIMOTHY ** 26000",
            from_phone="254725123456",
        )

        with patch.object(
            WhatsAppProvider,
            "send_freeform_text",
            side_effect=MessagingProviderError("Meta API unavailable"),
        ):
            result = handle_inbound_message(db, org.id, parsed)

        assert result["payment_review_item_id"] is not None

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert review_item is not None
        assert review_item.status == "pending_review"
        assert review_item.reference == "UAVO15EI8G"
        assert float(review_item.amount) == 26000.0

        db.commit()

    def test_review_item_committed_before_confirmation(
        self, db: Session, org, tenant_record
    ):
        """The PaymentReviewItem is committed before the confirmation send
        is attempted.  We verify by checking that even when the provider
        fails, the review item is already persisted (committed) and survives
        the confirmation's internal rollback."""
        parsed = _parsed_message(
            body="UAVO15EI8G 25479****032 - TIMOTHY **",
            from_phone="254725123456",
        )

        with patch.object(
            WhatsAppProvider,
            "send_freeform_text",
            side_effect=MessagingProviderError("Meta API unavailable"),
        ):
            result = handle_inbound_message(db, org.id, parsed)

        assert result["payment_review_item_id"] is not None

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert review_item is not None
        assert review_item.status == "pending_review"

        db.commit()

    def test_payment_review_item_idempotent_on_duplicate_message(
        self, db: Session, org, tenant_record
    ):
        """Calling _create_payment_review_item twice for the same message
        should only create one item."""
        parsed = _parsed_message(
            body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            from_phone="254725123456",
        )
        # Persist the message first (simulating prior webhook)
        from app.services.messaging.inbound_handler import _persist_inbound_message, _normalize_phone
        message, is_new = _persist_inbound_message(
            db=db, organization_id=org.id, parsed=parsed,
            tenant_id=tenant_record.id,
        )
        db.commit()

        parser_result = {
            "is_payment_evidence": True,
            "reference": "UB31M5J6YF",
            "amount": None,
            "confidence": "high",
            "evidence": [],
        }

        item1 = _create_payment_review_item(
            db=db, organization_id=org.id, message=message,
            tenant=tenant_record, parsed=parsed, parser_result=parser_result,
        )
        db.commit()

        item2 = _create_payment_review_item(
            db=db, organization_id=org.id, message=message,
            tenant=tenant_record, parsed=parsed, parser_result=parser_result,
        )
        db.commit()

        assert item1 is not None
        assert item2 is None  # duplicate guard → no second item

        # Verify only one exists in DB
        count = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.source_message_id == message.id
        ).count()
        assert count == 1


# ── Tenant and organization isolation ─────────────────────────────────────────

class TestTenantOrganizationIsolation:
    def test_duplicate_webhook_does_not_duplicate_ticket(
        self, db: Session, org, tenant_record
    ):
        """A duplicate webhook must not create a second Ticket row."""
        parsed = _parsed_message(body="Hello, maintenance request", from_phone="254725123456")
        result1 = handle_inbound_message(db, org.id, parsed)
        db.commit()

        result2 = handle_inbound_message(db, org.id, parsed)
        db.commit()

        assert result1["ticket_id"] == result2["ticket_id"]
        assert result2["duplicate"] is True

        tickets = db.query(Ticket).filter(
            Ticket.source_message_id == result1["message_id"]
        ).all()
        assert len(tickets) == 1

    def test_review_item_belongs_to_correct_org(
        self, db: Session, org, tenant_record, landlord_user
    ):
        """PaymentReviewItem is scoped to the organization passed in."""
        org_b = Organization(id=str(uuid.uuid4()), name="Org B", owner_id=landlord_user.id)
        db.add(org_b)
        db.flush()

        parsed = _parsed_message(
            body="MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900",
            from_phone="254725123456",
        )
        result = handle_inbound_message(db, org.id, parsed)
        db.commit()

        review_item = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.id == result["payment_review_item_id"]
        ).first()
        assert review_item.organization_id == org.id
        assert review_item.organization_id != org_b.id
