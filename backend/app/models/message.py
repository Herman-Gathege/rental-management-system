#backend\app\models\message.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Message(Base):
    """
    Communication log — all inbound and outbound messages flow through this table.

    This is the heart of the messaging system and serves multiple purposes:
      - conversation history per recipient
      - delivery tracking (status updates from the provider)
      - audit trail for compliance
      - source of truth for ticket creation from inbound messages

    The table is provider-agnostic: WhatsApp today, easily extended to
    SMS, email, or other channels later.
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # ─── Recipient / Sender ───
    # Phone number in E.164 format (e.g. +254712345678)
    phone_number = Column(String, nullable=False, index=True)

    # outgoing — system → user
    # incoming — user → system (from webhook)
    direction = Column(String, nullable=False)

    # ─── Content ───
    # notification — automated system message (rent due, payment receipt, etc.)
    # invite — organization invitation
    # ticket — message that created a maintenance ticket
    # reply — free-form reply within the 24h window
    # manual — manually sent by a staff user
    message_type = Column(String, nullable=False, default="notification")

    # The rendered message body (after template variables are filled in)
    content = Column(Text, nullable=False)

    # If this message was sent using a Meta-approved template, store the name
    template_name = Column(String, nullable=True)

    # ─── Status tracking ───
    # queued — created but not yet sent
    # sent — provider accepted it
    # delivered — provider confirms delivery (from status webhook)
    # read — recipient has read it (from status webhook)
    # failed — provider rejected or delivery failed
    status = Column(String, nullable=False, default="queued")

    # Provider's own ID for this message (used to correlate status webhooks)
    provider_message_id = Column(String, nullable=True, index=True)

    # If provider returned an error, capture it
    error_message = Column(Text, nullable=True)

    # ─── Metadata ───
    # Which channel this went through — for now always "whatsapp"
    channel = Column(String, nullable=False, default="whatsapp")

    # Optional FK to the user who triggered the send (for audit)
    triggered_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Optional FK to the tenant the message is about (for filtering history)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    triggered_by = relationship("User")
    tenant = relationship("Tenant")
