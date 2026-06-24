#backend\app\services\ticket_conversation_service.py
"""
Ticket conversation service — Sprint 6.

Handles the two child resources of a ticket:
  - TicketMessages: threaded replies from any stakeholder. Internal notes
    (is_internal=True) are visible only to staff, never to tenants.
  - TicketAttachments: file uploads (photos, invoices, receipts, PDFs).

RBAC:
  Landlord  → read/write all messages + attachments on any ticket in org.
  PM        → read/write on their assigned-property tickets.
  Finance   → read/write on their assigned-property tickets.
  Tenant    → read/write on their OWN tickets only; cannot post or see
              internal notes; cannot delete attachments posted by others.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT
from app.models.organization_member import OrganizationMember
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.models.ticket_attachment import TicketAttachment
from app.services.audit_service import log_action
from app.services.s3_service import upload_file


# ─── Helpers ─────────────────────────────────────────────────────────────

def _role(membership: OrganizationMember) -> str:
    return membership.role.name


def _get_ticket(db: Session, ticket_id: str, org_id: str) -> Ticket:
    t = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.organization_id == org_id)
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


def _assert_ticket_access(
    role: str,
    ticket: Ticket,
    user_id: str,
    db: Session,
    org_id: str,
    tenant_id: Optional[str] = None,
) -> None:
    """Raise 403 if the caller cannot access this ticket's conversation."""
    from app.models.property_manager import PropertyManager
    from app.models.property_finance_manager import PropertyFinanceManager

    if role == LANDLORD:
        return

    if role == PROPERTY_MANAGER:
        from app.models.property import Property
        allowed = [
            r.property_id
            for r in db.query(PropertyManager)
            .filter(PropertyManager.user_id == user_id)
            .all()
        ]
        if ticket.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
        return

    if role == FINANCE:
        allowed = [
            r.property_id
            for r in db.query(PropertyFinanceManager)
            .filter(PropertyFinanceManager.user_id == user_id)
            .all()
        ]
        if ticket.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
        return

    if role == TENANT:
        if not tenant_id or ticket.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Not your ticket")
        return

    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _enrich_message(msg: TicketMessage) -> dict:
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "sender_email": msg.sender.email if msg.sender else None,
        "message": msg.message,
        "is_internal": msg.is_internal,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _enrich_attachment(att: TicketAttachment) -> dict:
    return {
        "id": att.id,
        "ticket_id": att.ticket_id,
        "uploaded_by": att.uploaded_by,
        "file_name": att.file_name,
        "file_url": att.file_url,
        "created_at": att.created_at.isoformat() if att.created_at else None,
    }


# ─── Messages ────────────────────────────────────────────────────────────

def list_messages(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    tenant_id: Optional[str] = None,
) -> list[dict]:
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_ticket_access(role, ticket, user_id, db, org_id, tenant_id=tenant_id)

    q = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id)

    # Tenants never see internal notes.
    if role == TENANT:
        q = q.filter(TicketMessage.is_internal == False)  # noqa: E712

    messages = q.order_by(TicketMessage.created_at.asc()).all()
    return [_enrich_message(m) for m in messages]


def add_message(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    payload,
    tenant_id: Optional[str] = None,
) -> dict:
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_ticket_access(role, ticket, user_id, db, org_id, tenant_id=tenant_id)

    if ticket.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot add messages to a closed ticket")

    # Tenants cannot post internal notes.
    is_internal = payload.is_internal
    if role == TENANT and is_internal:
        raise HTTPException(status_code=403, detail="Tenants cannot post internal notes")

    msg = TicketMessage(
        id=str(uuid.uuid4()),
        ticket_id=ticket_id,
        sender_id=user_id,
        message=payload.message,
        is_internal=is_internal,
    )
    db.add(msg)
    db.flush()

    log_action(
        db, org_id, user_id, "create", "ticket_message", msg.id,
        f"{'[Internal] ' if is_internal else ''}Message added to ticket {ticket_id[:8]}",
    )
    db.commit()
    db.refresh(msg)
    return _enrich_message(msg)


def delete_message(
    db: Session,
    ticket_id: str,
    message_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    tenant_id: Optional[str] = None,
) -> dict:
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_ticket_access(role, ticket, user_id, db, org_id, tenant_id=tenant_id)

    msg = (
        db.query(TicketMessage)
        .filter(TicketMessage.id == message_id, TicketMessage.ticket_id == ticket_id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Tenants can only delete their own messages; staff can delete any.
    if role == TENANT and msg.sender_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own messages")

    # Nobody can delete internal notes except Landlord/PM/Finance.
    if msg.is_internal and role == TENANT:
        raise HTTPException(status_code=403, detail="Cannot delete internal notes")

    log_action(db, org_id, user_id, "delete", "ticket_message", msg.id,
               f"Message deleted from ticket {ticket_id[:8]}")
    db.delete(msg)
    db.commit()
    return {"detail": "Message deleted"}


# ─── Attachments ─────────────────────────────────────────────────────────

def list_attachments(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    tenant_id: Optional[str] = None,
) -> list[dict]:
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_ticket_access(role, ticket, user_id, db, org_id, tenant_id=tenant_id)

    attachments = (
        db.query(TicketAttachment)
        .filter(TicketAttachment.ticket_id == ticket_id)
        .order_by(TicketAttachment.created_at.asc())
        .all()
    )
    return [_enrich_attachment(a) for a in attachments]


def add_attachment(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    *,
    file_bytes: bytes,
    filename: str,
    tenant_id: Optional[str] = None,
) -> dict:
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_ticket_access(role, ticket, user_id, db, org_id, tenant_id=tenant_id)

    if ticket.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot add attachments to a closed ticket")

    s3_key = f"ticket-attachments/{ticket_id}/{uuid.uuid4()}-{filename}"
    try:
        file_url = upload_file(s3_key, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    att = TicketAttachment(
        id=str(uuid.uuid4()),
        ticket_id=ticket_id,
        uploaded_by=user_id,
        file_name=filename,
        file_url=file_url,
    )
    db.add(att)
    db.flush()

    log_action(
        db, org_id, user_id, "create", "ticket_attachment", att.id,
        f"Attachment '{filename}' added to ticket {ticket_id[:8]}",
    )
    db.commit()
    db.refresh(att)
    return _enrich_attachment(att)


def delete_attachment(
    db: Session,
    ticket_id: str,
    attachment_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    tenant_id: Optional[str] = None,
) -> dict:
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_ticket_access(role, ticket, user_id, db, org_id, tenant_id=tenant_id)

    att = (
        db.query(TicketAttachment)
        .filter(
            TicketAttachment.id == attachment_id,
            TicketAttachment.ticket_id == ticket_id,
        )
        .first()
    )
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Tenants can only delete their own uploads.
    if role == TENANT and att.uploaded_by != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own attachments")

    log_action(
        db, org_id, user_id, "delete", "ticket_attachment", att.id,
        f"Attachment '{att.file_name}' removed from ticket {ticket_id[:8]}",
    )
    # S3 object left for cleanup job; only drop the DB row.
    db.delete(att)
    db.commit()
    return {"detail": "Attachment deleted"}
