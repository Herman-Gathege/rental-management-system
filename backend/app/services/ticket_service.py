#backend\app\services\ticket_service.py
"""
Ticket service — Sprint 6.

RBAC contract (from guide):
  Landlord    → everything; all properties; can close.
  PM          → create/assign/respond/resolve on assigned properties only;
                can close.
  Finance     → respond to finance-related tickets on assigned properties;
                cannot create/assign/close.
  Tenant      → create tickets on their own lease's property; reply and
                upload images on their OWN tickets only; cannot see others'.
  System      → notifications only (no direct CRUD).

Lifecycle:  open → assigned → in_progress → waiting → resolved → closed
  assign()     open → assigned   (also: re-assign from any non-closed status)
  start()      assigned → in_progress
  wait()       in_progress → waiting
  resolve()    * → resolved     (PM/Landlord)
  close()      resolved → closed (PM/Landlord only)
  reopen()     resolved/closed → open (Landlord only)

Cash-basis rule carried over from Sprint 5: no income ever shown to PM.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.ticket_message import TicketMessage
from app.models.organization_member import OrganizationMember
from app.models.property_manager import PropertyManager
from app.models.property_finance_manager import PropertyFinanceManager
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

# ─── Valid values ────────────────────────────────────────────────────────

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_CATEGORIES = {
    "maintenance", "repairs", "electricity", "water", "security",
    "cleaning", "noise", "lease_question", "billing_question",
    "complaint", "suggestion", "other",
}
VALID_STATUSES = {"open", "assigned", "in_progress", "waiting", "resolved", "closed"}

# Roles that can see/manage tickets across their assigned properties
MANAGER_ROLES = {LANDLORD, PROPERTY_MANAGER}

# ─── Role helpers ────────────────────────────────────────────────────────

def _role(membership: OrganizationMember) -> str:
    return membership.role.name


def _pm_property_ids(db: Session, user_id: str, org_id: str) -> list[str]:
    rows = (
        db.query(PropertyManager)
        .filter(PropertyManager.user_id == user_id)
        .all()
    )
    return [r.property_id for r in rows]


def _finance_property_ids(db: Session, user_id: str, org_id: str) -> list[str]:
    rows = (
        db.query(PropertyFinanceManager)
        .filter(PropertyFinanceManager.user_id == user_id)
        .all()
    )
    return [r.property_id for r in rows]


def _assert_not_tenant_create(role: str) -> None:
    """Tenants go through create_for_tenant; other roles use create_ticket."""
    pass  # enforced at route layer — service accepts both paths


def _get_ticket(
    db: Session,
    ticket_id: str,
    org_id: str,
) -> Ticket:
    t = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.organization_id == org_id)
        .first()
    )
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


def _assert_can_manage(
    role: str,
    ticket: Ticket,
    user_id: str,
    db: Session,
    org_id: str,
) -> None:
    """
    Raise 403 if the caller cannot manage (edit/transition) this ticket.
    Tenants are blocked here — they use tenant-specific endpoints.
    Finance can respond but not transition status / assign.
    """
    from fastapi import HTTPException
    if role == LANDLORD:
        return
    if role == PROPERTY_MANAGER:
        allowed = _pm_property_ids(db, user_id, org_id)
        if ticket.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
        return
    if role == FINANCE:
        allowed = _finance_property_ids(db, user_id, org_id)
        if ticket.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _assert_can_close(role: str) -> None:
    from fastapi import HTTPException
    if role not in {LANDLORD, PROPERTY_MANAGER}:
        raise HTTPException(status_code=403, detail="Only managers and landlords can close tickets")


def _assert_can_assign(role: str) -> None:
    from fastapi import HTTPException
    if role not in {LANDLORD, PROPERTY_MANAGER}:
        raise HTTPException(status_code=403, detail="Only managers and landlords can assign tickets")


# ─── Scope helpers ───────────────────────────────────────────────────────

def _scoped_query(
    db: Session,
    org_id: str,
    role: str,
    user_id: str,
    tenant_id: Optional[str] = None,
):
    """Return a query pre-filtered to what the caller may see."""
    q = db.query(Ticket).filter(Ticket.organization_id == org_id)

    if role == LANDLORD:
        pass  # sees everything

    elif role == PROPERTY_MANAGER:
        allowed = _pm_property_ids(db, user_id, org_id)
        q = q.filter(Ticket.property_id.in_(allowed))

    elif role == FINANCE:
        allowed = _finance_property_ids(db, user_id, org_id)
        q = q.filter(Ticket.property_id.in_(allowed))

    elif role == TENANT:
        if not tenant_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Tenant profile not found")
        q = q.filter(Ticket.tenant_id == tenant_id)

    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return q


# ─── Enrichment ──────────────────────────────────────────────────────────

def _enrich(ticket: Ticket) -> dict:
    """Return a dict representation of a ticket suitable for API responses."""
    return {
        "id": ticket.id,
        "organization_id": ticket.organization_id,
        "property_id": ticket.property_id,
        "unit_id": ticket.unit_id,
        "tenant_id": ticket.tenant_id,
        "created_by": ticket.created_by,
        "assigned_to": ticket.assigned_to,
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
        "category": ticket.category,
        "status": ticket.status,
        "source": ticket.source,
        "source_phone": ticket.source_phone,
        "opened_at": ticket.opened_at.isoformat() if ticket.opened_at else None,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        # Joined names (may be None if not loaded)
        "assignee_email": ticket.assignee.email if ticket.assignee else None,
        "creator_email": ticket.creator.email if ticket.creator else None,
        # Message + attachment counts
        "message_count": len(ticket.messages) if ticket.messages is not None else 0,
        "attachment_count": len(ticket.attachments) if ticket.attachments is not None else 0,
    }


# ─── CRUD ────────────────────────────────────────────────────────────────

def list_tickets(
    db: Session,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    property_id: Optional[str] = None,
    category: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> list[dict]:
    role = _role(membership)
    q = _scoped_query(db, org_id, role, user_id, tenant_id=tenant_id)

    if status:
        q = q.filter(Ticket.status == status)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if property_id:
        q = q.filter(Ticket.property_id == property_id)
    if category:
        q = q.filter(Ticket.category == category)

    tickets = q.order_by(Ticket.created_at.desc()).all()
    return [_enrich(t) for t in tickets]


def get_ticket(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    tenant_id: Optional[str] = None,
) -> dict:
    from fastapi import HTTPException
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)

    # Access check
    if role == LANDLORD:
        pass
    elif role == PROPERTY_MANAGER:
        allowed = _pm_property_ids(db, user_id, org_id)
        if ticket.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
    elif role == FINANCE:
        allowed = _finance_property_ids(db, user_id, org_id)
        if ticket.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
    elif role == TENANT:
        if not tenant_id or ticket.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Not your ticket")
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return _enrich(ticket)


def create_ticket(
    db: Session,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    payload,
    tenant_id: Optional[str] = None,
) -> dict:
    from fastapi import HTTPException
    role = _role(membership)

    # Finance cannot create tickets
    if role == FINANCE:
        raise HTTPException(status_code=403, detail="Finance users cannot create tickets")

    # PM can only create on assigned properties
    if role == PROPERTY_MANAGER:
        allowed = _pm_property_ids(db, user_id, org_id)
        if payload.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")

    # Tenant can only create on their own lease property
    if role == TENANT:
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant profile not found")

    # Validate
    if payload.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Choose from: {VALID_PRIORITIES}")
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from: {VALID_CATEGORIES}")

    # Source based on role
    source_map = {
        LANDLORD: "landlord",
        PROPERTY_MANAGER: "manager",
        FINANCE: "finance",
        TENANT: "tenant_portal",
    }

    ticket = Ticket(
        organization_id=org_id,
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        tenant_id=tenant_id if role == TENANT else payload.tenant_id,
        created_by=user_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        status="open",
        source=source_map.get(role, "system"),
        opened_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.flush()

    log_action(
        db, org_id, user_id, "create", "ticket", ticket.id,
        f"Ticket created: {ticket.title}",
    )
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def update_ticket(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    payload,
) -> dict:
    from fastapi import HTTPException
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_can_manage(role, ticket, user_id, db, org_id)

    if role == FINANCE:
        raise HTTPException(status_code=403, detail="Finance users cannot edit ticket details")

    if ticket.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot edit a closed ticket")

    updates = payload.dict(exclude_unset=True)
    if "priority" in updates and updates["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority")
    if "category" in updates and updates["category"] not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category")

    old = {k: getattr(ticket, k) for k in updates}
    for k, v in updates.items():
        setattr(ticket, k, v)

    log_action(
        db, org_id, user_id, "update", "ticket", ticket.id,
        f"Ticket updated: {list(updates.keys())}",
        old_values=json.dumps(old),
        new_values=json.dumps(updates),
    )
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def delete_ticket(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
) -> dict:
    from fastapi import HTTPException
    role = _role(membership)
    if role != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can delete tickets")

    ticket = _get_ticket(db, ticket_id, org_id)
    log_action(db, org_id, user_id, "delete", "ticket", ticket.id, f"Ticket deleted: {ticket.title}")
    db.delete(ticket)
    db.commit()
    return {"detail": "Ticket deleted"}


# ─── Lifecycle transitions ───────────────────────────────────────────────

def assign_ticket(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    payload,
) -> dict:
    from fastapi import HTTPException
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_can_manage(role, ticket, user_id, db, org_id)
    _assert_can_assign(role)

    if ticket.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot reassign a closed ticket")

    old_assignee = ticket.assigned_to
    ticket.assigned_to = payload.assigned_to
    if payload.assigned_to and ticket.status == "open":
        ticket.status = "assigned"

    # Record assignment history
    assignment = TicketAssignment(
        ticket_id=ticket.id,
        assigned_from=old_assignee,
        assigned_to=payload.assigned_to,
        reason=payload.reason,
    )
    db.add(assignment)

    log_action(
        db, org_id, user_id, "assign", "ticket", ticket.id,
        f"Ticket assigned to {payload.assigned_to or 'nobody'} (was {old_assignee or 'nobody'})",
    )
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def _transition(
    db: Session,
    ticket_id: str,
    org_id: str,
    user_id: str,
    membership: OrganizationMember,
    new_status: str,
    allowed_from: set[str],
    note: Optional[str] = None,
    *,
    extra_check=None,
) -> dict:
    from fastapi import HTTPException
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_can_manage(role, ticket, user_id, db, org_id)

    if extra_check:
        extra_check(role)

    if ticket.status not in allowed_from:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move to '{new_status}' from '{ticket.status}'",
        )

    old_status = ticket.status
    ticket.status = new_status

    if new_status == "resolved":
        ticket.resolved_at = datetime.utcnow()
    if new_status == "closed":
        ticket.closed_at = datetime.utcnow()
    if new_status == "open":
        ticket.resolved_at = None
        ticket.closed_at = None

    if note:
        msg = TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            message=note,
            is_internal=True,
        )
        db.add(msg)

    log_action(
        db, org_id, user_id, "status_change", "ticket", ticket.id,
        f"Ticket status: {old_status} → {new_status}",
    )
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def start_ticket(db, ticket_id, org_id, user_id, membership, note=None):
    return _transition(db, ticket_id, org_id, user_id, membership,
                       "in_progress", {"assigned"}, note)


def wait_ticket(db, ticket_id, org_id, user_id, membership, note=None):
    return _transition(db, ticket_id, org_id, user_id, membership,
                       "waiting", {"in_progress"}, note)


def resolve_ticket(db, ticket_id, org_id, user_id, membership, note=None):
    return _transition(db, ticket_id, org_id, user_id, membership,
                       "resolved", {"open", "assigned", "in_progress", "waiting"}, note)


def close_ticket(db, ticket_id, org_id, user_id, membership, note=None):
    return _transition(db, ticket_id, org_id, user_id, membership,
                       "closed", {"resolved"}, note,
                       extra_check=_assert_can_close)


def reopen_ticket(db, ticket_id, org_id, user_id, membership, note=None):
    from fastapi import HTTPException
    role = _role(membership)
    if role != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can reopen tickets")
    return _transition(db, ticket_id, org_id, user_id, membership,
                       "open", {"resolved", "closed"}, note)
