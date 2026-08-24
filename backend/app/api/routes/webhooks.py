#backend\app\api\routes\webhooks.py
"""
WhatsApp webhook routes.

Two endpoints, both mounted at /webhooks/whatsapp:

  GET  — Meta's verification handshake. Called once when you configure
         the webhook URL in the Meta App dashboard. We echo back the
         `hub.challenge` value if the verify token matches.

  POST — Live webhook delivery. Meta sends every inbound message and
         every status update here. We:
            1. Verify the X-Hub-Signature-256 HMAC header
            2. Parse the event envelope
            3. Resolve the org by phone_number_id → WhatsAppIntegration
               (sandbox falls back to WHATSAPP_DEFAULT_ORG_ID)
            4. Hand each message / status to inbound_handler
            5. Always return 200 OK (per Meta best-practice; non-2xx
               triggers exponential-backoff retries that compound any
               temporary issue we're having)

Organization resolution is environment-aware:
  • sandbox   → WhatsAppIntegration lookup, then WHATSAPP_DEFAULT_ORG_ID
  • production → WhatsAppIntegration lookup only (unknown numbers rejected)

Logging is verbose by design — Phase 2 is the most opaque part of the
WhatsApp integration to debug from the outside, so we want a clear
trail in the logs of every event we receive and how we processed it.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.deps import get_db
from app.services.messaging import inbound_handler
from app.services.messaging.whatsapp_provider import WhatsAppProvider
from app.services.messaging.organization_resolver import resolve_organization

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ─────────────────────────────────────────────────────────────────────────
# GET /webhooks/whatsapp — verification handshake
# ─────────────────────────────────────────────────────────────────────────

@router.get("/whatsapp", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
) -> str:
    """
    Meta calls this once when you save the webhook URL.

    Spec: https://developers.facebook.com/docs/graph-api/webhooks/getting-started

    If hub.mode == "subscribe" and hub.verify_token matches the value
    we configured in .env (WHATSAPP_WEBHOOK_VERIFY_TOKEN), we MUST
    respond with the raw hub.challenge value as plain text. Anything
    else (or a 403) tells Meta to reject the webhook configuration.
    """
    expected_token = settings.whatsapp.webhook_verify_token

    if hub_mode != "subscribe":
        logger.warning("Webhook verify rejected: unexpected mode '%s'", hub_mode)
        raise HTTPException(status_code=403, detail="Invalid mode")

    if not expected_token or hub_verify_token != expected_token:
        logger.warning("Webhook verify rejected: token mismatch")
        raise HTTPException(status_code=403, detail="Invalid verify token")

    logger.info("Webhook verification successful")
    return hub_challenge


# ─────────────────────────────────────────────────────────────────────────
# POST /webhooks/whatsapp — live events
# ─────────────────────────────────────────────────────────────────────────

@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Receive a live webhook event from Meta.

    We read the raw body BEFORE parsing JSON because the HMAC signature
    is computed over the exact bytes Meta sent. FastAPI's parsed `body`
    parameter would re-serialize and break the signature check.
    """
    raw_body = await request.body()

    # ── 1) Signature verification ────────────────────────────────────────
    # In dev (no WHATSAPP_APP_SECRET configured) we skip verification with
    # a loud warning — so local-only testing without an app secret still
    # works, but production deployments will scream in the logs if mis-set.
    if settings.whatsapp.app_secret:
        if not x_hub_signature_256:
            logger.warning("Webhook POST rejected: missing X-Hub-Signature-256 header")
            raise HTTPException(status_code=401, detail="Missing signature")

        provider = WhatsAppProvider()
        if not provider.validate_webhook_signature(raw_body, x_hub_signature_256):
            logger.warning("Webhook POST rejected: invalid signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        logger.warning(
            "WHATSAPP_APP_SECRET is not set - skipping signature verification. "
            "DO NOT run like this in production."
        )

    # ── 2) Parse JSON ────────────────────────────────────────────────────
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        logger.error("Webhook POST: invalid JSON: %s", exc)
        # Still return 200 — Meta will not benefit from a retry of malformed JSON
        return {"status": "ignored", "reason": "invalid_json"}

    logger.debug("Webhook payload: %s", json.dumps(payload)[:1000])

    if payload.get("object") != "whatsapp_business_account":
        logger.info("Ignoring non-WhatsApp webhook object: %s", payload.get("object"))
        return {"status": "ignored", "reason": "wrong_object"}

    # ── 3) Dispatch entries ──────────────────────────────────────────────
    # Envelope shape:
    #   { "object": "whatsapp_business_account",
    #     "entry": [ { "id": "...", "changes": [
    #       { "field": "messages",
    #         "value": { "messaging_product": "whatsapp",
    #                    "metadata": {"phone_number_id": "..."},
    #                    "contacts": [...],
    #                    "messages": [...],     # inbound
    #                    "statuses":  [...] } } ] } ] }
    #
    # Organization resolution is per-value-block because each value block
    # carries its own metadata.phone_number_id.  In practice all value blocks
    # in a single webhook share the same business account, but resolving per
    # block is correct and future-proof.
    processed = {"messages": 0, "statuses": 0, "errors": 0}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue

            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id")

            # ── 3a) Resolve organization from phone_number_id ─────────────
            # Sandbox: WhatsAppIntegration lookup → WHATSAPP_DEFAULT_ORG_ID fallback
            # Production: WhatsAppIntegration lookup only (unknown → reject)
            organization_id = resolve_organization(db, phone_number_id)

            if not organization_id:
                # In production this means the phone_number_id is not registered
                # in the whatsapp_integrations table.  We still process status
                # updates (they're keyed by provider_message_id, org-agnostic)
                # but skip inbound messages since we can't scope them to an org.
                if settings.whatsapp.is_production:
                    logger.warning(
                        "Production webhook: no organization resolved for "
                        "phone_number_id %s — skipping inbound messages, "
                        "still processing status updates",
                        phone_number_id,
                    )
                # Process statuses regardless (they don't need org scoping)
                for parsed_status in inbound_handler.parse_status_payload(value):
                    try:
                        inbound_handler.handle_status_update(db, parsed_status)
                        processed["statuses"] += 1
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "Failed to process status update for message %s",
                            parsed_status.get("provider_message_id"),
                        )
                        db.rollback()
                        processed["errors"] += 1
                continue

            # ── 3b) Inbound messages ────────────────────────────────────
            for parsed in inbound_handler.parse_message_payload(value):
                try:
                    inbound_handler.handle_inbound_message(
                        db=db,
                        organization_id=organization_id,
                        parsed=parsed,
                    )
                    processed["messages"] += 1
                except Exception:  # noqa: BLE001
                    # One bad message must not poison the rest of the batch
                    logger.exception(
                        "Failed to process inbound message %s",
                        parsed.get("provider_message_id"),
                    )
                    db.rollback()
                    processed["errors"] += 1

            # ── 3c) Delivery status updates ──────────────────────────────
            for parsed in inbound_handler.parse_status_payload(value):
                try:
                    inbound_handler.handle_status_update(db, parsed)
                    processed["statuses"] += 1
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Failed to process status update for message %s",
                        parsed.get("provider_message_id"),
                    )
                    db.rollback()
                    processed["errors"] += 1

    # Always 200 — see module docstring
    return {"status": "ok", "processed": processed}
