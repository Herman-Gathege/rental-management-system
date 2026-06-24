#backend\app\services\notification_service.py
"""
Notification service — Sprint 6.

Central engine for all system notifications. Follows the architecture the
guide describes: business logic (ticket_service, expense_service) calls
functions here; this module creates in-app Notification rows AND fires
WhatsApp messages through the existing messaging stack.

Pizza-inn-style tenant lifecycle notifications:
  ticket_opened      → "Your request has been received"
  ticket_assigned    → "Your issue has been assigned"
  ticket_in_progress → "Work has started"
  ticket_resolved    → "Your issue has been resolved"
  ticket_closed      → "Ticket closed. Thank you!"

Staff notifications (in-app only for now):
  ticket_created_for_staff → landlord/PM get in-app when a tenant opens a ticket

Design decisions:
  - Every function opens its own DB session (background-task safe, matching
    the pattern in notifications.py for lease/payment events).
  - Failures are logged but never re-raised so a bad notification never rolls
    back the ticket operation.
  - WhatsApp is sent only when the tenant has a phone number on their record.
  - In-app notification always written regardless of WhatsApp success/failure.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.tenant import Tenant
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property_manager import PropertyManager
from app.services.messaging import send_notification as send_whatsapp

logger = logging.getLogger(__name__)


# ─── Internal helpers ─────────────────────────────────────────────────────

def _db() -> Session:
    return SessionLocal()


def _short_id(ticket_id: str) -> str:
    return ticket_id[:8]


def _create_in_app(
    db: Session,
    org_id: str,
    user_id: str,
    title: str,
    body: str,
    notification_type: str,
) -> None:
    """Write a single in-app Notification row. Caller is responsible for commit."""
    n = Notification(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        is_read=False,
    )
    db.add(n)


def _send_tenant_whatsapp(
    db: Session,
    tenant: Tenant,
    org_id: str,
    template_name: str,
    variables: dict,
) -> None:
    """Fire a WhatsApp notification to the tenant — best-effort, logs on failure."""
    if not tenant or not tenant.phone:
        return
    try:
        send_whatsapp(
            db=db,
            organization_id=org_id,
            phone_number=tenant.phone,
            template_name=template_name,
            variables=variables,
            tenant_id=tenant.id,
            message_type="notification",
        )
    except Exception as exc:
        logger.exception(
            "WhatsApp notification '%s' failed for tenant %s: %s",
            template_name, tenant.id, exc,
        )


def _get_ticket_tenant(db: Session, ticket: Ticket) -> Optional[Tenant]:
    if not ticket.tenant_id:
        return None
    return db.query(Tenant).filter(Tenant.id == ticket.tenant_id).first()


def _get_landlord_ids(db: Session, org_id: str) -> list[str]:
    """Return user IDs of all Landlords in the org."""
    from app.models.role import Role
    rows = (
        db.query(OrganizationMember)
        .join(Role, Role.id == OrganizationMember.role_id)
        .filter(
            OrganizationMember.organization_id == org_id,
            Role.name == "LANDLORD",
        )
        .all()
    )
    return [r.user_id for r in rows]


def _get_pm_ids_for_property(db: Session, property_id: str) -> list[str]:
    """Return user IDs of PMs assigned to this property."""
    rows = (
        db.query(PropertyManager)
        .filter(PropertyManager.property_id == property_id)
        .all()
    )
    return [r.user_id for r in rows]


# ─── Public notification functions ───────────────────────────────────────
# All are designed to be called via FastAPI BackgroundTasks.
# They open their own DB session and swallow exceptions.

def notify_ticket_created(ticket_id: str) -> None:
    """
    Ticket opened by a tenant:
      - WhatsApp confirmation to tenant ("received, we'll be in touch")
      - In-app notification to landlord + assigned PMs for that property
    """
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return

        org_id = ticket.organization_id
        short = _short_id(ticket_id)
        tenant = _get_ticket_tenant(db, ticket)

        # WhatsApp → tenant (ticket_received template already existed)
        _send_tenant_whatsapp(
            db, tenant, org_id,
            "ticket_received",
            {"ticket_id": short},
        )

        # In-app → landlords
        for uid in _get_landlord_ids(db, org_id):
            _create_in_app(
                db, org_id, uid,
                title=f"New ticket #{short}",
                body=ticket.title,
                notification_type="ticket_created",
            )

        # In-app → PMs assigned to this property
        if ticket.property_id:
            for uid in _get_pm_ids_for_property(db, ticket.property_id):
                _create_in_app(
                    db, org_id, uid,
                    title=f"New ticket #{short}",
                    body=ticket.title,
                    notification_type="ticket_created",
                )

        db.commit()
    except Exception as exc:
        logger.exception("notify_ticket_created failed for %s: %s", ticket_id, exc)
        db.rollback()
    finally:
        db.close()


def notify_ticket_assigned(ticket_id: str) -> None:
    """
    Ticket assigned to a staff member:
      - WhatsApp → tenant ("your issue has been assigned")
      - In-app → the newly assigned user
    """
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return

        org_id = ticket.organization_id
        short = _short_id(ticket_id)
        tenant = _get_ticket_tenant(db, ticket)

        # WhatsApp → tenant
        _send_tenant_whatsapp(
            db, tenant, org_id,
            "ticket_assigned",
            {"ticket_id": short, "ticket_title": ticket.title},
        )

        # In-app → assigned staff member
        if ticket.assigned_to:
            _create_in_app(
                db, org_id, ticket.assigned_to,
                title=f"Ticket assigned to you #{short}",
                body=ticket.title,
                notification_type="ticket_assigned",
            )

        db.commit()
    except Exception as exc:
        logger.exception("notify_ticket_assigned failed for %s: %s", ticket_id, exc)
        db.rollback()
    finally:
        db.close()


def notify_ticket_in_progress(ticket_id: str) -> None:
    """
    Work started on ticket:
      - WhatsApp → tenant ("we're working on it")
      - In-app → ticket creator (if different from assignee)
    """
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return

        org_id = ticket.organization_id
        short = _short_id(ticket_id)
        tenant = _get_ticket_tenant(db, ticket)

        # WhatsApp → tenant
        _send_tenant_whatsapp(
            db, tenant, org_id,
            "ticket_in_progress",
            {"ticket_id": short, "ticket_title": ticket.title},
        )

        # In-app → creator (if they're a staff user, not the tenant)
        if ticket.created_by and ticket.created_by != ticket.assigned_to:
            _create_in_app(
                db, org_id, ticket.created_by,
                title=f"Work started on ticket #{short}",
                body=ticket.title,
                notification_type="ticket_in_progress",
            )

        db.commit()
    except Exception as exc:
        logger.exception("notify_ticket_in_progress failed for %s: %s", ticket_id, exc)
        db.rollback()
    finally:
        db.close()


def notify_ticket_resolved(ticket_id: str) -> None:
    """
    Ticket resolved:
      - WhatsApp → tenant ("resolved, let us know if not")
      - In-app → tenant's user account (if linked)
    """
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return

        org_id = ticket.organization_id
        short = _short_id(ticket_id)
        tenant = _get_ticket_tenant(db, ticket)

        # WhatsApp → tenant
        _send_tenant_whatsapp(
            db, tenant, org_id,
            "ticket_resolved",
            {"ticket_id": short, "ticket_title": ticket.title},
        )

        # In-app → tenant's linked user account
        if tenant and tenant.user_id:
            _create_in_app(
                db, org_id, tenant.user_id,
                title=f"Your issue has been resolved #{short}",
                body=f"{ticket.title} — please confirm or reopen if the issue persists.",
                notification_type="ticket_resolved",
            )

        db.commit()
    except Exception as exc:
        logger.exception("notify_ticket_resolved failed for %s: %s", ticket_id, exc)
        db.rollback()
    finally:
        db.close()


def notify_ticket_closed(ticket_id: str) -> None:
    """
    Ticket closed:
      - WhatsApp → tenant ("closed, thank you")
      - In-app → tenant's linked user account
    """
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return

        org_id = ticket.organization_id
        short = _short_id(ticket_id)
        tenant = _get_ticket_tenant(db, ticket)

        # WhatsApp → tenant
        _send_tenant_whatsapp(
            db, tenant, org_id,
            "ticket_closed",
            {"ticket_id": short, "ticket_title": ticket.title},
        )

        # In-app → tenant's linked user account
        if tenant and tenant.user_id:
            _create_in_app(
                db, org_id, tenant.user_id,
                title=f"Ticket closed #{short}",
                body=ticket.title,
                notification_type="ticket_closed",
            )

        db.commit()
    except Exception as exc:
        logger.exception("notify_ticket_closed failed for %s: %s", ticket_id, exc)
        db.rollback()
    finally:
        db.close()


def notify_new_message(ticket_id: str, sender_id: str, is_internal: bool) -> None:
    """
    New message on a ticket:
      - In-app → all parties on the ticket except the sender.
      - No WhatsApp for messages (avoids noise; lifecycle events cover the
        key moments; a future phase could add opt-in message notifications).
    """
    if is_internal:
        return  # Internal notes don't notify tenants

    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return

        org_id = ticket.organization_id
        short = _short_id(ticket_id)

        # Notify: creator, assignee, tenant user — excluding the sender
        recipients = set()
        if ticket.created_by:
            recipients.add(ticket.created_by)
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to)

        tenant = _get_ticket_tenant(db, ticket)
        if tenant and tenant.user_id:
            recipients.add(tenant.user_id)

        recipients.discard(sender_id)

        for uid in recipients:
            _create_in_app(
                db, org_id, uid,
                title=f"New message on ticket #{short}",
                body=ticket.title,
                notification_type="ticket_message",
            )

        db.commit()
    except Exception as exc:
        logger.exception("notify_new_message failed for %s: %s", ticket_id, exc)
        db.rollback()
    finally:
        db.close()
