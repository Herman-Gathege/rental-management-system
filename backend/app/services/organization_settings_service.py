# backend/app/services/organization_settings_service.py
"""
Organization settings: defaults, read/write and channel resolution.

This is the single place that answers "what is this organisation's
configuration?" - routes, the automation jobs and the messaging pipeline all
go through it, so the defaults only exist in one place.

Two access patterns, deliberately:

  ``get_settings(db, org_id)``          creates the row if missing (used by the
                                        settings API, where a write is expected)
  ``get_settings_or_none(db, org_id)``  never writes (used on notification
                                        paths, which must not create rows as a
                                        side effect of sending a message)
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models.organization_settings import (
    CHANNEL_DUAL,
    CHANNEL_EMAIL_ONLY,
    CHANNEL_FALLBACK,
    CHANNEL_WHATSAPP_ONLY,
    VALID_CHANNEL_MODES,
    OrganizationSettings,
)

logger = logging.getLogger(__name__)


DEFAULTS = {
    "invoice_generation_day": 1,
    "invoice_automation_enabled": True,
    "reminder_day": 10,
    "reminder_automation_enabled": True,
    "timezone": "Africa/Nairobi",
    "channel_mode": CHANNEL_WHATSAPP_ONLY,
    "whatsapp_enabled": True,
    "email_enabled": False,
    "email_payment_receipts": True,
}


def get_settings_or_none(
    db: Session, organization_id: str
) -> Optional[OrganizationSettings]:
    """Return the org's settings row, or None. Never writes."""
    if not organization_id:
        return None
    return (
        db.query(OrganizationSettings)
        .filter(OrganizationSettings.organization_id == organization_id)
        .first()
    )


def get_settings(db: Session, organization_id: str) -> OrganizationSettings:
    """Return the org's settings row, creating it with defaults when absent.

    Caller is responsible for committing.
    """
    row = get_settings_or_none(db, organization_id)
    if row:
        return row
    row = OrganizationSettings(organization_id=organization_id, **DEFAULTS)
    db.add(row)
    db.flush()
    return row


def setting_value(row: Optional[OrganizationSettings], field: str):
    """Read a field off the settings row, falling back to the platform default."""
    if row is not None:
        value = getattr(row, field, None)
        if value is not None:
            return value
    return DEFAULTS[field]


def channel_mode(row: Optional[OrganizationSettings]) -> str:
    """Resolved channel mode, guaranteed to be a known value."""
    mode = setting_value(row, "channel_mode")
    return mode if mode in VALID_CHANNEL_MODES else CHANNEL_WHATSAPP_ONLY


def channel_status(row: Optional[OrganizationSettings]) -> dict:
    """Describe each channel as enabled / disabled / not_configured / invalid.

    Never exposes a credential: only booleans, host and from-address.
    """
    wa_cfg = app_settings.whatsapp
    email_cfg = app_settings.email

    wa_errors = wa_cfg.validate()
    email_errors = email_cfg.validate()

    whatsapp_enabled = bool(setting_value(row, "whatsapp_enabled"))
    email_enabled = bool(setting_value(row, "email_enabled"))

    def _state(enabled: bool, configured: bool, errors: list[str]) -> str:
        if not enabled:
            return "disabled"
        if not configured:
            return "not_configured"
        # A channel that is switched on and has *some* configuration but fails
        # validation is the case an admin actually needs to be warned about.
        if errors:
            return "invalid"
        return "enabled"

    return {
        "whatsapp": {
            "state": _state(
                whatsapp_enabled,
                not wa_errors,
                wa_errors,
            ),
            "enabled": whatsapp_enabled,
            "configured": not wa_errors,
            "environment": wa_cfg.environment,
            "errors": wa_errors,
        },
        "email": {
            "state": _state(email_enabled, email_cfg.is_configured, email_errors),
            "enabled": email_enabled,
            "errors": email_errors,
            **email_cfg.describe(),
        },
        "channel_mode": channel_mode(row),
    }


def resolve_channels(
    row: Optional[OrganizationSettings],
    *,
    has_phone: bool,
    has_email: bool,
) -> list[str]:
    """Return the channels to attempt, in order, for one message.

    WhatsApp is first whenever it is part of the plan - SMTP must never
    displace the existing WhatsApp behaviour.

    * whatsapp_only -> ["whatsapp"]; email is used only when WhatsApp cannot
      reach this recipient and email can
    * email_only    -> ["email"]
    * fallback      -> ["whatsapp", "email"] - email is used when WhatsApp fails
    * dual          -> ["whatsapp", "email"] - both are sent

    A channel that is switched off, unconfigured or has no destination for
    this recipient is simply unavailable rather than an error.
    """
    mode = channel_mode(row)

    whatsapp_enabled = bool(setting_value(row, "whatsapp_enabled"))
    email_enabled = bool(setting_value(row, "email_enabled"))

    wa_available = (
        whatsapp_enabled and has_phone and not app_settings.whatsapp.validate()
    )
    email_available = (
        email_enabled and has_email and app_settings.email.is_usable
    )

    if mode == CHANNEL_EMAIL_ONLY:
        return ["email"] if email_available else []
    if mode == CHANNEL_WHATSAPP_ONLY:
        if wa_available:
            return ["whatsapp"]
        return ["email"] if email_available else []
    if mode == CHANNEL_DUAL:
        return [
            name
            for name, ok in (("whatsapp", wa_available), ("email", email_available))
            if ok
        ]
    if mode == CHANNEL_FALLBACK:
        if wa_available:
            return ["whatsapp", "email"] if email_available else ["whatsapp"]
        return ["email"] if email_available else []
    return []
