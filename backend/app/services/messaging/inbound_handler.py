#backend\app\services\messaging\inbound_handler.py
"""
Inbound WhatsApp message handler.

This module owns the business logic that runs whenever Meta POSTs us a
webhook event. The HTTP route in `app/api/routes/webhooks.py` is a thin
shell — all the real work happens here so it can be unit-tested without
spinning up FastAPI.

Pipeline for a single inbound message:

    payload  ──► parse_message_payload()
                       │
                       ▼
              find Tenant by phone + organization_id (best-effort)
                       │
                       ▼
              persist Message (direction=incoming, status=received)
                       │
                       ▼
              create Ticket (linked to message + tenant + org)
                       │
                       ▼
              write audit_log entries
                       │
                       ▼
              commit
                       │
                       ▼
              send "ticket_received" confirmation via messaging_service
                       │
                       ▼
              commit confirmation
                       │
                       ▼
              return summary dict for logging

Pipeline for a status update (sent / delivered / read / failed):

    payload  ──► parse_status_payload()
                       │
                       ▼
              find existing Message by provider_message_id
                       │
                       ▼
              update Message.status (with rank guard so out-of-order
              webhooks don't downgrade read → delivered)
                       │
                       ▼
              commit

Both pipelines swallow per-event exceptions so one bad event in a batch
doesn't poison the rest. The webhook endpoint always returns 200 to Meta
(per Meta's docs — non-2xx triggers retries that compound the problem).

Sprint 6 note: the tickets table was evolved (subject -> title, plus
property/assignee/priority/category/lifecycle fields). WhatsApp tickets keep
arriving uncategorized with source="whatsapp"; staff triage them in the hub.
The only change here vs. the Phase 2 version is writing `title` instead of
`subject`.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.tenant import Tenant
from app.models.ticket import Ticket
from app.services.audit_service import log_action
from app.services.messaging import send_notification

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Payload parsing
# ─────────────────────────────────────────────────────────────────────────

def parse_message_payload(value: dict) -> list[dict]:
    """
    Extract inbound messages from a single `value` block in a Meta webhook.

    Meta delivers messages under:
        entry[].changes[].value.messages[]

    Each message looks roughly like:
        {
            "from": "254712345678",
            "id":   "wamid.HBg...",
            "timestamp": "1716123456",
            "type": "text",
            "text": { "body": "hello" }
        }

    Returns a list of normalized dicts. Non-text messages (image, audio,
    interactive, etc.) are still captured with a placeholder body so we
    don't lose the audit trail; richer handling lands in a later phase.
    """
    messages = value.get("messages") or []
    contacts = value.get("contacts") or []

    # Build phone → display-name lookup from the contacts array
    name_by_phone: dict[str, str] = {}
    for c in contacts:
        wa_id = c.get("wa_id")
        profile = c.get("profile") or {}
        if wa_id and profile.get("name"):
            name_by_phone[wa_id] = profile["name"]

    parsed: list[dict] = []
    for m in messages:
        msg_type = m.get("type", "unknown")
        from_phone = m.get("from", "")

        # Extract body based on message type
        if msg_type == "text":
            body = (m.get("text") or {}).get("body", "")
        elif msg_type in {"image", "audio", "video", "document", "sticker"}:
            media = m.get(msg_type) or {}
            caption = media.get("caption", "")
            body = caption or f"[{msg_type} message — media not yet supported]"
        elif msg_type == "interactive":
            interactive = m.get("interactive") or {}
            kind = interactive.get("type", "")
            if kind == "button_reply":
                body = (interactive.get("button_reply") or {}).get("title", "")
            elif kind == "list_reply":
                body = (interactive.get("list_reply") or {}).get("title", "")
            else:
                body = f"[interactive: {kind}]"
        else:
            body = f"[{msg_type} message]"

        # Meta sends timestamp as a unix-seconds string
        try:
            ts = datetime.utcfromtimestamp(int(m.get("timestamp", "0")))
        except (TypeError, ValueError):
            ts = datetime.utcnow()

        parsed.append({
            "provider_message_id": m.get("id"),
            "from_phone": from_phone,
            "sender_name": name_by_phone.get(from_phone),
            "message_type": msg_type,
            "body": body,
            "timestamp": ts,
        })

    return parsed


def parse_status_payload(value: dict) -> list[dict]:
    """
    Extract delivery status updates from a `value` block.

    Meta delivers statuses under:
        entry[].changes[].value.statuses[]

    Each status looks like:
        {
            "id": "wamid.HBg...",            # the original outbound message id
            "status": "delivered",            # sent | delivered | read | failed
            "timestamp": "1716123456",
            "recipient_id": "254712345678",
            "errors": [...]                   # only on failed
        }
    """
    statuses = value.get("statuses") or []
    parsed: list[dict] = []
    for s in statuses:
        try:
            ts = datetime.utcfromtimestamp(int(s.get("timestamp", "0")))
        except (TypeError, ValueError):
            ts = datetime.utcnow()

        errors = s.get("errors") or []
        error_msg = None
        if errors:
            first = errors[0] or {}
            error_msg = first.get("message") or first.get("title") or str(first)

        parsed.append({
            "provider_message_id": s.get("id"),
            "status": s.get("status"),
            "timestamp": ts,
            "recipient": s.get("recipient_id"),
            "error": error_msg,
        })

    return parsed


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _normalize_phone(phone: str) -> str:
    """
    Normalize a phone number to E.164 format with leading '+'.

    Meta strips the '+' from inbound payloads (you get "254712345678",
    not "+254712345678"). Our tenants are stored with '+' in Phase 1.
    Re-attach it so the equality match works.
    """
    if not phone:
        return phone
    phone = phone.strip()
    if phone.startswith("+"):
        return phone
    # Meta wa_id is always digits-only in E.164 form (just missing the +)
    return f"+{phone}"


def _find_tenant_by_phone(
    db: Session,
    organization_id: str,
    phone: str,
) -> Optional[Tenant]:
    """
    Best-effort tenant lookup by phone number, scoped to the organization.

    Returns None if no match — the ticket is still created with
    tenant_id=null so staff can triage.

    We try the normalized form first (matches what tenant CRUD stores),
    then fall back to the raw inbound phone in case tenants were
    created with the Meta-style no-'+' format.
    """
    normalized = _normalize_phone(phone)

    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.organization_id == organization_id,
            Tenant.phone == normalized,
        )
        .first()
    )
    if tenant:
        return tenant

    # Fallback: maybe the tenant was stored without the leading '+'
    if normalized != phone:
        tenant = (
            db.query(Tenant)
            .filter(
                Tenant.organization_id == organization_id,
                Tenant.phone == phone,
            )
            .first()
        )

    return tenant


def _persist_inbound_message(
    db: Session,
    organization_id: str,
    parsed: dict,
    tenant_id: Optional[str],
) -> tuple[Message, bool]:
    """
    Save an inbound message to the messages table.

    Idempotent on provider_message_id: if Meta retries the webhook (which
    happens often), we don't create duplicates.

    Returns (message, is_new).
    """
    existing = (
        db.query(Message)
        .filter(Message.provider_message_id == parsed["provider_message_id"])
        .first()
    )
    if existing:
        return existing, False

    msg = Message(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        phone_number=_normalize_phone(parsed["from_phone"]),
        direction="incoming",
        message_type="ticket",  # Phase 2: all inbound messages create tickets
        content=parsed["body"],
        status="received",
        channel="whatsapp",
        provider_message_id=parsed["provider_message_id"],
        tenant_id=tenant_id,
    )
    db.add(msg)
    db.flush()  # populate msg.id without committing the whole batch yet
    return msg, True


def _create_ticket_from_message(
    db: Session,
    organization_id: str,
    message: Message,
    tenant_id: Optional[str],
    body: str,
    source_phone: str,
) -> Ticket:
    """
    Create a ticket from an inbound message body.

    Title = first 80 chars of body, single-line, trimmed.

    Sprint 6: the column is now `title` (was `subject`). property_id /
    category / created_by are left null — a WhatsApp ticket is uncategorized
    and unassigned to a property until staff triage it in the hub. source
    stays "whatsapp" so it's distinguishable from user-created tickets.
    """
    title = (body or "").replace("\n", " ").strip()
    if not title:
        title = "(empty message)"
    if len(title) > 80:
        title = title[:77] + "..."

    ticket = Ticket(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        tenant_id=tenant_id,
        source_phone=source_phone,
        source_message_id=message.id,
        title=title,
        description=body or "",
        status="open",
        source="whatsapp",
    )
    db.add(ticket)
    db.flush()

    # Link the message back to the ticket it created (set on the same row,
    # no second INSERT — just an UPDATE column in the same transaction).
    message.ticket_id = ticket.id
    return ticket


def _send_ticket_confirmation(
    db: Session,
    organization_id: str,
    phone: str,
    ticket_id: str,
    tenant_id: Optional[str],
) -> None:
    """
    Fire the 'ticket_received' template back to the sender.

    Failures are logged but never re-raised: the ticket has already been
    created and committed, so we shouldn't fail the webhook over a
    confirmation send. The send itself persists a Message row via
    messaging_service, so the failure is also captured there.
    """
    try:
        send_notification(
            db=db,
            organization_id=organization_id,
            phone_number=_normalize_phone(phone),
            template_name="ticket_received",
            variables={"ticket_id": str(ticket_id)[:8]},  # short ID for UX
            tenant_id=tenant_id,
            message_type="notification",
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 — we genuinely want to swallow
        logger.exception(
            "Failed to send ticket_received confirmation for ticket %s: %s",
            ticket_id, exc,
        )
        db.rollback()


# ─────────────────────────────────────────────────────────────────────────
# Public entrypoints
# ─────────────────────────────────────────────────────────────────────────

def handle_inbound_message(
    db: Session,
    organization_id: str,
    parsed: dict,
) -> dict[str, Any]:
    """
    Full pipeline for a single inbound message.

    Returns a dict suitable for logging:
        {
            "message_id": str,
            "ticket_id": str | None,
            "tenant_id": str | None,
            "duplicate": bool,
        }
    """
    # 1) Find tenant first (informs whether the inbound message row
    #    can be linked to a tenant from the start)
    tenant = _find_tenant_by_phone(db, organization_id, parsed["from_phone"])
    tenant_id = tenant.id if tenant else None

    # 2) Persist message (idempotent — returns existing row on duplicate webhook)
    message, is_new = _persist_inbound_message(
        db=db,
        organization_id=organization_id,
        parsed=parsed,
        tenant_id=tenant_id,
    )

    if not is_new:
        logger.info(
            "Duplicate inbound webhook for message %s — skipping ticket creation",
            parsed["provider_message_id"],
        )
        return {
            "message_id": message.id,
            "ticket_id": message.ticket_id,
            "tenant_id": message.tenant_id,
            "duplicate": True,
        }

    # 3) Create ticket
    ticket = _create_ticket_from_message(
        db=db,
        organization_id=organization_id,
        message=message,
        tenant_id=tenant_id,
        body=parsed["body"],
        source_phone=_normalize_phone(parsed["from_phone"]),
    )

    # 4) Audit log entries — one for message received, one for ticket created.
    #    user_id=None because this is a system-triggered event (Meta webhook,
    #    not a logged-in user). Your audit_log model already allows nullable
    #    user_id.
    log_action(
        db=db,
        organization_id=organization_id,
        user_id=None,
        action="receive",
        entity_type="message",
        entity_id=message.id,
        description=(
            f"Inbound WhatsApp message from {parsed['from_phone']}"
            + (f" (tenant: {tenant.full_name})" if tenant else " (unknown sender)")
        ),
    )
    log_action(
        db=db,
        organization_id=organization_id,
        user_id=None,
        action="create",
        entity_type="ticket",
        entity_id=ticket.id,
        description=f"Ticket auto-created from WhatsApp message: {ticket.title}",
    )

    # 5) Commit everything together so message + ticket + audit are atomic.
    #    The confirmation send below will commit separately so a failed
    #    confirmation doesn't undo the ticket.
    db.commit()

    # 6) Send confirmation (best-effort, logged on failure, own commit)
    _send_ticket_confirmation(
        db=db,
        organization_id=organization_id,
        phone=parsed["from_phone"],
        ticket_id=ticket.id,
        tenant_id=tenant_id,
    )

    logger.info(
        "Inbound WhatsApp processed: message_id=%s ticket_id=%s tenant_id=%s phone=%s",
        message.id, ticket.id, tenant_id, parsed["from_phone"],
    )

    return {
        "message_id": message.id,
        "ticket_id": ticket.id,
        "tenant_id": tenant_id,
        "duplicate": False,
    }


def handle_status_update(db: Session, parsed: dict) -> dict[str, Any]:
    """
    Update a previously-sent Message with a delivery status from Meta.

    Status progression per Meta:  sent → delivered → read
    Failed can happen at any point.

    We only move forward in that progression so out-of-order webhooks
    don't downgrade a "read" message back to "delivered".

    Note: status updates don't need org scoping — they're keyed by
    provider_message_id which is globally unique across all orgs.
    """
    msg = (
        db.query(Message)
        .filter(Message.provider_message_id == parsed["provider_message_id"])
        .first()
    )
    if not msg:
        logger.warning(
            "Status update for unknown message id %s — ignoring",
            parsed["provider_message_id"],
        )
        return {"updated": False, "reason": "unknown_message"}

    # Rank statuses so we never regress
    rank = {
        "queued": 0,
        "sent": 1,
        "delivered": 2,
        "read": 3,
        "failed": 99,  # terminal — wins over everything
    }
    new_status = parsed["status"]
    if new_status not in rank:
        logger.warning("Unknown status '%s' for message %s", new_status, msg.id)
        return {"updated": False, "reason": "unknown_status"}

    current_rank = rank.get(msg.status, -1)
    if rank[new_status] < current_rank and new_status != "failed":
        logger.debug(
            "Skipping out-of-order status %s for message %s (currently %s)",
            new_status, msg.id, msg.status,
        )
        return {"updated": False, "reason": "out_of_order"}

    msg.status = new_status
    if new_status == "failed" and parsed.get("error"):
        msg.error_message = parsed["error"]

    db.commit()
    return {"updated": True, "message_id": msg.id, "status": new_status}
