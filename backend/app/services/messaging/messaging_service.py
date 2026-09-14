#backend\app\services\messaging\messaging_service.py
"""
Messaging service.

The ONE place the rest of the codebase calls when it wants to send a message.
Handles:
  - Choosing the right provider (currently always WhatsApp)
  - Rendering templates (free-form OR Meta-template depending on env flag)
  - Persisting the message to the database
  - Catching and logging provider errors

Example usage from any route:

    from app.services.messaging import send_notification

    send_notification(
        db=db,
        organization_id=org.id,
        phone_number=tenant.phone,
        template_name="payment_receipt",
        variables={
            "tenant_name": tenant.full_name,
            "amount": "15,000",
            "date": "2026-05-19",
        },
        triggered_by_user_id=current_user.id,
        tenant_id=tenant.id,
    )
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.message import Message
from app.services.messaging.whatsapp_provider import WhatsAppProvider
from app.services.messaging.base_provider import MessagingProviderError
from app.services.messaging import templates
from app.services.email_service import send_email_message
from app.services.organization_settings_service import (
    get_settings_or_none,
    resolve_channels,
    channel_mode,
)


# Channels this pipeline knows how to deliver on.
CHANNEL_WHATSAPP = "whatsapp"
CHANNEL_EMAIL = "email"


# ─── Helpers ───

def _get_provider():
    """Return the active messaging provider (currently always WhatsApp)."""
    return WhatsAppProvider()


def _use_meta_templates() -> bool:
    """Whether to send via Meta-approved templates or as free-form text."""
    return settings.whatsapp.use_templates


def _html_from_body(subject: str, body: str) -> str:
    """Wrap a rendered template body into a minimal, brand-neutral HTML email.

    Deliberately reuses the same rendered text as the WhatsApp message so a
    tenant sees identical wording on both channels — one template, two
    transports. Only newlines are converted; the body is escaped first so
    tenant-supplied values can never inject markup.
    """
    from html import escape

    paragraphs = [
        f"<p style='margin:0 0 12px'>{escape(line)}</p>"
        for line in str(body).split("\n")
        if line.strip()
    ]
    return (
        "<div style=\"font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,"
        "sans-serif;font-size:15px;line-height:1.5;color:#1f2937\">"
        f"<h2 style='font-size:17px;margin:0 0 16px'>{escape(subject)}</h2>"
        + "".join(paragraphs)
        + "</div>"
    )


def _email_subject(template_name: str) -> str:
    """Human subject line for the email channel, derived from the template."""
    return EMAIL_SUBJECTS.get(
        template_name,
        template_name.replace("_", " ").capitalize(),
    )


# Subject lines for the email channel only. WhatsApp ignores these — the
# approved Meta template text is what recipients see there.
EMAIL_SUBJECTS = {
    "payment_receipt": "Payment receipt",
    "payment_evidence_received": "Payment record received",
    "rent_due_reminder": "Rent due reminder",
    "overdue_notice": "Rent payment outstanding",
    "lease_welcome": "Welcome to your new home",
    "tenant_invite": "Your tenant portal invitation",
    "staff_invite": "You've been invited to AlphaOne",
    "account_locked": "Your account was temporarily locked",
}


def _send_whatsapp(message: Message, template_name: str, variables: dict, body: str) -> None:
    """Attempt WhatsApp delivery and stamp the result onto ``message``."""
    try:
        provider = _get_provider()
        if _use_meta_templates():
            params = templates.get_template_params(template_name, variables)
            lang = templates.get_template_language(template_name)
            result = provider.send_template(
                to_phone=message.phone_number,
                template_name=template_name,
                template_params=params,
                language_code=lang,
            )
        else:
            result = provider.send_freeform_text(
                to_phone=message.phone_number,
                body=body,
            )
        message.status = "sent"
        message.provider_message_id = result.get("provider_message_id")
    except MessagingProviderError as e:
        message.status = "failed"
        message.error_message = str(e)


# ─── Public API ───

def send_notification(
    db: Session,
    organization_id: str,
    phone_number: str,
    template_name: str,
    variables: dict,
    triggered_by_user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    message_type: str = "notification",
    email_address: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    email_subject: Optional[str] = None,
) -> Message:
    """
    Send a notification using a registered template.

    This is the canonical entry point for system-generated messages
    (rent reminders, payment receipts, invites, etc).

    Channel selection
    -----------------
    Delivery goes through the organisation's communication settings
    (organization_settings_service): WhatsApp is attempted first whenever it
    is enabled, and email is added as a fallback and/or a second channel
    depending on the configured mode. Each attempt writes its own Message row,
    so the delivery log shows exactly what was tried on which channel.

    Idempotency
    -----------
    Pass ``idempotency_key`` for anything driven by a webhook, background task
    or scheduled job. When a Message row already exists for that key within
    the organisation, it is returned untouched and nothing is sent — retries
    and repeated event delivery can never double-message a tenant.

    Args:
        db: SQLAlchemy session — caller is responsible for commit
        organization_id: Which org this message belongs to
        phone_number: Recipient phone number (any format — will be normalized)
        template_name: Key from templates.TEMPLATES
        variables: Dict of values to fill into the template
        triggered_by_user_id: Optional FK to user who triggered the send
        tenant_id: Optional FK to tenant the message is about
        message_type: Category — defaults to "notification"
        email_address: Optional recipient email, enabling the email channel
        idempotency_key: Optional dedup key, unique per organisation
        email_subject: Optional override for the email subject line

    Returns:
        The primary persisted Message row (status "sent" or "failed").
        Any additional channel rows are persisted alongside it.
    """
    # ── Idempotency: a retried event must not send twice ────────────────────
    if idempotency_key:
        existing = (
            db.query(Message)
            .filter(
                Message.organization_id == organization_id,
                Message.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            return existing

    # Render the body text — both for storing AND for free-form sends
    body = templates.render_freeform(template_name, variables)
    subject = email_subject or _email_subject(template_name)

    org_settings = get_settings_or_none(db, organization_id)
    mode = channel_mode(org_settings)
    channels = resolve_channels(
        org_settings,
        has_phone=bool(phone_number),
        has_email=bool(email_address),
    )
    # "dual" delivers on every listed channel; every other mode stops at the
    # first success.
    send_all_channels = mode == "dual"

    if not channels:
        # Nothing could be attempted (all channels off/unconfigured, or no
        # destination). Record the failure rather than silently dropping the
        # notification — the audit trail must show that it did not go out.
        message = Message(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            phone_number=phone_number or None,
            email_address=email_address or None,
            direction="outgoing",
            message_type=message_type,
            content=body,
            template_name=template_name,
            status="failed",
            channel=CHANNEL_WHATSAPP,
            error_message="No delivery channel available (check communication settings)",
            idempotency_key=idempotency_key,
            triggered_by_user_id=triggered_by_user_id,
            tenant_id=tenant_id,
        )
        db.add(message)
        db.flush()
        return message

    rows: list[Message] = []

    for index, channel in enumerate(channels):
        if channel == CHANNEL_WHATSAPP:
            row = Message(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                phone_number=phone_number,
                direction="outgoing",
                message_type=message_type,
                content=body,
                template_name=template_name,
                status="queued",
                channel=CHANNEL_WHATSAPP,
                # Only the first row carries the key: it is the row later
                # lookups will find, and the unique-ish index stays cheap.
                idempotency_key=idempotency_key if index == 0 else None,
                triggered_by_user_id=triggered_by_user_id,
                tenant_id=tenant_id,
            )
            db.add(row)
            db.flush()
            _send_whatsapp(row, template_name, variables, body)
        else:
            row = Message(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                phone_number=None,
                email_address=email_address,
                direction="outgoing",
                message_type=message_type,
                content=body,
                template_name=template_name,
                status="queued",
                channel=CHANNEL_EMAIL,
                idempotency_key=idempotency_key if index == 0 else None,
                triggered_by_user_id=triggered_by_user_id,
                tenant_id=tenant_id,
            )
            db.add(row)
            db.flush()
            ok, error = send_email_message(
                email_address,
                subject,
                _html_from_body(subject, body),
            )
            row.status = "sent" if ok else "failed"
            row.error_message = error

        rows.append(row)

        # First channel succeeded and this is a fallback chain → done.
        if row.status == "sent" and not send_all_channels:
            break

    # Do NOT commit here — let the caller commit when they're ready,
    # alongside their other changes. This keeps the messaging service
    # composable with other DB operations.
    db.flush()

    return rows[0]


def send_template_message(
    db: Session,
    organization_id: str,
    phone_number: str,
    template_name: str,
    variables: dict,
    **kwargs,
) -> Message:
    """Alias for send_notification with explicit "template" semantic."""
    return send_notification(
        db=db,
        organization_id=organization_id,
        phone_number=phone_number,
        template_name=template_name,
        variables=variables,
        **kwargs,
    )


def send_freeform_message(
    db: Session,
    organization_id: str,
    phone_number: str,
    body: str,
    triggered_by_user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    message_type: str = "reply",
) -> Message:
    """
    Send a raw text message — no template.

    Use this only for replies WITHIN the 24-hour customer service window,
    or against test numbers in dev. Don't use it for cold outbound — Meta
    will block it.
    """
    message = Message(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        phone_number=phone_number,
        direction="outgoing",
        message_type=message_type,
        content=body,
        status="queued",
        channel="whatsapp",
        triggered_by_user_id=triggered_by_user_id,
        tenant_id=tenant_id,
    )
    db.add(message)
    db.flush()

    try:
        provider = _get_provider()
        result = provider.send_freeform_text(to_phone=phone_number, body=body)
        message.status = "sent"
        message.provider_message_id = result.get("provider_message_id")
    except MessagingProviderError as e:
        message.status = "failed"
        message.error_message = str(e)

    db.flush()
    return message
