#backend\app\services\messaging\notifications.py
"""
Event-driven notification helpers.

This module is the bridge between business events (lease created, payment
received, charge generated, invitation sent) and the underlying messaging
service. Each function here represents ONE event in the system's lifecycle.

Why a separate module?

  - Routes shouldn't know template names. A route says
    `notify_lease_created(...)` — not `send_notification("lease_welcome",...)`.
    If we ever rename the template or restructure variables, routes don't
    care.

  - Tenant phone + name + property/unit lookups live here, not duplicated
    in every route. Lookup logic stays in one place.

  - These functions are designed to be called via FastAPI's BackgroundTasks
    so they never block the HTTP response. A failed WhatsApp send must never
    block a successful lease/payment creation.

Background-task safety contract:

  Every function in this module:
    1. Opens its own DB session (the request session is closed by the time
       the background task runs)
    2. Catches & logs all exceptions — never re-raises (would crash the
       background worker)
    3. Returns None — no caller will await the result

The actual provider call (Meta WhatsApp Cloud API) still happens inside
`send_notification`, which persists a Message row regardless of success
or failure. So even a notification that fails to deliver leaves an audit
trail in the messages table.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.charge import Charge
from app.models.lease import Lease
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.payment import Payment
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.users import User
from app.services.email_service import send_email
from app.services.messaging import send_notification

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────

def _db() -> Session:
    """
    Open a fresh DB session for the background task.

    The request-scoped session passed to the route handler is closed by
    the time the background task runs, so we need our own.
    """
    return SessionLocal()


def _format_amount(amount) -> str:
    """
    Format a numeric amount for human display in WhatsApp messages.

    Example: 15000.00 -> "15,000"
    Falls back to str(amount) on any error.
    """
    try:
        # Convert Decimal/float to int when there's no fractional part,
        # otherwise keep 2 decimal places.
        amt = float(amount)
        if amt == int(amt):
            return f"{int(amt):,}"
        return f"{amt:,.2f}"
    except (TypeError, ValueError):
        return str(amount)


def _format_date(d) -> str:
    """
    Format a date for human display.

    Example: date(2026, 5, 21) -> "21 May 2026"
    """
    if d is None:
        return ""
    try:
        return d.strftime("%d %b %Y")
    except AttributeError:
        return str(d)


def _safe_send(send_fn, event_label: str, **kwargs) -> None:
    """
    Call a send function inside a logged try/except.

    `event_label` is what shows up in the log line on failure so we
    can identify which event broke without parsing tracebacks. It is
    NOT forwarded to the underlying send function.
    """
    try:
        send_fn(**kwargs)
    except Exception as exc:  # noqa: BLE001 — background tasks must not raise
        logger.exception(
            "Notification send failed for event=%s: %s",
            event_label, exc,
        )


# ─────────────────────────────────────────────────────────────────────────
# Public notification helpers
# ─────────────────────────────────────────────────────────────────────────

def notify_lease_created(lease_id: str) -> None:
    """
    Send a 'lease_welcome' WhatsApp to the tenant when their lease is created.

    Template: lease_welcome
    Vars:     tenant_name, property_name, unit_name

    Called from POST /leases/ after commit.
    """
    db = _db()
    try:
        lease = db.query(Lease).filter(Lease.id == lease_id).first()
        if not lease:
            logger.warning("notify_lease_created: lease %s not found", lease_id)
            return

        tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
        if not tenant or not tenant.phone:
            logger.warning(
                "notify_lease_created: tenant %s missing or has no phone",
                lease.tenant_id,
            )
            return

        unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
        prop = (
            db.query(Property).filter(Property.id == unit.property_id).first()
            if unit else None
        )

        _safe_send(
            send_notification,
            "lease_created",
            db=db,
            organization_id=lease.organization_id,
            phone_number=tenant.phone,
            template_name="lease_welcome",
            variables={
                "tenant_name": tenant.full_name,
                "property_name": prop.name if prop else "your property",
                "unit_name": unit.name if unit else "your unit",
            },
            tenant_id=tenant.id,
            message_type="notification",
        )
        db.commit()
    finally:
        db.close()


def notify_payment_received(payment_id: str) -> None:
    """
    Send a 'payment_receipt' WhatsApp to the tenant when their payment is recorded.

    Template: payment_receipt
    Vars:     tenant_name, amount, date

    Called from POST /payments/ after commit.
    """
    db = _db()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            logger.warning(
                "notify_payment_received: payment %s not found", payment_id,
            )
            return

        tenant = db.query(Tenant).filter(Tenant.id == payment.tenant_id).first()
        if not tenant or not tenant.phone:
            logger.warning(
                "notify_payment_received: tenant %s missing or has no phone",
                payment.tenant_id,
            )
            return

        _safe_send(
            send_notification,
            "payment_received",
            db=db,
            organization_id=payment.organization_id,
            phone_number=tenant.phone,
            template_name="payment_receipt",
            variables={
                "tenant_name": tenant.full_name,
                "amount": _format_amount(payment.amount),
                "date": _format_date(payment.payment_date),
            },
            tenant_id=tenant.id,
            message_type="notification",
        )
        db.commit()
    finally:
        db.close()


def notify_rent_due_for_charges(charge_ids: list[str]) -> None:
    """
    Send 'rent_due_reminder' WhatsApps for a batch of newly-generated charges.

    Template: rent_due_reminder
    Vars:     tenant_name, amount, due_date

    Called from POST /charges/generate-monthly after commit. Receives the
    list of charge IDs that were just created so we don't re-notify on
    existing charges.

    One commit per charge is intentional — a failed send for charge #3
    shouldn't roll back the audit trail of charges #1 and #2.
    """
    if not charge_ids:
        return

    db = _db()
    try:
        for charge_id in charge_ids:
            charge = db.query(Charge).filter(Charge.id == charge_id).first()
            if not charge:
                logger.warning(
                    "notify_rent_due_for_charges: charge %s not found",
                    charge_id,
                )
                continue

            lease = db.query(Lease).filter(Lease.id == charge.lease_id).first()
            if not lease:
                continue

            tenant = (
                db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
            )
            if not tenant or not tenant.phone:
                logger.info(
                    "notify_rent_due_for_charges: skipping charge %s — tenant "
                    "missing phone",
                    charge_id,
                )
                continue

            _safe_send(
                send_notification,
                f"rent_due_charge_{charge_id}",
                db=db,
                organization_id=charge.organization_id,
                phone_number=tenant.phone,
                template_name="rent_due_reminder",
                variables={
                    "tenant_name": tenant.full_name,
                    "amount": _format_amount(charge.amount),
                    "due_date": _format_date(charge.due_date),
                },
                tenant_id=tenant.id,
                message_type="notification",
            )
            db.commit()
    finally:
        db.close()


def notify_org_invite(
    invitation_id: str,
    phone: Optional[str] = None,
) -> None:
    """
    Send a 'staff_invite' WhatsApp containing the invitation link.

    Template: staff_invite
    Vars:     org_name, role, link

    Called from POST /organizations/invite after commit. If the invitation
    didn't capture a phone number, this is a no-op (log warning) — the
    admin must share the token via another channel.

    Args:
        invitation_id: The OrganizationInvitation.id we just created
        phone: Optional phone number from the invite request. If omitted,
               we'll look it up from the invitation row.
    """
    # Lazy import to avoid circular dependency at module load
    from app.models.organization_invitation import OrganizationInvitation

    db = _db()
    try:
        invitation = (
            db.query(OrganizationInvitation)
            .filter(OrganizationInvitation.id == invitation_id)
            .first()
        )
        if not invitation:
            logger.warning(
                "notify_org_invite: invitation %s not found", invitation_id,
            )
            return

        # Phone resolution priority:
        #   1. Explicit phone arg from caller
        #   2. invitation.phone column (added in Chunk C)
        #   3. Skip with warning if neither
        recipient_phone = phone or getattr(invitation, "phone", None)
        if not recipient_phone:
            logger.warning(
                "notify_org_invite: no phone for invitation %s — admin must "
                "share token manually",
                invitation_id,
            )
            return

        org = (
            db.query(Organization)
            .filter(Organization.id == invitation.organization_id)
            .first()
        )
        if not org:
            logger.warning(
                "notify_org_invite: org %s not found for invitation %s",
                invitation.organization_id, invitation_id,
            )
            return

        # Build the acceptance link. The frontend route is the contract
        # between backend (here) and the React app's invite-accept page.
        # If your frontend route differs, this is the line to change.
        invite_link = f"http://localhost:5173/accept-invite/{invitation.token}"

        _safe_send(
            send_notification,
            "org_invite",
            db=db,
            organization_id=invitation.organization_id,
            phone_number=recipient_phone,
            template_name="staff_invite",
            variables={
                "org_name": org.name,
                "role": invitation.role.name if invitation.role else "team member",
                "link": invite_link,
            },
            message_type="invite",
        )
        db.commit()
    finally:
        db.close()


def notify_account_locked(user_id: str) -> None:
    """
    Send an 'account_locked' alert to a user whose account was just
    temporarily locked after 5 failed login attempts.

    Template: account_locked (WhatsApp) or plain HTML email fallback.
    Vars:     user_email, unlock_time

    Channel priority:
      1. WhatsApp — if the user has a verified phone AND at least one
         organization membership (needed for the messaging service to
         attach the Message row to an org for audit).
      2. Email — otherwise, using send_email() from email_service.

    Called from auth.login() as a background task ONLY on the failure
    that crossed the threshold. Subsequent failures during the same lock
    window do not re-notify.
    """
    db = _db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("notify_account_locked: user %s not found", user_id)
            return
        if not user.locked_until:
            logger.warning(
                "notify_account_locked: user %s has no locked_until "
                "(lockout was cleared before notification ran)",
                user_id,
            )
            return

        unlock_str = user.locked_until.strftime("%d %b %Y %H:%M UTC")

        # Look up org for messaging service context. If none, fall back
        # to email since send_notification requires an organization_id.
        membership = (
            db.query(OrganizationMember)
            .filter(OrganizationMember.user_id == user.id)
            .first()
        )
        org_id = membership.organization_id if membership else None

        # Prefer WhatsApp when possible.
        if user.phone and user.phone_verified and org_id:
            _safe_send(
                send_notification,
                "account_locked",
                db=db,
                organization_id=org_id,
                phone_number=user.phone,
                template_name="account_locked",
                variables={
                    "user_email": user.email,
                    "unlock_time": unlock_str,
                },
                message_type="notification",
            )
            db.commit()
            return

        # Fall back to email. Failure here is logged but not raised —
        # this is a best-effort notification.
        try:
            send_email(
                user.email,
                "Your account was temporarily locked",
                (
                    "<p>Hi,</p>"
                    f"<p>Someone tried to sign in to your account ({user.email}) "
                    "and failed too many times. Your account has been "
                    f"temporarily locked until <b>{unlock_str}</b>.</p>"
                    "<p>If this wasn't you, we recommend resetting your "
                    "password once the lock lifts.</p>"
                ),
            )
        except Exception as exc:  # noqa: BLE001 — background task
            logger.exception(
                "notify_account_locked: email fallback failed for %s: %s",
                user.email, exc,
            )
    finally:
        db.close()
