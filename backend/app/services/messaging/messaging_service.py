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


# ─── Helpers ───

def _get_provider():
    """Return the active messaging provider (currently always WhatsApp)."""
    return WhatsAppProvider()


def _use_meta_templates() -> bool:
    """Whether to send via Meta-approved templates or as free-form text."""
    return settings.whatsapp.use_templates


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
) -> Message:
    """
    Send a notification using a registered template.

    This is the canonical entry point for system-generated messages
    (rent reminders, payment receipts, invites, etc).

    Args:
        db: SQLAlchemy session — caller is responsible for commit
        organization_id: Which org this message belongs to
        phone_number: Recipient phone number (any format — will be normalized)
        template_name: Key from templates.TEMPLATES
        variables: Dict of values to fill into the template
        triggered_by_user_id: Optional FK to user who triggered the send
        tenant_id: Optional FK to tenant the message is about
        message_type: Category — defaults to "notification"

    Returns:
        The persisted Message row (status will be "sent" or "failed")
    """
    # Render the body text — both for storing AND for free-form sends
    body = templates.render_freeform(template_name, variables)

    # Create the Message row in 'queued' state — we save first so we have
    # an audit trail even if the provider call fails
    message = Message(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        phone_number=phone_number,
        direction="outgoing",
        message_type=message_type,
        content=body,
        template_name=template_name,
        status="queued",
        channel="whatsapp",
        triggered_by_user_id=triggered_by_user_id,
        tenant_id=tenant_id,
    )
    db.add(message)
    db.flush()

    # Make the actual provider call
    try:
        provider = _get_provider()

        if _use_meta_templates():
            # Production mode — use Meta-approved template
            params = templates.get_template_params(template_name, variables)
            lang = templates.get_template_language(template_name)
            result = provider.send_template(
                to_phone=phone_number,
                template_name=template_name,
                template_params=params,
                language_code=lang,
            )
        else:
            # Dev mode — send free-form text (works only for test numbers
            # or within the 24h customer service window)
            result = provider.send_freeform_text(
                to_phone=phone_number,
                body=body,
            )

        message.status = "sent"
        message.provider_message_id = result.get("provider_message_id")

    except MessagingProviderError as e:
        message.status = "failed"
        message.error_message = str(e)

    # Do NOT commit here — let the caller commit when they're ready,
    # alongside their other changes. This keeps the messaging service
    # composable with other DB operations.
    db.flush()

    return message


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
