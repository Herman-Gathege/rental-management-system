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

    balance = float(total_charges) - float(total_payments)

    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.full_name,
        "total_charges": float(total_charges),
        "total_payments": float(total_payments),
        "balance": balance,
    }


# ─── Dashboard Financial Summary ───

@router.get("/dashboard-summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id

    # Total expected rent (sum of all active lease rent amounts)
    total_expected = (
        db.query(func.coalesce(func.sum(Lease.rent_amount), 0))
        .filter(Lease.organization_id == org_id, Lease.status == "active")
        .scalar()
    )

    # Total collected (all payments)
    total_collected = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.organization_id == org_id)
        .scalar()
    )

    # Total overdue
    total_overdue = (
        db.query(func.coalesce(func.sum(Charge.amount), 0))
        .filter(
            Charge.organization_id == org_id,
            Charge.status.in_(["overdue", "pending"])
        )
        .scalar()
    )

    # Occupancy
    total_units = (
        db.query(func.count(Unit.id))
        .join(Property, Unit.property_id == Property.id)
        .filter(Property.organization_id == org_id, Unit.is_active == True)
        .scalar()
    )

    occupied_units = (
        db.query(func.count(func.distinct(Lease.unit_id)))
        .filter(Lease.organization_id == org_id, Lease.status == "active")
        .scalar()
    )

    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

    return {
        "total_expected_rent": float(total_expected),
        "total_collected": float(total_collected),
        "total_overdue": float(total_overdue),
        "occupancy_rate": round(occupancy_rate, 1),
        "total_units": total_units,
        "occupied_units": occupied_units,
    }
