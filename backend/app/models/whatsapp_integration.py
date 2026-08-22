#backend\app\models\whatsapp_integration.py
"""
WhatsAppIntegration — maps a Meta WhatsApp phone number identity to an
organization, scoped by environment.

Architecture
------------

::

    Meta phone_number_id
            ↓
    WhatsAppIntegration   (one row per env + phone_number_id)
            ↓
    organization_id
            ↓
    Tenant → Lease → PaymentReviewItem

This table is the **foundation** for the transition from sandbox
(single hardcoded organization) to production (multi-tenant SaaS where
each organization registers its own Meta phone number).

Sandbox may initially use ``WHATSAPP_DEFAULT_ORG_ID`` as a controlled
fallback when no integration row exists yet.  Production must resolve
the organization from this table — an unknown phone_number_id in
production is rejected, never silently routed to an arbitrary org.

Design rules
------------
* Only ``meta_phone_number_id``, ``meta_business_account_id``,
  ``environment``, and ``is_active`` live here.
* **No raw access tokens or app secrets** are stored in this table.
  Credentials remain in the environment/configuration system.
* The uniqueness constraint
  ``uniq_whatsapp_integration_number_environment``
  on ``(environment, meta_phone_number_id)`` ensures one integration
  per phone number per environment.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class WhatsAppIntegration(Base):
    __tablename__ = "whatsapp_integrations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Meta identity ─────────────────────────────────────────────
    # The phone_number_id that Meta includes in webhook payload metadata.
    # This is the value that uniquely identifies *which* WhatsApp business
    # phone number received the message.
    meta_phone_number_id = Column(String, nullable=False)
    # The Meta Business Account (business account ID) that owns the number.
    # Nullable because some setups only track the phone number.
    meta_business_account_id = Column(String, nullable=True)

    # ── Environment scoping ────────────────────────────────────────
    # "sandbox" or "production" — keeps test and live numbers from colliding.
    environment = Column(String, nullable=False, default="sandbox", index=True)

    # Soft-delete / toggle — deactivate a number without losing history.
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # ── Audit ──────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "environment",
            "meta_phone_number_id",
            name="uniq_whatsapp_integrations_env_phone_number",
        ),
    )

    # ── Relationships ─────────────────────────────────────────────
    organization = relationship("Organization")
