# backend/app/services/dashboard_service.py
"""
Dashboard query layer (Sprint 4.5).

One function per dashboard section. Routes handle authz (which role may call
what) and hand us the resolved user_id + organization_id; we do the data work
and return plain dicts.

Scoping rules enforced here:
  - Manager: only properties assigned to them in property_managers, and only
    within their own organization.
  - Finance: organization-wide financial records.
  - Tenant: only the tenant row linked to their user account (tenants.user_id),
    and that tenant's own leases / charges / payments.

Occupancy note: a Unit has no "occupied" flag. A unit is occupied iff it has an
active lease -- the same definition finance.py already uses.

Overdue note (Sprint 4.5 partial-payment fix, Option A): "overdue" means a
charge that is past its due date and still has a balance (amount_paid < amount).
This matches the Billing page's Overdue tab and catches partially-paid-but-late
charges too.
"""
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
            "amount_paid": float(c.amount_paid or 0),
            "balance": float(c.amount) - float(c.amount_paid or 0),
            "status": c.status,
            "due_date": c.due_date.isoformat() if c.due_date else None,
        }
        for c in charges
    ]
