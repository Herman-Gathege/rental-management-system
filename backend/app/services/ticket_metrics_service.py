#backend\app\services\ticket_metrics_service.py
"""
Ticket metrics service — Sprint 6, Chunk 7 (dashboard metrics).

Computes the metrics the guide specifies for dashboards:
  - Open vs Closed counts
  - Critical / high open issues
  - Average resolution time (opened_at → resolved_at)
  - Tickets by status
  - Tickets by category
  - Top properties by ticket volume

All metrics are role-scoped using the same visibility rules as the ticket
list: Landlord sees org-wide; PM/Finance see their assigned properties;
Tenant sees only their own tickets.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT
from app.models.ticket import Ticket
from app.models.organization_member import OrganizationMember
from app.models.property_manager import PropertyManager
from app.models.property_finance_manager import PropertyFinanceManager

OPEN_STATUSES = {"open", "assigned", "in_progress", "waiting"}


def _role(membership: OrganizationMember) -> str:
    return membership.role.name


def _scoped_tickets(db, org_id, role, user_id, tenant_id=None):
    q = db.query(Ticket).filter(Ticket.organization_id == org_id)
    if role == LANDLORD:
        pass
    elif role == PROPERTY_MANAGER:
        allowed = [r.property_id for r in
                   db.query(PropertyManager).filter(PropertyManager.user_id == user_id).all()]
        q = q.filter(Ticket.property_id.in_(allowed or ["__none__"]))
    elif role == FINANCE:
        allowed = [r.property_id for r in
                   db.query(PropertyFinanceManager).filter(PropertyFinanceManager.user_id == user_id).all()]
        q = q.filter(Ticket.property_id.in_(allowed or ["__none__"]))
    elif role == TENANT:
        if not tenant_id:
            return []
        q = q.filter(Ticket.tenant_id == tenant_id)
    else:
        return []
    return q.all()


def get_metrics(db: Session, org_id: str, user_id: str,
                membership: OrganizationMember, tenant_id: Optional[str] = None) -> dict:
    role = _role(membership)
    tickets = _scoped_tickets(db, org_id, role, user_id, tenant_id=tenant_id)

    total = len(tickets)
    open_count = sum(1 for t in tickets if t.status in OPEN_STATUSES)
    closed_count = sum(1 for t in tickets if t.status == "closed")
    resolved_count = sum(1 for t in tickets if t.status == "resolved")
    critical_open = sum(1 for t in tickets
                        if t.status in OPEN_STATUSES and t.priority in ("high", "critical"))

    # By status
    by_status: dict[str, int] = {}
    for t in tickets:
        by_status[t.status] = by_status.get(t.status, 0) + 1

    # By category
    by_category: dict[str, int] = {}
    for t in tickets:
        cat = t.category or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1

    # Average resolution time (hours) — tickets with both opened_at + resolved_at
    durations = []
    for t in tickets:
        if t.opened_at and t.resolved_at:
            delta = (t.resolved_at - t.opened_at).total_seconds() / 3600.0
            if delta >= 0:
                durations.append(delta)
    avg_resolution_hours = round(sum(durations) / len(durations), 1) if durations else None

    # Top properties by ticket volume (count per property_id)
    prop_counts: dict[str, int] = {}
    for t in tickets:
        if t.property_id:
            prop_counts[t.property_id] = prop_counts.get(t.property_id, 0) + 1

    # Resolve property names
    from app.models.property import Property
    top_properties = []
    if prop_counts:
        prop_ids = list(prop_counts.keys())
        props = db.query(Property).filter(Property.id.in_(prop_ids)).all()
        name_map = {p.id: p.name for p in props}
        top_properties = sorted(
            [{"property_id": pid, "property_name": name_map.get(pid, "Unknown"), "count": c}
             for pid, c in prop_counts.items()],
            key=lambda x: x["count"], reverse=True,
        )[:5]

    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "resolved": resolved_count,
        "critical_open": critical_open,
        "avg_resolution_hours": avg_resolution_hours,
        "by_status": by_status,
        "by_category": by_category,
        "top_properties": top_properties,
    }
