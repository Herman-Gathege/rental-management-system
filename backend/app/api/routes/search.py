# backend/app/api/routes/search.py
"""
Global search (Ctrl+K command palette).

One permission-aware endpoint that searches the entities a user is actually
allowed to see. Authorisation is applied inside each query - never by filtering
results after the fact - so an unauthorised record can never be returned, even
by a hand-crafted request.

    GET /search?q=...&property_id=...&limit=...

Scoping mirrors the rest of the platform:
  * LANDLORD         - everything in their organisation
  * FINANCE          - properties assigned via property_finance_managers
  * PROPERTY_MANAGER - properties assigned via property_managers
  * TENANT           - only their own tenant record, leases, payments, tickets
  * SYSTEM           - organisations only
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_org_membership
from app.core.roles import FINANCE, LANDLORD, PROPERTY_MANAGER, SYSTEM, TENANT
from app.db.deps import get_db
from app.models.charge import Charge
from app.models.lease import Lease
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.payment import Payment
from app.models.property import Property
from app.models.property_finance_manager import PropertyFinanceManager
from app.models.property_manager import PropertyManager
from app.models.tenant import Tenant
from app.models.ticket import Ticket
from app.models.unit import Unit
from app.models.users import User

router = APIRouter(prefix="/search", tags=["Search"])

# The palette shows a handful of hits per group; there is no reason to make the
# database scan further than that.
MAX_PER_GROUP = 5
_NO_MATCH = [""]


def _like(term: str) -> str:
    return f"%{term.strip()}%"


def _scoped_property_ids(db: Session, user, membership) -> Optional[list[str]]:
    """Property IDs the caller may search, or None for "no restriction"."""
    role = membership.role.name if membership.role else None
    org_id = membership.organization_id

    if role == LANDLORD:
        return None
    if role == PROPERTY_MANAGER:
        return [
            r[0]
            for r in db.query(PropertyManager.property_id)
            .join(Property, Property.id == PropertyManager.property_id)
            .filter(
                PropertyManager.user_id == user.id,
                Property.organization_id == org_id,
            )
            .all()
        ]
    if role == FINANCE:
        return [
            r[0]
            for r in db.query(PropertyFinanceManager.property_id)
            .join(Property, Property.id == PropertyFinanceManager.property_id)
            .filter(
                PropertyFinanceManager.user_id == user.id,
                Property.organization_id == org_id,
            )
            .all()
        ]
    return []


def _lease_ids_for_properties(
    db: Session, property_ids: Optional[list[str]]
) -> Optional[list[str]]:
    """Lease IDs inside the given properties, or None when unrestricted."""
    if property_ids is None:
        return None
    if not property_ids:
        return []
    return [
        r[0]
        for r in db.query(Lease.id)
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Unit.property_id.in_(property_ids))
        .all()
    ]


@router.get("")
def global_search(
    q: str = Query("", max_length=100),
    property_id: Optional[str] = Query(None),
    limit: int = Query(MAX_PER_GROUP, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search across searchable entities, grouped by type."""
    term = (q or "").strip()
    if len(term) < 2:
        return {"query": term, "groups": [], "total": 0}

    membership = get_user_org_membership(current_user, db)
    role = membership.role.name if membership.role else None
    org_id = membership.organization_id
    like = _like(term)
    groups: list[dict] = []
    total = 0

    def add(group_type: str, label: str, items: list[dict]) -> None:
        nonlocal total
        if items:
            groups.append({"type": group_type, "label": label, "items": items})
            total += len(items)

    # ── SYSTEM: platform operator sees organisations only ──────────────────
    if role == SYSTEM:
        orgs = (
            db.query(Organization)
            .filter(Organization.name.ilike(like))
            .limit(limit)
            .all()
        )
        add(
            "organizations",
            "Organizations",
            [
                {
                    "id": o.id,
                    "label": o.name,
                    "sublabel": "Organization",
                    "path": "/super-admin/organizations",
                }
                for o in orgs
            ],
        )
        return {"query": term, "groups": groups, "total": total}

    scoped_property_ids = _scoped_property_ids(db, current_user, membership)
    lease_ids = _lease_ids_for_properties(db, scoped_property_ids)

    # A requested property filter is additionally constrained by what the
    # caller may see: asking for a property they have no access to yields an
    # empty result rather than a peek at its data.
    if property_id:
        if scoped_property_ids is not None and property_id not in scoped_property_ids:
            return {"query": term, "groups": [], "total": 0}
        scoped_property_ids = [property_id]
        lease_ids = _lease_ids_for_properties(db, scoped_property_ids)

    is_tenant = role == TENANT
    tenant_self: Optional[Tenant] = None
    if is_tenant:
        tenant_self = (
            db.query(Tenant).filter(Tenant.user_id == current_user.id).first()
        )
    own_lease_ids = (
        [r[0] for r in db.query(Lease.id).filter(Lease.tenant_id == tenant_self.id).all()]
        if tenant_self
        else []
    )

    # ── Properties ─────────────────────────────────────────────────────────
    if not is_tenant:
        prop_q = db.query(Property).filter(
            Property.organization_id == org_id,
            or_(
                Property.name.ilike(like),
                Property.address.ilike(like),
                Property.city.ilike(like),
            ),
        )
        if scoped_property_ids is not None:
            prop_q = prop_q.filter(Property.id.in_(scoped_property_ids or _NO_MATCH))
        add(
            "properties",
            "Properties",
            [
                {
                    "id": p.id,
                    "label": p.name,
                    "sublabel": ", ".join(filter(None, [p.address, p.city])),
                    "path": (
                        f"/manager/properties"
                        if role == PROPERTY_MANAGER
                        else f"/owner/properties/{p.id}"
                    ),
                }
                for p in prop_q.limit(limit).all()
            ],
        )

    # ── Units ──────────────────────────────────────────────────────────────
    unit_q = (
        db.query(Unit)
        .join(Property, Property.id == Unit.property_id)
        .filter(Property.organization_id == org_id, Unit.name.ilike(like))
    )
    if is_tenant:
        unit_q = unit_q.filter(
            Unit.id.in_(
                [r[0] for r in db.query(Lease.unit_id).filter(Lease.id.in_(own_lease_ids or _NO_MATCH)).all()]
                or _NO_MATCH
            )
        )
    elif scoped_property_ids is not None:
        unit_q = unit_q.filter(Unit.property_id.in_(scoped_property_ids or _NO_MATCH))
    add(
        "units",
        "Units",
        [
            {
                "id": u.id,
                "label": u.name,
                "sublabel": u.property.name if u.property else None,
                "path": f"/owner/units/{u.id}",
            }
            for u in unit_q.limit(limit).all()
        ],
    )

    # ── Tenants ────────────────────────────────────────────────────────────
    if not is_tenant:
        tenant_q = db.query(Tenant).filter(
            Tenant.organization_id == org_id,
            Tenant.full_name.ilike(like),
        )
        if lease_ids is not None:
            allowed_tenant_ids = [
                r[0]
                for r in db.query(Lease.tenant_id)
                .filter(Lease.id.in_(lease_ids or _NO_MATCH))
                .all()
            ]
            tenant_q = tenant_q.filter(Tenant.id.in_(allowed_tenant_ids or _NO_MATCH))
        add(
            "tenants",
            "Tenants",
            [
                {
                    "id": t.id,
                    "label": t.full_name,
                    "sublabel": t.phone,
                    "path": (
                        "/manager/tenants"
                        if role == PROPERTY_MANAGER
                        else f"/owner/tenants/{t.id}"
                    ),
                }
                for t in tenant_q.limit(limit).all()
            ],
        )

    # ── Leases ─────────────────────────────────────────────────────────────
    # Leases have no free-text column of their own, so match against the
    # tenant name and unit name the user would actually type.
    lease_q = db.query(Lease).filter(Lease.organization_id == org_id)
    if is_tenant:
        lease_q = lease_q.filter(Lease.id.in_(own_lease_ids or _NO_MATCH))
    elif lease_ids is not None:
        lease_q = lease_q.filter(Lease.id.in_(lease_ids or _NO_MATCH))
    lease_items: list[dict] = []
    for lease in lease_q.limit(200).all():
        unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
        tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
        haystack = " ".join(
            filter(
                None,
                [
                    unit.name if unit else "",
                    tenant.full_name if tenant else "",
                    lease.status or "",
                ],
            )
        ).lower()
        if term.lower() not in haystack:
            continue
        lease_items.append(
            {
                "id": lease.id,
                "label": (
                    f"{tenant.full_name if tenant else 'Lease'} - "
                    f"{unit.name if unit else ''}"
                ).strip(" -"),
                "sublabel": f"{lease.status} - from {lease.start_date}",
                "path": (
                    "/tenant/lease"
                    if is_tenant
                    else (
                        f"/manager/leases/{lease.id}"
                        if role == PROPERTY_MANAGER
                        else f"/owner/leases/{lease.id}"
                    )
                ),
            }
        )
        if len(lease_items) >= limit:
            break
    add("leases", "Leases", lease_items)

    # ── Payments ───────────────────────────────────────────────────────────
    pay_q = db.query(Payment).filter(
        Payment.organization_id == org_id,
        or_(Payment.reference.ilike(like), Payment.payment_method.ilike(like)),
    )
    if is_tenant:
        pay_q = pay_q.filter(
            Payment.tenant_id == (tenant_self.id if tenant_self else "")
        )
    elif lease_ids is not None:
        pay_q = pay_q.filter(Payment.lease_id.in_(lease_ids or _NO_MATCH))
    add(
        "payments",
        "Payments",
        [
            {
                "id": p.id,
                "label": f"{p.amount} - {p.payment_date}",
                "sublabel": " ".join(filter(None, [p.payment_method, p.reference])),
                "path": (
                    "/tenant/payments"
                    if is_tenant
                    else (
                        "/manager/tenants"
                        if role == PROPERTY_MANAGER
                        else (
                            "/finance/payments"
                            if role == FINANCE
                            else "/owner/payments/history"
                        )
                    )
                ),
            }
            for p in pay_q.order_by(Payment.payment_date.desc()).limit(limit).all()
        ],
    )

    # ── Invoices (rent / deposit charges) ──────────────────────────────────
    charge_q = db.query(Charge).filter(
        Charge.organization_id == org_id,
        or_(Charge.status.ilike(like), Charge.charge_type.ilike(like)),
    )
    if is_tenant:
        charge_q = charge_q.filter(Charge.lease_id.in_(own_lease_ids or _NO_MATCH))
    elif lease_ids is not None:
        charge_q = charge_q.filter(Charge.lease_id.in_(lease_ids or _NO_MATCH))
    add(
        "invoices",
        "Invoices",
        [
            {
                "id": c.id,
                "label": f"{c.charge_type} {c.billing_month} - {c.amount}",
                "sublabel": f"{c.status} - due {c.due_date}",
                "path": (
                    "/tenant/charges"
                    if is_tenant
                    else (
                        "/finance/billing"
                        if role == FINANCE
                        else "/owner/billing"
                    )
                ),
            }
            for c in charge_q.order_by(Charge.due_date.desc()).limit(limit).all()
        ],
    )

    # ── Tickets ────────────────────────────────────────────────────────────
    ticket_q = db.query(Ticket).filter(
        Ticket.organization_id == org_id,
        Ticket.title.ilike(like),
    )
    if is_tenant:
        ticket_q = ticket_q.filter(
            Ticket.tenant_id == (tenant_self.id if tenant_self else "")
        )
    elif scoped_property_ids is not None:
        ticket_q = ticket_q.filter(
            Ticket.property_id.in_(scoped_property_ids or _NO_MATCH)
        )
    ticket_path_prefix = (
        "/tenant/tickets"
        if is_tenant
        else (
            "/manager/tickets"
            if role == PROPERTY_MANAGER
            else ("/finance/tickets" if role == FINANCE else "/owner/tickets")
        )
    )
    add(
        "tickets",
        "Tickets",
        [
            {
                "id": t.id,
                "label": t.title,
                "sublabel": t.status,
                "path": f"{ticket_path_prefix}/{t.id}",
            }
            for t in ticket_q.order_by(Ticket.created_at.desc()).limit(limit).all()
        ],
    )

    # ── Team (landlord only) ───────────────────────────────────────────────
    if role == LANDLORD:
        user_rows = (
            db.query(User)
            .join(OrganizationMember, OrganizationMember.user_id == User.id)
            .filter(
                OrganizationMember.organization_id == org_id,
                or_(User.full_name.ilike(like), User.email.ilike(like)),
            )
            .limit(limit)
            .all()
        )
        add(
            "users",
            "Team",
            [
                {
                    "id": u.id,
                    "label": u.full_name or u.email,
                    "sublabel": u.email,
                    "path": "/owner/team",
                }
                for u in user_rows
            ],
        )

    return {"query": term, "groups": groups, "total": total}
