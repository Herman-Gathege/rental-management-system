#backend\app\models\ticket.py
"""
Ticket model — minimal version for Phase 2 auto-ticketing from inbound WhatsApp.

Phase 2 only needs enough fields to:
  1. Persist an inbound WhatsApp message as a maintenance request
  2. Link the originating message and tenant (when known)
  3. Surface a ticket reference in the auto-confirmation reply
  4. Scope every ticket to an organization (multi-tenant safety)

Phase 3 will expand this model with assignment, SLA, comments, attachments,
status transitions, and the matching API routes + frontend sidebar item.

Conventions matched:
  - String UUID primary key (same as Message, Tenant, etc.)
  - organization_id FK with ondelete CASCADE
  - created_at + updated_at with default=utcnow
"""

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Source / ownership ───
    # tenant_id is nullable: inbound messages from unknown numbers still
    # create a ticket so staff can triage manually instead of losing them.
    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # The phone number the message came from (always populated, even when
    # tenant_id is null). Useful for grouping unknown-sender tickets.
    source_phone = Column(String, nullable=False, index=True)

    # The Message row that triggered this ticket (the first inbound message).
    # Nullable so a ticket created manually in the future isn't blocked.
    source_message_id = Column(
        String,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Content ───
    # A short subject we derive from the message body (first ~80 chars).
    subject = Column(String, nullable=False)

    # Full original message body for context.
    description = Column(Text, nullable=False)

    # ─── Lifecycle ───
    # Phase 2 keeps status as a plain string for simplicity.
    # Phase 3 will swap this for an Enum + status-transition rules.
    # Values: "open", "in_progress", "resolved", "closed"
    status = Column(String, nullable=False, default="open", index=True)

    # How the ticket was created — distinguishes WhatsApp tickets from
    # tickets created manually in the admin UI (coming in Phase 3).
    source = Column(String, nullable=False, default="whatsapp")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ─── Relationships ───
    organization = relationship("Organization")
    tenant = relationship("Tenant")
    source_message = relationship(
        "Message",
        foreign_keys=[source_message_id],
    )
