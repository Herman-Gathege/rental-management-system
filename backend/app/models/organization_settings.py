# backend/app/models/organization_settings.py
"""
Per-organization configuration for billing automation and communication.

One row per organization, created lazily with platform defaults the first time
an org opens its settings (see organization_settings_service). Defaults are
deliberately the behaviour the system already had before this table existed:

  * invoices generated on the 1st of the month
  * pending-payment reminders on the 10th
  * WhatsApp enabled, email disabled (WhatsApp stays the primary channel)

Keeping the defaults identical means introducing this table changes nothing
for an organisation until an admin actually edits something.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


# ─── Communication channel modes ───
# Stored explicitly rather than derived so the settings UI can round-trip the
# admin's intent unambiguously.
CHANNEL_WHATSAPP_ONLY = "whatsapp_only"
CHANNEL_EMAIL_ONLY = "email_only"
CHANNEL_FALLBACK = "fallback"          # WhatsApp first, email if it fails
CHANNEL_DUAL = "dual"                  # send through both
VALID_CHANNEL_MODES = (
    CHANNEL_WHATSAPP_ONLY,
    CHANNEL_EMAIL_ONLY,
    CHANNEL_FALLBACK,
    CHANNEL_DUAL,
)


class OrganizationSettings(Base):
    __tablename__ = "organization_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ─── Billing automation ───
    # Day-of-month the monthly invoice run fires (1-28 — 29-31 would silently
    # skip months that are shorter, so the API rejects them).
    invoice_generation_day = Column(Integer, nullable=False, default=1)
    invoice_automation_enabled = Column(Boolean, nullable=False, default=True)
    # Day-of-month the pending-payment reminder run fires.
    reminder_day = Column(Integer, nullable=False, default=10)
    reminder_automation_enabled = Column(Boolean, nullable=False, default=True)
    # IANA timezone name used to decide "what day is it" for this org.
    timezone = Column(String, nullable=False, default="Africa/Nairobi")

    # ─── Communication channels ───
    channel_mode = Column(String, nullable=False, default=CHANNEL_WHATSAPP_ONLY)
    whatsapp_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=False)
    # Send payment receipts (and other payment-type notifications) over email.
    email_payment_receipts = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization")
