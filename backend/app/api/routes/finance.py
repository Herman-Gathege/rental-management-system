#backend\app\api\routes\finance.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.unit import Unit
from app.models.property import Property
from app.models.charge import Charge
from app.models.payment import Payment
from app.core.roles import FINANCE
from app.services.finance_scope import assigned_finance_property_ids, lease_ids_for_properties

router = APIRouter(prefix="/finance", tags=["Finance"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


# ─── Tenant Balance ───

@router.get("/tenant-balance/{tenant_id}")
def get_tenant_balance(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id

    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == tenant_id, Tenant.organization_id == org_id)
        .first()
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get all lease IDs for this tenant
    lease_ids = (
        db.query(Lease.id)
        .filter(Lease.tenant_id == tenant_id, Lease.organization_id == org_id)
        .all()
    )
    lease_id_list = [lid[0] for lid in lease_ids]

    if not lease_id_list:
        return {
            "tenant_id": tenant.id,
            "tenant_name": tenant.full_name,
            "total_charges": 0,
            "total_payments": 0,
            "balance": 0,
            "amount_owed": 0,
            "credit": 0,
        }

    # Sum charges
    total_charges = (
        db.query(func.coalesce(func.sum(Charge.amount), 0))
        .filter(Charge.lease_id.in_(lease_id_list))
        .scalar()
    )

    # Sum payments
    total_payments = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.lease_id.in_(lease_id_list))
        .scalar()
    )

    # Signed balance: positive = tenant owes money, negative = tenant is in
    # credit (overpaid). Rounded to cents so float subtraction doesn't leak
    # noise like -4999.9999999. The two derived fields below let the frontend
    # render owed/credit without doing any sign math itself.
    balance = round(float(total_charges) - float(total_payments), 2)
    amount_owed = balance if balance > 0 else 0.0
    credit = -balance if balance < 0 else 0.0

    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.full_name,
        "total_charges": float(total_charges),
        "total_payments": float(total_payments),
        "balance": balance,          # signed (owes > 0, credit < 0)
        "amount_owed": amount_owed,  # max(0, balance)
        "credit": credit,            # max(0, -balance)
    }


# ─── Dashboard Financial Summary ───

@router.get("/dashboard-summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id
    role = membership.role.name if membership.role else None

    # Finance scoping: restrict every figure to the finance user's assigned
    # properties. None => org-wide (landlord). Empty list => sees nothing.
    scoped_lease_ids = None
    scoped_property_ids = None
    if role == FINANCE:
        scoped_property_ids = assigned_finance_property_ids(db, current_user.id, org_id)
        scoped_lease_ids = lease_ids_for_properties(db, scoped_property_ids)
        if not scoped_lease_ids:
            return {
                "total_expected_rent": 0.0,
                "total_collected": 0.0,
                "total_overdue": 0.0,
                "occupancy_rate": 0.0,
                "total_units": 0,
                "occupied_units": 0,
            }

    # Total expected rent (sum of all active lease rent amounts)
    expected_q = (
        db.query(func.coalesce(func.sum(Lease.rent_amount), 0))
        .filter(Lease.organization_id == org_id, Lease.status == "active")
    )
    # Total collected — RENT payments only (Sprint 6.2 #7: deposits are tracked
    # separately and must not inflate rent-collection figures).
    collected_q = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.organization_id == org_id, Payment.payment_type == "rent")
    )
    # Total overdue — RENT charges only, pending/overdue status.
    overdue_q = (
        db.query(func.coalesce(func.sum(Charge.amount), 0))
        .filter(
            Charge.organization_id == org_id,
            Charge.charge_type == "rent",
            Charge.status.in_(["overdue", "pending"])
        )
    )
    # Occupancy
    units_q = (
        db.query(func.count(Unit.id))
        .join(Property, Unit.property_id == Property.id)
        .filter(Property.organization_id == org_id, Unit.is_active == True)  # noqa: E712
    )
    occupied_q = (
        db.query(func.count(func.distinct(Lease.unit_id)))
        .filter(Lease.organization_id == org_id, Lease.status == "active")
    )

    if scoped_lease_ids is not None:
        expected_q = expected_q.filter(Lease.id.in_(scoped_lease_ids))
        collected_q = collected_q.filter(Payment.lease_id.in_(scoped_lease_ids))
        overdue_q = overdue_q.filter(Charge.lease_id.in_(scoped_lease_ids))
        units_q = units_q.filter(Unit.property_id.in_(scoped_property_ids))
        occupied_q = occupied_q.filter(Lease.id.in_(scoped_lease_ids))

    total_expected = expected_q.scalar()
    total_collected = collected_q.scalar()
    total_overdue = overdue_q.scalar()
    total_units = units_q.scalar() or 0
    occupied_units = occupied_q.scalar() or 0

    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

    return {
        "total_expected_rent": float(total_expected),
        "total_collected": float(total_collected),
        "total_overdue": float(total_overdue),
        "occupancy_rate": round(occupancy_rate, 1),
        "total_units": total_units,
        "occupied_units": occupied_units,
    }