#backend\app\services\messaging\organization_resolver.py
"""
WhatsApp organization resolver.

Resolves an incoming Meta webhook's ``phone_number_id`` to the
``organization_id`` that owns that WhatsApp business number, based on
the configured ``WHATSAPP_ENV``.

Transition design
-----------------

::

    SANDBOX     phone_number_id
              ↘ try WhatsAppIntegration lookup
              ↘ if found → use mapped organization
              ↘ otherwise → WHATSAPP_DEFAULT_ORG_ID  (SANDBOX FALLBACK ONLY)

    PRODUCTION  phone_number_id
              ↘ WhatsAppIntegration lookup
              ↘ found → use mapped organization
              ↘ NOT found → reject (log + return None)

The sandbox fallback (``WHATSAPP_DEFAULT_ORG_ID``) is a controlled escape
hatch so sandbox development can run without pre-populating the DB table.
It is NOT used in production and does NOT establish tenant ownership —
tenant resolution continues via sender-phone → blind-index → tenant, scoped
to the resolved organization.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.whatsapp_integration import WhatsAppIntegration

logger = logging.getLogger(__name__)


def resolve_organization(
    db: Session,
    phone_number_id: Optional[str],
) -> Optional[str]:
    """
    Resolve a Meta ``phone_number_id`` to an ``organization_id``.

    Strategy depends on ``WHATSAPP_ENV``:

    * **sandbox** — look up the ``WhatsAppIntegration`` table for an active
      row matching ``(environment='sandbox', meta_phone_number_id)`` and the
      configured phone number.  If found, return its ``organization_id``.
      If not found, fall back to ``settings.whatsapp.default_org_id``
      (SANDBOX FALLBACK ONLY — logged as such).

    * **production** — look up the same table for an active row matching
      ``(environment='production', meta_phone_number_id)``.  If found, return
      its ``organization_id``.  If not found, log a clear warning and return
      ``None`` (the webhook event is safely ignored).

    Returns
    -------
    str or None
        The resolved ``organization_id``, or ``None`` when production cannot
        resolve the number (or when ``phone_number_id`` is empty).
    """
    if not phone_number_id:
        logger.warning(
            "resolve_organization: no phone_number_id in webhook metadata — "
            "ignoring event"
        )
        return None

    env = settings.whatsapp.environment

    # ── DB lookup: phone_number_id → WhatsAppIntegration → organization_id
    integration = (
        db.query(WhatsAppIntegration)
        .filter(
            WhatsAppIntegration.environment == env,
            WhatsAppIntegration.meta_phone_number_id == phone_number_id,
            WhatsAppIntegration.is_active.is_(True),
        )
        .first()
    )

    if integration:
        logger.info(
            "Resolved WhatsApp phone_number_id '%s' → organization %s "
            "(environment=%s, via WhatsAppIntegration)",
            phone_number_id,
            integration.organization_id,
            env,
        )
        return integration.organization_id

    # ── Fallback ────────────────────────────────────────────────
    if settings.whatsapp.is_sandbox:
        if settings.whatsapp.default_org_id:
            # SANDBOX FALLBACK ONLY — documented as such so nobody mistakes
            # this for production tenant-routing logic.
            logger.info(
                "resolve_organization: SANDBOX FALLBACK — phone_number_id %s "
                "not found in whatsapp_integrations; using WHATSAPP_DEFAULT_ORG_ID",
                phone_number_id,
            )
            return settings.whatsapp.default_org_id

        logger.warning(
            "resolve_organization: sandbox environment has no "
            "WHATSAPP_DEFAULT_ORG_ID fallback and no WhatsAppIntegration "
            "row for phone_number_id %s — ignoring event",
            phone_number_id,
        )
        return None

    # ── Production: unknown number → reject ──────────────────────
    logger.error(
        "resolve_organization: PRODUCTION — unknown phone_number_id %s. "
        "No active WhatsAppIntegration found for environment='production'. "
        "Event ignored — not routing to an arbitrary organization.",
        phone_number_id,
    )
    return None
