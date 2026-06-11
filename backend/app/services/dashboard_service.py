# backend/app/services/dashboard_service.py
"""
Dashboard query layer (Sprint 4.5).

One function per dashboard section. Routes handle authz (which role may call
what) and hand us the resolved user_id + organization_id; we do the data work
and return plain dicts.

Scoping rules enforced here:
  - Manager: only properties assigned to them in property_managers, and only
    within their own organization. Units / tenants / leases are all derived
    from those assigned properties.
  - Finance: organization-wide financial records.
  - Tenant: only the tenant row linked to their user account (tenants.user_id),
    and that tenant's own leases / charges / payments.

Occupancy note: a Unit has no "occupied" flag. A unit is occupied iff it has an
active lease -- the same definition finance.py already uses.

Overdue note (Sprint 4.5 partial-payment fix, Option A): "overdue" means a
charge that is past its due date and still has a balance (amount_paid < amount).
This matches the Billing page's Overdue tab and catches partially-paid-but-late
charges too.

Tenant rows (charges / payments) carry property_id + property_name + unit_name
+ lease_id so the tenant portal can group / filter by property (multi-lease
tenants rent across more than one property).
"""
import json
from datetime import date
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_manager import PropertyManager
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.lease_inspection import LeaseInspection
from app.models.inspection_item import InspectionItem


# ---------------------------------------------------------------------
# Property Manager
# ---------------------------------------------------------------------

def _assigned_property_ids(db: Session, user_id: str, org_id: str) -> list:
    """Property IDs assigned to this manager, scoped to their organization."""
    rows = (
        db.query(PropertyManager.property_id)
        .join(Property, Property.id == PropertyManager.property_id)
        .filter(
            PropertyManager.user_id == user_id,
            Property.organization_id == org_id,
        )
        .all()
    )
    return [r[0] for r in rows]


def get_manager_summary(db: Session, user_id: str, org_id: str) -> dict:
    property_ids = _assigned_property_ids(db, user_id, org_id)

    if not property_ids:
        return {
            "properties": 0, "units": 0, "occupied_units": 0,
            "vacant_units": 0, "tenants": 0, "active_leases": 0,
        }

    units = (
        db.query(func.count(Unit.id))
        .filter(Unit.property_id.in_(property_ids), Unit.is_active == True)  # noqa: E712
        .scalar()
    ) or 0

    occupied_units = (
        db.query(func.count(func.distinct(Lease.unit_id)))
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Unit.property_id.in_(property_ids), Lease.status == "active")
        .scalar()
    ) or 0

    active_leases = (
        db.query(func.count(Lease.id))
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Unit.property_id.in_(property_ids), Lease.status == "active")
        .scalar()
    ) or 0

    tenants = (
        db.query(func.count(func.distinct(Lease.tenant_id)))
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Unit.property_id.in_(property_ids), Lease.status == "active")
        .scalar()
    ) or 0

    return {
        "properties": len(property_ids),
        "units": units,
        "occupied_units": occupied_units,
        "vacant_units": max(units - occupied_units, 0),
        "tenants": tenants,
        "active_leases": active_leases,
    }


def get_manager_properties(db: Session, user_id: str, org_id: str) -> list:
    property_ids = _assigned_property_ids(db, user_id, org_id)
    if not property_ids:
        return []
    props = (
        db.query(Property)
        .filter(Property.id.in_(property_ids))
        .order_by(Property.name.asc())
        .all()
    )
    return [
        {"id": p.id, "name": p.name, "address": p.address, "city": p.city}
        for p in props
    ]


def get_manager_units(db: Session, user_id: str, org_id: str) -> list:
    """Units in the manager's assigned properties, with occupancy + tenant."""
    property_ids = _assigned_property_ids(db, user_id, org_id)
    if not property_ids:
        return []

    rows = (
        db.query(Unit, Property.name)
        .join(Property, Property.id == Unit.property_id)
        .filter(Unit.property_id.in_(property_ids), Unit.is_active == True)  # noqa: E712
        .order_by(Property.name.asc(), Unit.name.asc())
        .all()
    )

    # Active lease per unit -> occupancy + current tenant.
    unit_ids = [u.id for u, _pname in rows]
    active_by_unit: dict = {}
    if unit_ids:
        lease_rows = (
            db.query(Lease, Tenant.full_name)
            .outerjoin(Tenant, Tenant.id == Lease.tenant_id)
            .filter(Lease.unit_id.in_(unit_ids), Lease.status == "active")
            .all()
        )
        for lease, tenant_name in lease_rows:
            active_by_unit[lease.unit_id] = tenant_name

    result = []
    for u, pname in rows:
        tenant_name = active_by_unit.get(u.id)
        result.append({
            "id": u.id,
            "name": u.name,
            "property_name": pname,
            "rent_amount": float(u.rent_amount) if u.rent_amount is not None else None,
            "status": "occupied" if u.id in active_by_unit else "vacant",
            "tenant_name": tenant_name,
        })
    return result


def get_manager_tenants(db: Session, user_id: str, org_id: str) -> list:
    """Active tenancies in the manager's assigned properties (one row per
    active lease, so a tenant renting in two assigned properties shows twice,
    each with the relevant property/unit)."""
    property_ids = _assigned_property_ids(db, user_id, org_id)
    if not property_ids:
        return []

    rows = (
        db.query(Tenant, Property.name, Unit.name)
        .join(Lease, Lease.tenant_id == Tenant.id)
        .join(Unit, Unit.id == Lease.unit_id)
        .join(Property, Property.id == Unit.property_id)
        .filter(Unit.property_id.in_(property_ids), Lease.status == "active")
        .order_by(Tenant.full_name.asc())
        .all()
    )
    return [
        {
            "id": t.id,
            "full_name": t.full_name,
            "phone": t.phone,
            "email": t.email,
            "property_name": pname,
            "unit_name": uname,
        }
        for t, pname, uname in rows
    ]


def get_manager_leases(db: Session, user_id: str, org_id: str) -> list:
    """All leases (any status) in the manager's assigned properties."""
    property_ids = _assigned_property_ids(db, user_id, org_id)
    if not property_ids:
        return []

    rows = (
        db.query(Lease, Tenant.full_name, Property.name, Unit.name)
        .outerjoin(Tenant, Tenant.id == Lease.tenant_id)
        .join(Unit, Unit.id == Lease.unit_id)
        .join(Property, Property.id == Unit.property_id)
        .filter(Unit.property_id.in_(property_ids))
        .order_by(Lease.start_date.desc())
        .all()
    )
    return [
        {
            "id": l.id,
            "tenant_name": tname,
            "property_name": pname,
            "unit_name": uname,
            "status": l.status,
            "start_date": l.start_date.isoformat() if l.start_date else None,
            "end_date": l.end_date.isoformat() if l.end_date else None,
            "rent_amount": float(l.rent_amount) if l.rent_amount is not None else None,
        }
        for l, tname, pname, uname in rows
    ]


# ---------------------------------------------------------------------
# Finance
# ---------------------------------------------------------------------

def get_finance_summary(db: Session, org_id: str) -> dict:
    today = date.today()

    expected_rent = (
        db.query(func.coalesce(func.sum(Lease.rent_amount), 0))
        .filter(Lease.organization_id == org_id, Lease.status == "active")
        .scalar()
    )
    total_collected = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.organization_id == org_id)
        .scalar()
    )
    total_charged = (
        db.query(func.coalesce(func.sum(Charge.amount), 0))
        .filter(Charge.organization_id == org_id)
        .scalar()
    )

    # Overdue (Option A): past due AND still owing a balance. Counts
    # partially-paid-but-late charges, matching the Billing Overdue tab.
    overdue_charges = (
        db.query(func.count(Charge.id))
        .filter(
            Charge.organization_id == org_id,
            Charge.due_date < today,
            Charge.amount_paid < Charge.amount,
        )
        .scalar()
    ) or 0

    outstanding_balance = max(float(total_charged) - float(total_collected), 0.0)

    return {
        "total_collected": float(total_collected),
        "expected_rent": float(expected_rent),
        "outstanding_balance": outstanding_balance,
        "overdue_charges": overdue_charges,
    }


def get_finance_recent_payments(db: Session, org_id: str, limit: int = 10) -> list:
    rows = (
        db.query(Payment, Tenant.full_name)
        .join(Tenant, Tenant.id == Payment.tenant_id)
        .filter(Payment.organization_id == org_id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "tenant_name": full_name,
            "amount": float(p.amount),
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "method": p.payment_method,
            "reference": p.reference,
        }
        for p, full_name in rows
    ]


# ---------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------

def _resolve_tenant(db: Session, user_id: str, org_id: str) -> Tenant:
    """
    Find the tenant row linked to this login (tenants.user_id, added in
    migration b7f3c1e9a4d2). 404 if the account was never linked.
    """
    tenant = (
        db.query(Tenant)
        .filter(Tenant.user_id == user_id, Tenant.organization_id == org_id)
        .first()
    )
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="No tenant record is linked to this account.",
        )
    return tenant


def _tenant_lease_ids(db: Session, tenant_id: str) -> list:
    return [r[0] for r in db.query(Lease.id).filter(Lease.tenant_id == tenant_id).all()]


def get_tenant_dashboard(db: Session, user_id: str, org_id: str) -> dict:
    tenant = _resolve_tenant(db, user_id, org_id)

    # All of this tenant's leases, each joined to its unit + property so the
    # portal can show "Property · Unit" per lease. Multi-lease is supported:
    # a tenant may hold leases across several properties.
    rows = (
        db.query(Lease, Unit, Property)
        .outerjoin(Unit, Unit.id == Lease.unit_id)
        .outerjoin(Property, Property.id == Unit.property_id)
        .filter(Lease.tenant_id == tenant.id)
        .all()
    )

    # Order: active leases first, newest start date first within each group.
    def _rank(row):
        lease = row[0]
        active_first = 0 if lease.status == "active" else 1
        start_ord = lease.start_date.toordinal() if lease.start_date else 0
        return (active_first, -start_ord)

    rows = sorted(rows, key=_rank)

    lease_ids = [lease.id for lease, _unit, _prop in rows]

    # Per-lease sums in two grouped queries (no N+1). Each lease shows its own
    # balance, and the aggregate is simply the sum of the parts.
    charge_sums: dict = {}
    payment_sums: dict = {}
    if lease_ids:
        charge_sums = {
            lid: float(total)
            for lid, total in (
                db.query(Charge.lease_id, func.coalesce(func.sum(Charge.amount), 0))
                .filter(Charge.lease_id.in_(lease_ids))
                .group_by(Charge.lease_id)
                .all()
            )
        }
        payment_sums = {
            lid: float(total)
            for lid, total in (
                db.query(Payment.lease_id, func.coalesce(func.sum(Payment.amount), 0))
                .filter(Payment.lease_id.in_(lease_ids))
                .group_by(Payment.lease_id)
                .all()
            )
        }

    leases = []
    for lease, unit, prop in rows:
        l_charges = charge_sums.get(lease.id, 0.0)
        l_payments = payment_sums.get(lease.id, 0.0)
        l_balance = round(l_charges - l_payments, 2)
        leases.append({
            "id": lease.id,
            "status": lease.status,
            "start_date": lease.start_date.isoformat() if lease.start_date else None,
            "end_date": lease.end_date.isoformat() if lease.end_date else None,
            "rent_amount": float(lease.rent_amount) if lease.rent_amount is not None else None,
            "property_id": prop.id if prop else None,
            "property_name": prop.name if prop else None,
            "unit_name": unit.name if unit else None,
            "balance": l_balance,
            "amount_owed": l_balance if l_balance > 0 else 0.0,
            "credit": -l_balance if l_balance < 0 else 0.0,
        })

    # Aggregate account standing across every lease (the top-line figure).
    total_charges = round(sum(charge_sums.values()), 2)
    total_payments = round(sum(payment_sums.values()), 2)
    balance = round(total_charges - total_payments, 2)
    amount_owed = balance if balance > 0 else 0.0
    credit = -balance if balance < 0 else 0.0

    # Primary lease/unit = first after sorting (newest active). Kept as scalar
    # fields for backward compatibility with the existing Dashboard page.
    primary_lease, primary_unit, _primary_prop = rows[0] if rows else (None, None, None)

    return {
        "tenant": {
            "id": tenant.id,
            "full_name": tenant.full_name,
            "email": tenant.email,
            "phone": tenant.phone,
        },
        "unit": (
            {
                "id": primary_unit.id,
                "name": primary_unit.name,
                "rent_amount": float(primary_unit.rent_amount) if primary_unit.rent_amount is not None else None,
            }
            if primary_unit else None
        ),
        "lease": (
            {
                "id": primary_lease.id,
                "status": primary_lease.status,
                "start_date": primary_lease.start_date.isoformat() if primary_lease.start_date else None,
                "end_date": primary_lease.end_date.isoformat() if primary_lease.end_date else None,
                "rent_amount": float(primary_lease.rent_amount) if primary_lease.rent_amount is not None else None,
            }
            if primary_lease else None
        ),
        "balance": balance,
        "amount_owed": amount_owed,
        "credit": credit,
        "leases": leases,
    }


def get_tenant_payments(db: Session, user_id: str, org_id: str) -> list:
    tenant = _resolve_tenant(db, user_id, org_id)
    rows = (
        db.query(Payment, Property.id, Property.name, Unit.name)
        .join(Lease, Lease.id == Payment.lease_id)
        .outerjoin(Unit, Unit.id == Lease.unit_id)
        .outerjoin(Property, Property.id == Unit.property_id)
        .filter(Payment.tenant_id == tenant.id)
        .order_by(Payment.payment_date.desc())
        .all()
    )
    return [
        {
            "date": p.payment_date.isoformat() if p.payment_date else None,
            "reference": p.reference,
            "amount": float(p.amount),
            "method": p.payment_method,
            "lease_id": p.lease_id,
            "property_id": pid,
            "property_name": pname,
            "unit_name": uname,
        }
        for p, pid, pname, uname in rows
    ]


def get_tenant_charges(db: Session, user_id: str, org_id: str) -> list:
    tenant = _resolve_tenant(db, user_id, org_id)
    lease_ids = _tenant_lease_ids(db, tenant.id)
    if not lease_ids:
        return []
    rows = (
        db.query(Charge, Property.id, Property.name, Unit.name)
        .join(Lease, Lease.id == Charge.lease_id)
        .outerjoin(Unit, Unit.id == Lease.unit_id)
        .outerjoin(Property, Property.id == Unit.property_id)
        .filter(Charge.lease_id.in_(lease_ids))
        .order_by(Charge.billing_month.desc())
        .all()
    )
    return [
        {
            "month": c.billing_month.isoformat() if c.billing_month else None,
            "amount": float(c.amount),
            "amount_paid": float(c.amount_paid or 0),
            "balance": float(c.amount) - float(c.amount_paid or 0),
            "status": c.status,
            "due_date": c.due_date.isoformat() if c.due_date else None,
            "lease_id": c.lease_id,
            "property_id": pid,
            "property_name": pname,
            "unit_name": uname,
        }
        for c, pid, pname, uname in rows
    ]


def _parse_photo_urls(raw):
    """Inspection photo URLs are stored as a JSON string array."""
    try:
        return json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_tenant_inspections(db: Session, user_id: str, org_id: str) -> list:
    """Read-only move-in / move-out inspection records for the tenant's own
    leases (multi-lease aware). Excludes internal notes and inspector identity:
    the tenant sees the checklist items, conditions, comments, photos, and (for
    move-out) any deposit deductions."""
    tenant = _resolve_tenant(db, user_id, org_id)
    lease_ids = _tenant_lease_ids(db, tenant.id)
    if not lease_ids:
        return []

    rows = (
        db.query(LeaseInspection, Unit, Property)
        .join(Lease, Lease.id == LeaseInspection.lease_id)
        .outerjoin(Unit, Unit.id == Lease.unit_id)
        .outerjoin(Property, Property.id == Unit.property_id)
        .filter(LeaseInspection.lease_id.in_(lease_ids))
        .order_by(LeaseInspection.created_at.desc())
        .all()
    )

    result = []
    for insp, unit, prop in rows:
        items = (
            db.query(InspectionItem)
            .filter(InspectionItem.inspection_id == insp.id)
            .order_by(InspectionItem.sort_order.asc())
            .all()
        )
        result.append({
            "id": insp.id,
            "lease_id": insp.lease_id,
            "inspection_type": insp.inspection_type,
            "inspection_date": insp.inspection_date.isoformat() if insp.inspection_date else None,
            "status": insp.status,
            "property_id": prop.id if prop else None,
            "property_name": prop.name if prop else None,
            "unit_name": unit.name if unit else None,
            "tenant_signed_name": insp.tenant_signed_name,
            "tenant_signed_at": insp.tenant_signed_at.isoformat() if insp.tenant_signed_at else None,
            "total_deduction_amount": float(insp.total_deduction_amount) if insp.total_deduction_amount else 0,
            "items": [
                {
                    "id": it.id,
                    "item_name": it.item_name,
                    "condition": it.condition,
                    "comments": it.comments,
                    "photo_urls": _parse_photo_urls(it.photo_urls),
                    "deduction_amount": float(it.deduction_amount) if it.deduction_amount else 0,
                }
                for it in items
            ],
        })
    return result
