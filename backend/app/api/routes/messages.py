#backend\app\api\routes\messages.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.message import Message
from app.schemas.message import (
    MessageOut,
    SendTestMessageRequest,
    SendFreeformRequest,
)
from app.services.messaging import send_notification, send_freeform_message
from app.services.messaging.templates import TEMPLATES

router = APIRouter(prefix="/messages", tags=["Messages"])


def get_user_org(user: User, db: Session):
    """Helper: get the current user's org membership or raise 403."""
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def message_dict(message: Message) -> dict:
    return {
        "id": message.id,
        "organization_id": message.organization_id,
        "phone_number": message.phone_number,
        "direction": message.direction,
        "message_type": message.message_type,
        "content": message.content,
        "template_name": message.template_name,
        "status": message.status,
        "provider_message_id": message.provider_message_id,
        "error_message": message.error_message,
        "channel": message.channel,
        "tenant_id": message.tenant_id,
        "created_at": message.created_at,
        "updated_at": message.updated_at,
    }


# ─── List Messages ───

@router.get("/")
def list_messages(
    direction: Optional[str] = Query(None, description="outgoing or incoming"),
    phone_number: Optional[str] = Query(None, description="Filter by recipient/sender phone"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    status: Optional[str] = Query(None, description="queued / sent / delivered / read / failed"),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List messages for the current organization with optional filters."""
    membership = get_user_org(current_user, db)

    query = db.query(Message).filter(
        Message.organization_id == membership.organization_id
    )

    if direction:
        query = query.filter(Message.direction == direction)
    if phone_number:
        query = query.filter(Message.phone_number == phone_number)
    if tenant_id:
        query = query.filter(Message.tenant_id == tenant_id)
    if status:
        query = query.filter(Message.status == status)

    messages = query.order_by(Message.created_at.desc()).limit(limit).all()

    return [message_dict(m) for m in messages]


# ─── Get Single Message ───

@router.get("/{message_id}")
def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)

    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.organization_id == membership.organization_id,
        )
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message_dict(message)


# ─── List Available Templates (utility) ───

@router.get("/templates/list")
def list_templates(
    current_user: User = Depends(get_current_user),
):
    """
    Return the catalogue of registered templates.

    Useful for the frontend to know what's sendable and what variables
    each template needs.
    """
    return {
        name: {
            "param_order": tmpl["param_order"],
            "preview": tmpl["template_body_freeform"],
            "language_code": tmpl["language_code"],
        }
        for name, tmpl in TEMPLATES.items()
    }


# ─── Send Test Message (TEMPLATE) ───

@router.post("/send-test")
def send_test_message(
    payload: SendTestMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually send a templated message — useful for testing and ad-hoc sends.

    The endpoint validates that the template exists and that all required
    variables are present, then sends via the messaging service.

    Example body:
    {
        "phone_number": "+254712345678",
        "template_name": "payment_receipt",
        "variables": {
            "tenant_name": "Jane Doe",
            "amount": "15,000",
            "date": "2026-05-19"
        }
    }
    """
    membership = get_user_org(current_user, db)

    if payload.template_name not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template '{payload.template_name}'. "
                   f"Available: {list(TEMPLATES.keys())}"
        )

    # Check all required variables are present
    required = TEMPLATES[payload.template_name]["param_order"]
    missing = [k for k in required if k not in payload.variables]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required variables: {missing}"
        )

    message = send_notification(
        db=db,
        organization_id=membership.organization_id,
        phone_number=payload.phone_number,
        template_name=payload.template_name,
        variables=payload.variables,
        triggered_by_user_id=current_user.id,
        message_type="manual",
    )

    db.commit()
    db.refresh(message)

    return message_dict(message)


# ─── Send Free-form Text ───

@router.post("/send-freeform")
def send_freeform(
    payload: SendFreeformRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a raw text message — no template.

    Only works within the 24-hour customer service window, or against
    Meta test numbers in dev mode.
    """
    membership = get_user_org(current_user, db)

    message = send_freeform_message(
        db=db,
        organization_id=membership.organization_id,
        phone_number=payload.phone_number,
        body=payload.body,
        triggered_by_user_id=current_user.id,
    )

    db.commit()
    db.refresh(message)

    return message_dict(message)
