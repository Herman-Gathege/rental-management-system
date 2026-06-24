#backend\app\api\routes\ticket_conversation.py
"""
Ticket conversation routes — Sprint 6.

Nested under /tickets/{ticket_id}/:

  GET    /tickets/{id}/messages                list messages
  POST   /tickets/{id}/messages                post a message (or internal note)
  DELETE /tickets/{id}/messages/{message_id}   delete a message

  GET    /tickets/{id}/attachments             list attachments
  POST   /tickets/{id}/attachments             upload a file
  DELETE /tickets/{id}/attachments/{att_id}    delete an attachment
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.schemas.ticket import TicketMessageCreate
from app.services import ticket_conversation_service as conv

router = APIRouter(prefix="/tickets", tags=["Ticket Conversation"])


# ─── Shared dep ──────────────────────────────────────────────────────────

def get_user_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No organization membership")
    return current_user, membership, db


def _tenant_id(user: User, membership: OrganizationMember, db: Session) -> Optional[str]:
    from app.core.roles import TENANT
    if membership.role.name != TENANT:
        return None
    tenant = db.query(Tenant).filter(Tenant.user_id == user.id).first()
    return tenant.id if tenant else None


# ─── Messages ────────────────────────────────────────────────────────────

@router.get("/{ticket_id}/messages")
def list_messages(
    ticket_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return conv.list_messages(
        db, ticket_id, membership.organization_id, user.id, membership, tenant_id=tid
    )


@router.post("/{ticket_id}/messages")
def add_message(
    ticket_id: str,
    payload: TicketMessageCreate,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return conv.add_message(
        db, ticket_id, membership.organization_id, user.id, membership, payload, tenant_id=tid
    )


@router.delete("/{ticket_id}/messages/{message_id}")
def delete_message(
    ticket_id: str,
    message_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return conv.delete_message(
        db, ticket_id, message_id, membership.organization_id, user.id, membership, tenant_id=tid
    )


# ─── Attachments ─────────────────────────────────────────────────────────

@router.get("/{ticket_id}/attachments")
def list_attachments(
    ticket_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return conv.list_attachments(
        db, ticket_id, membership.organization_id, user.id, membership, tenant_id=tid
    )


@router.post("/{ticket_id}/attachments")
async def add_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    file_bytes = await file.read()
    return conv.add_attachment(
        db,
        ticket_id,
        membership.organization_id,
        user.id,
        membership,
        file_bytes=file_bytes,
        filename=file.filename,
        tenant_id=tid,
    )


@router.delete("/{ticket_id}/attachments/{attachment_id}")
def delete_attachment(
    ticket_id: str,
    attachment_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return conv.delete_attachment(
        db, ticket_id, attachment_id, membership.organization_id, user.id, membership, tenant_id=tid
    )
