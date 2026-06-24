#backend\app\models\ticket.py
"""
Ticket model — the unified maintenance / support ticket.

History: a minimal version was introduced for WhatsApp Phase 2 auto-ticketing
(inbound message -> ticket). Sprint 6 evolves that SAME table into the full
support hub: property/unit scope, an assignee, priority, category, the full
lifecycle (open -> assigned -> in_progress -> waiting -> resolved -> closed),
plus conversation / attachment / assignment-history child tables.

WhatsApp tickets keep working unchanged: they arrive with source="whatsapp",
tenant_id (best-effort), source_phone, source_message_id, and now title (was
"subject"). property_id / category / created_by are nullable so a
machine-created ticket isn't blocked — staff fill those in during triage.
User-created tickets (portal/manager/landlord/finance) always set created_by
and category at the API layer.

Conventions matched:
  - String UUID primary key
  - organization_id FK, ondelete CASCADE
  - created_at + updated_at default=utcnow
  - multiple user FKs disambiguated with foreign_keys=[...]
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

    # ─── Scope ───
    # property_id nullable: WhatsApp tickets have no property until triage.
    property_id = Column(
        String,
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    unit_id = Column(
        String, ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    # tenant_id nullable: inbound messages from unknown numbers still create a
    # ticket so staff can triage instead of losing it.
    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ─── People ───
    # created_by nullable: system / WhatsApp tickets have no authoring user
    # (source tells you it came from WhatsApp). User-created tickets always
    # set this at the API layer.
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    assigned_to = Column(
        String, ForeignKey("users.id"), nullable=True, index=True
    )

    # ─── WhatsApp intake fields (kept from Phase 2) ───
    # The phone the message came from (always set for WhatsApp tickets, even
    # when tenant_id is null). Nullable so user-created tickets need not set it.
    source_phone = Column(String, nullable=True, index=True)
    # The Message row that triggered this ticket (first inbound message).
    source_message_id = Column(
        String, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )

    # ─── Content ───
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # low | medium | high | critical
    priority = Column(String, nullable=False, default="medium")
    # maintenance | repairs | electricity | water | security | cleaning |
    # noise | lease_question | billing_question | complaint | suggestion | other
    # Nullable: WhatsApp tickets are uncategorized until triage.
    category = Column(String, nullable=True)
    # open -> assigned -> in_progress -> waiting -> resolved -> closed
    status = Column(String, nullable=False, default="open", index=True)
    # tenant_portal | manager | finance | landlord | system | whatsapp
    source = Column(String, nullable=False, default="whatsapp")

    # ─── Lifecycle timestamps ───
    opened_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ─── Relationships ───
    organization = relationship("Organization")
    tenant = relationship("Tenant")
    source_message = relationship("Message", foreign_keys=[source_message_id])

    # Two FKs point at users — disambiguate. One-directional (no back_populates
    # on User) so the User model is untouched.
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])

    messages = relationship(
        "TicketMessage", back_populates="ticket", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "TicketAttachment", back_populates="ticket", cascade="all, delete-orphan"
    )
    assignments = relationship(
        "TicketAssignment", back_populates="ticket", cascade="all, delete-orphan"
    )
