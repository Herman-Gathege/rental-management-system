# backend/app/services/dashboard_service.py
"""
Dashboard query layer (Sprint 4.5).

One function per dashboard section. Routes handle authz (which role may call
what) and hand us the resolved user_id + organization_id; we do the data work
and return plain dicts. Keeping queries here (not in the routes) means they can
be unit-tested without FastAPI and reused later (e.g. a future landlord
overview that rolls up manager summaries).

Scoping rules enforced here:
  - Manager: only properties assigned to them in property_managers, and only
    within their own organization.
  - Finance: organization-wide financial records.
  - Tenant: only the tenant row linked to their user account (tenants.user_id),
    and that tenant's own leases / charges / payments.

Occupancy note: a Unit has no "occupied" flag. A unit is occupied iff it has an
active lease -- the same definition finance.py already uses -- so we derive it
from leases rather than storing redundant state.
"""
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


# ─────────────────────────────────────────────────────────────────────
# Property Manager
# ─────────────────────────────────────────────────────────────────────

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

    # No assignments yet -> all zeros. This is a valid empty state, not an error.
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

    # A unit is "occupied" if it has an active lease.
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

    # Distinct tenants currently housed in the assigned properties.
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


# ─────────────────────────────────────────────────────────────────────
# Finance
# ─────────────────────────────────────────────────────────────────────

def get_finance_summary(db: Session, org_id: str) -> dict:
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
    overdue_charges = (
        db.query(func.count(Charge.id))
        .filter(Charge.organization_id == org_id, Charge.status == "overdue")
        .scalar()
    ) or 0

    # Outstanding = everything ever billed minus everything ever paid
    # (cumulative-settlement model). Floored at 0 so an overpaid org never
    # shows a negative "owed" figure on the dashboard.
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


# ─────────────────────────────────────────────────────────────────────
# Tenant
# ─────────────────────────────────────────────────────────────────────

def _resolve_tenant(db: Session, user_id: str, org_id: str) -> Tenant:
    """
    Find the tenant row linked to this login. Relies on tenants.user_id (added
    in migration b7f3c1e9a4d2). If it's missing, the account was never linked to
    a tenant record -- surface a clear 404 rather than a confusing empty
    dashboard.
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

    # Prefer the active lease; fall back to the most recent one of any status.
    lease = (
        db.query(Lease)
        .filter(Lease.tenant_id == tenant.id, Lease.status == "active")
        .order_by(Lease.start_date.desc())
        .first()
    )
    if not lease:
        lease = (
            db.query(Lease)
            .filter(Lease.tenant_id == tenant.id)
            .order_by(Lease.start_date.desc())
            .first()
        )

    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first() if lease else None

    # Balance = all charges across this tenant's leases minus all their payments.
    lease_ids = _tenant_lease_ids(db, tenant.id)
    total_charges = 0.0
    if lease_ids:
        total_charges = float(
            db.query(func.coalesce(func.sum(Charge.amount), 0))
            .filter(Charge.lease_id.in_(lease_ids))
            .scalar()
        )
    total_payments = float(
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.tenant_id == tenant.id)
        .scalar()
    )
    balance = total_charges - total_payments

    return {
        "tenant": {
            "id": tenant.id,
            "full_name": tenant.full_name,
            "email": tenant.email,
            "phone": tenant.phone,
        },
        "unit": (
            {
                "id": unit.id,
                "name": unit.name,
                "rent_amount": float(unit.rent_amount) if unit.rent_amount is not None else None,
            }
            if unit else None
        ),
        "lease": (
            {
                "id": lease.id,
                "status": lease.status,
                "start_date": lease.start_date.isoformat() if lease.start_date else None,
                "end_date": lease.end_date.isoformat() if lease.end_date else None,
                "rent_amount": float(lease.rent_amount) if lease.rent_amount is not None else None,
            }
            if lease else None
        ),
        "balance": balance,
    }


def get_tenant_payments(db: Session, user_id: str, org_id: str) -> list:
    tenant = _resolve_tenant(db, user_id, org_id)
    payments = (
        db.query(Payment)
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
        }
        for p in payments
    ]


def get_tenant_charges(db: Session, user_id: str, org_id: str) -> list:
    tenant = _resolve_tenant(db, user_id, org_id)
    lease_ids = _tenant_lease_ids(db, tenant.id)
    if not lease_ids:
        return []
    charges = (
        db.query(Charge)
        .filter(Charge.lease_id.in_(lease_ids))
        .order_by(Charge.billing_month.desc())
        .all()
    )
    return [
        {
            "month": c.billing_month.isoformat() if c.billing_month else None,
            "amount": float(c.amount),
            "status": c.status,
            "due_date": c.due_date.isoformat() if c.due_date else None,
        }
        for c in charges
    ]