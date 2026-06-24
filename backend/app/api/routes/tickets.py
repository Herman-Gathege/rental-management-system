#backend\app\api\routes\tickets.py
"""
Ticket routes — Sprint 6.

Endpoints:
  GET    /tickets/                        list (role-scoped)
  POST   /tickets/                        create
  GET    /tickets/{id}                    detail
  PUT    /tickets/{id}                    update fields
  DELETE /tickets/{id}                    delete (landlord only)

  POST   /tickets/{id}/assign             assign / reassign
  POST   /tickets/{id}/start              → in_progress
  POST   /tickets/{id}/wait               → waiting
  POST   /tickets/{id}/resolve            → resolved
  POST   /tickets/{id}/close              → closed (manager/landlord)
  POST   /tickets/{id}/reopen             → open (landlord only)

Notifications are fired via BackgroundTasks so they never block the
HTTP response — same pattern as lease/payment notifications.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketAssignPayload,
    TicketStatusPayload,
)
from app.services import ticket_service
from app.services.notification_service import (
    notify_ticket_created,
    notify_ticket_assigned,
    notify_ticket_in_progress,
    notify_ticket_resolved,
    notify_ticket_closed,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ─── Shared deps ─────────────────────────────────────────────────────────

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


# ─── CRUD ────────────────────────────────────────────────────────────────

@router.get("/")
def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    property_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return ticket_service.list_tickets(
        db,
        membership.organization_id,
        user.id,
        membership,
        status=status,
        priority=priority,
        property_id=property_id,
        category=category,
        tenant_id=tid,
    )


@router.post("/")
def create_ticket(
    payload: TicketCreate,
    background_tasks: BackgroundTasks,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    ticket = ticket_service.create_ticket(
        db, membership.organization_id, user.id, membership, payload, tenant_id=tid
    )
    # Pizza-inn stage 1: "Your request has been received"
    background_tasks.add_task(notify_ticket_created, ticket["id"])
    return ticket


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return ticket_service.get_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, tenant_id=tid
    )


@router.put("/{ticket_id}")
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    return ticket_service.update_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload
    )


@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    return ticket_service.delete_ticket(
        db, ticket_id, membership.organization_id, user.id, membership
    )


# ─── Lifecycle transitions ───────────────────────────────────────────────

@router.post("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: str,
    payload: TicketAssignPayload,
    background_tasks: BackgroundTasks,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    ticket = ticket_service.assign_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload
    )
    # Pizza-inn stage 2: "Your issue has been assigned"
    background_tasks.add_task(notify_ticket_assigned, ticket_id)
    return ticket


@router.post("/{ticket_id}/start")
def start_ticket(
    ticket_id: str,
    payload: TicketStatusPayload = TicketStatusPayload(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    ticket = ticket_service.start_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload.reason
    )
    # Pizza-inn stage 3: "We're working on it"
    background_tasks.add_task(notify_ticket_in_progress, ticket_id)
    return ticket


@router.post("/{ticket_id}/wait")
def wait_ticket(
    ticket_id: str,
    payload: TicketStatusPayload = TicketStatusPayload(),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    return ticket_service.wait_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload.reason
    )


@router.post("/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: str,
    payload: TicketStatusPayload = TicketStatusPayload(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    ticket = ticket_service.resolve_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload.reason
    )
    # Pizza-inn stage 4: "Your issue has been resolved"
    background_tasks.add_task(notify_ticket_resolved, ticket_id)
    return ticket


@router.post("/{ticket_id}/close")
def close_ticket(
    ticket_id: str,
    payload: TicketStatusPayload = TicketStatusPayload(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    ticket = ticket_service.close_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload.reason
    )
    # Pizza-inn stage 5: "Ticket closed. Thank you!"
    background_tasks.add_task(notify_ticket_closed, ticket_id)
    return ticket


@router.post("/{ticket_id}/reopen")
def reopen_ticket(
    ticket_id: str,
    payload: TicketStatusPayload = TicketStatusPayload(),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    return ticket_service.reopen_ticket(
        db, ticket_id, membership.organization_id, user.id, membership, payload.reason
    )
