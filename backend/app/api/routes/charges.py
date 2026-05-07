#backend\app\api\routes\charges.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import date, datetime

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.lease import Lease
from app.models.unit import Unit
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.charge import Charge

router = APIRouter(prefix="/charges", tags=["Charges"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def enrich_charge(charge, db):
    lease = db.query(Lease).filter(Lease.id == charge.lease_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first() if lease else None
    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first() if lease else None
    prop = db.query(Property).filter(Property.id == unit.property_id).first() if unit else None

    return {
        "id": charge.id,
        "organization_id": charge.organization_id,
        "lease_id": charge.lease_id,
        "amount": float(charge.amount),
        "due_date": charge.due_date,
        "billing_month": charge.billing_month,
        "status": charge.status,
        "created_at": charge.created_at,
        "tenant_name": tenant.full_name if tenant else None,
        "unit_name": unit.name if unit else None,
        "property_name": prop.name if prop else None,
    }


# ─── Generate Monthly Charges ───

@router.post("/generate-monthly")
def generate_monthly_charges(
    billing_date: date = Query(None, description="Date to bill for (defaults to today)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id

    if not billing_date:
        billing_date = date.today()

    billing_month = billing_date.replace(day=1)

    # Get all active leases for this org
    active_leases = (
        db.query(Lease)
        .filter(
            Lease.organization_id == org_id,
            Lease.status == "active"
        )
        .all()
    )

    created = 0
    skipped = 0

    for lease in active_leases:
        # Check if charge already exists for this month
        existing = (
            db.query(Charge)
            .filter(
                Charge.lease_id == lease.id,
                Charge.billing_month == billing_month
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        # Calculate due date using lease billing_day
        try:
            due = billing_date.replace(day=lease.billing_day)
        except ValueError:
            due = billing_date.replace(day=28)

        charge = Charge(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            lease_id=lease.id,
            amount=lease.rent_amount,
            due_date=due,
            billing_month=billing_month,
            status="pending",
        )
        db.add(charge)
        created += 1

    db.commit()

    return {
        "message": f"Billing complete: {created} charges created, {skipped} already existed",
        "created": created,
        "skipped": skipped,
    }


# ─── List Charges ───

@router.get("/")
def list_charges(
    status: str = Query(None, description="Filter: pending, paid, overdue"),
    lease_id: str = Query(None),
    property_id: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(Charge).filter(
        Charge.organization_id == membership.organization_id
    )

    if status:
        query = query.filter(Charge.status == status)

    if lease_id:
        query = query.filter(Charge.lease_id == lease_id)

    if property_id:
        lease_ids = (
            db.query(Lease.id)
            .join(Unit, Lease.unit_id == Unit.id)
            .filter(Unit.property_id == property_id)
            .subquery()
        )
        query = query.filter(Charge.lease_id.in_(lease_ids))

    charges = query.order_by(Charge.due_date.desc()).all()

    # Auto-mark overdue
    today = date.today()
    for c in charges:
        if c.status == "pending" and c.due_date < today:
            c.status = "overdue"
    db.commit()

    return [enrich_charge(c, db) for c in charges]


# ─── Get Single Charge ───

@router.get("/{charge_id}")
def get_charge(
    charge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    charge = (
        db.query(Charge)
        .filter(
            Charge.id == charge_id,
            Charge.organization_id == membership.organization_id
        )
        .first()
    )

    if not charge:
        raise HTTPException(status_code=404, detail="Charge not found")

    return enrich_charge(charge, db)
