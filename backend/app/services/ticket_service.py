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

Sprint 7 follow-up (audit): lifecycle transitions now log distinct action
verbs (`start`, `wait`, `resolve`, `close`, `reopen`) rather than a generic
`status_change`, so the audit log is filterable by specific event — per
the guide's Module 3 list ("Ticket Closed" is a named event). Also fixes
a bug in update_ticket that was double-JSON-encoding old/new values.
"""

from __future__ import annotations

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

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_CATEGORIES = {
    "maintenance", "repairs", "electricity", "water", "security",
    "cleaning", "noise", "lease_question", "billing_question",
    "complaint", "suggestion", "other",
}
VALID_STATUSES = {"open", "assigned", "in_progress", "waiting", "resolved", "closed"}
MANAGER_ROLES = {LANDLORD, PROPERTY_MANAGER}

# Sprint 7 follow-up: each status transition audits under its own action
# verb so the log is filterable per event. Reaching "open" via _transition
# is always a reopen (initial create doesn't go through _transition).
_TRANSITION_ACTION = {
    "in_progress": "start",
    "waiting": "wait",
    "resolved": "resolve",
    "closed": "close",
    "open": "reopen",
}


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


def _resolve_tenant_property(db: Session, tenant_id: str, org_id: str) -> Optional[str]:
    """
    Resolve property_id from the tenant's most recent active lease.
    Falls back to any lease if no active one found.
    """
    from app.models.lease import Lease
    from app.models.unit import Unit

    lease = (
        db.query(Lease)
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Lease.tenant_id == tenant_id, Lease.status == "active")
        .first()
    )
    if not lease:
        lease = (
            db.query(Lease)
            .filter(Lease.tenant_id == tenant_id)
            .order_by(Lease.created_at.desc())
            .first()
        )
    if lease:
        unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
        return unit.property_id if unit else None
    return None


def _get_ticket(db: Session, ticket_id: str, org_id: str) -> Ticket:
    t = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.organization_id == org_id)
        .first()
    )
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


def _assert_can_manage(role, ticket, user_id, db, org_id):
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


def _assert_can_close(role):
    from fastapi import HTTPException
    if role not in {LANDLORD, PROPERTY_MANAGER}:
        raise HTTPException(status_code=403, detail="Only managers and landlords can close tickets")


def _assert_can_assign(role):
    from fastapi import HTTPException
    if role not in {LANDLORD, PROPERTY_MANAGER}:
        raise HTTPException(status_code=403, detail="Only managers and landlords can assign tickets")


def _scoped_query(db, org_id, role, user_id, tenant_id=None):
    q = db.query(Ticket).filter(Ticket.organization_id == org_id)
    if role == LANDLORD:
        pass
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


def _enrich(ticket: Ticket) -> dict:
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
        "assignee_email": ticket.assignee.email if ticket.assignee else None,
        "creator_email": ticket.creator.email if ticket.creator else None,
        "message_count": len(ticket.messages) if ticket.messages is not None else 0,
        "attachment_count": len(ticket.attachments) if ticket.attachments is not None else 0,
    }


# ─── CRUD ────────────────────────────────────────────────────────────────

def list_tickets(db, org_id, user_id, membership, *, status=None, priority=None,
                 property_id=None, category=None, tenant_id=None,
                 limit=None, offset=0):
    """
    List tickets, role-scoped.

    Pagination (Sprint 6.2 #3): when `limit` is provided, returns a dict
    { items, total, limit, offset }. When `limit` is omitted, returns the
    bare list (unchanged) so existing callers keep working.
    """
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

    q = q.order_by(Ticket.created_at.desc())

    if limit is not None:
        total = q.count()
        tickets = q.offset(offset).limit(limit).all()
        return {
            "items": [_enrich(t) for t in tickets],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    tickets = q.all()
    return [_enrich(t) for t in tickets]


def get_ticket(db, ticket_id, org_id, user_id, membership, tenant_id=None):
    from fastapi import HTTPException
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    if role == LANDLORD:
        pass
    elif role == PROPERTY_MANAGER:
        if ticket.property_id not in _pm_property_ids(db, user_id, org_id):
            raise HTTPException(status_code=403, detail="Not assigned to this property")
    elif role == FINANCE:
        if ticket.property_id not in _finance_property_ids(db, user_id, org_id):
            raise HTTPException(status_code=403, detail="Not assigned to this property")
    elif role == TENANT:
        if not tenant_id or ticket.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Not your ticket")
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return _enrich(ticket)


def create_ticket(db, org_id, user_id, membership, payload, tenant_id=None):
    from fastapi import HTTPException
    role = _role(membership)

    if role == FINANCE:
        raise HTTPException(status_code=403, detail="Finance users cannot create tickets")

    if role == PROPERTY_MANAGER:
        allowed = _pm_property_ids(db, user_id, org_id)
        if payload.property_id not in allowed:
            raise HTTPException(status_code=403, detail="Not assigned to this property")

    if payload.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Choose from: {VALID_PRIORITIES}")
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from: {VALID_CATEGORIES}")

    # Resolve property_id for tenants — they may not send one (or send "")
    property_id = payload.property_id if payload.property_id else None
    if role == TENANT:
        if not property_id and tenant_id:
            property_id = _resolve_tenant_property(db, tenant_id, org_id)
        if not property_id:
            raise HTTPException(
                status_code=400,
                detail="Could not determine your property. Please contact your landlord.",
            )

    if not property_id:
        raise HTTPException(status_code=400, detail="property_id is required")

    source_map = {
        LANDLORD:         "landlord",
        PROPERTY_MANAGER: "manager",
        FINANCE:          "finance",
        TENANT:           "tenant_portal",
    }

    ticket = Ticket(
        organization_id=org_id,
        property_id=property_id,
        unit_id=payload.unit_id or None,
        tenant_id=tenant_id if role == TENANT else getattr(payload, "tenant_id", None),
        created_by=user_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        status="open",
        source=source_map.get(role, "system"),
        source_phone=None,      # not applicable for user-created tickets
        opened_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.flush()

    log_action(db, org_id, user_id, "create", "ticket", ticket.id,
               f"Ticket created: {ticket.title}")
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def update_ticket(db, ticket_id, org_id, user_id, membership, payload):
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
        raise HTTPException(status_code=400, detail="Invalid priority")
    if "category" in updates and updates["category"] not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")

    # Sprint 7 follow-up: pass DICTS to log_action, not JSON strings. The
    # previous code did `json.dumps(old)` then log_action did another
    # `json.dumps()` around it — producing escaped-string JSON in the
    # audit table. Values are coerced to str so datetime / UUID objects
    # (if any ever appear) don't break the second json.dumps() inside
    # log_action.
    old_dict = {
        k: (str(getattr(ticket, k)) if getattr(ticket, k) is not None else None)
        for k in updates
    }
    new_dict = {k: (str(v) if v is not None else None) for k, v in updates.items()}

    for k, v in updates.items():
        setattr(ticket, k, v)

    log_action(
        db, org_id, user_id, "update", "ticket", ticket.id,
        "Ticket updated",
        old_values=old_dict, new_values=new_dict,
    )
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def delete_ticket(db, ticket_id, org_id, user_id, membership):
    from fastapi import HTTPException
    if _role(membership) != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can delete tickets")
    ticket = _get_ticket(db, ticket_id, org_id)
    log_action(db, org_id, user_id, "delete", "ticket", ticket.id, f"Ticket deleted: {ticket.title}")
    db.delete(ticket)
    db.commit()
    return {"detail": "Ticket deleted"}


# ─── Lifecycle transitions ───────────────────────────────────────────────

def assign_ticket(db, ticket_id, org_id, user_id, membership, payload):
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
    db.add(TicketAssignment(
        ticket_id=ticket.id, assigned_from=old_assignee,
        assigned_to=payload.assigned_to, reason=payload.reason,
    ))
    log_action(db, org_id, user_id, "assign", "ticket", ticket.id,
               f"Ticket assigned to {payload.assigned_to or 'nobody'}")
    db.commit()
    db.refresh(ticket)
    return _enrich(ticket)


def _transition(db, ticket_id, org_id, user_id, membership, new_status,
                allowed_from, note=None, *, extra_check=None):
    from fastapi import HTTPException
    role = _role(membership)
    ticket = _get_ticket(db, ticket_id, org_id)
    _assert_can_manage(role, ticket, user_id, db, org_id)
    if extra_check:
        extra_check(role)
    if ticket.status not in allowed_from:
        raise HTTPException(status_code=400,
                            detail=f"Cannot move to '{new_status}' from '{ticket.status}'")
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
        db.add(TicketMessage(ticket_id=ticket.id, sender_id=user_id,
                             message=note, is_internal=True))

    # Sprint 7 follow-up: distinct action verb per transition so audit
    # filters can find "all closes" or "all reopens" without parsing
    # description strings.
    action = _TRANSITION_ACTION.get(new_status, "status_change")
    log_action(db, org_id, user_id, action, "ticket", ticket.id,
               f"Ticket status: {old_status} → {new_status}")
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
                       "closed", {"resolved"}, note, extra_check=_assert_can_close)


def reopen_ticket(db, ticket_id, org_id, user_id, membership, note=None):
    from fastapi import HTTPException
    if _role(membership) != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can reopen tickets")
    return _transition(db, ticket_id, org_id, user_id, membership,
                       "open", {"resolved", "closed"}, note)