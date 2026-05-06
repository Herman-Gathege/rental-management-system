#backend\app\api\routes\leases.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.schemas.rental import LeaseCreate, LeaseUpdate

router = APIRouter(prefix="/leases", tags=["Leases"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def enrich_lease(lease, db):
    """Add tenant_name, unit_name, property_name to lease response."""
    tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
    prop = db.query(Property).filter(Property.id == unit.property_id).first() if unit else None

    return {
        "id": lease.id,
        "organization_id": lease.organization_id,
        "unit_id": lease.unit_id,
        "tenant_id": lease.tenant_id,
        "start_date": lease.start_date,
        "end_date": lease.end_date,
        "rent_amount": float(lease.rent_amount),
        "deposit_amount": float(lease.deposit_amount) if lease.deposit_amount else 0,
        "billing_day": lease.billing_day,
        "status": lease.status,
        "created_at": lease.created_at,
        "tenant_name": tenant.full_name if tenant else None,
        "unit_name": unit.name if unit else None,
        "property_name": prop.name if prop else None,
    }


# ─── Create Lease ───

@router.post("/")
def create_lease(
    payload: LeaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id

    # Verify unit belongs to this org
    unit = (
        db.query(Unit)
        .join(Property, Unit.property_id == Property.id)
        .filter(
            Unit.id == payload.unit_id,
            Property.organization_id == org_id
        )
        .first()
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Verify tenant belongs to this org
    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.id == payload.tenant_id,
            Tenant.organization_id == org_id
        )
        .first()
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check unit doesn't already have an active lease
    existing = (
        db.query(Lease)
        .filter(Lease.unit_id == payload.unit_id, Lease.status == "active")
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Unit already has an active lease")

    # Check tenant doesn't already have an active lease
    #tenant_lease = (
    #  db.query(Lease)
    #    .filter(Lease.tenant_id == payload.tenant_id, Lease.status == "active")
    #    .first()
    #)
    #if tenant_lease:
    #    raise HTTPException(status_code=400, detail="Tenant already has an active lease")

    lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        unit_id=payload.unit_id,
        tenant_id=payload.tenant_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        rent_amount=payload.rent_amount,
        deposit_amount=payload.deposit_amount or 0,
        billing_day=payload.billing_day or 1,
        status="active",
    )
    db.add(lease)
    db.commit()
    db.refresh(lease)

    return enrich_lease(lease, db)


# ─── List Leases ───

@router.get("/")
def list_leases(
    status: str = Query(None, description="Filter by status: active, ended, terminated"),
    property_id: str = Query(None, description="Filter by property"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(Lease).filter(
        Lease.organization_id == membership.organization_id
    )

    if status:
        query = query.filter(Lease.status == status)

    if property_id:
        unit_ids = (
            db.query(Unit.id)
            .filter(Unit.property_id == property_id)
            .subquery()
        )
        query = query.filter(Lease.unit_id.in_(unit_ids))

    leases = query.order_by(Lease.created_at.desc()).all()

    return [enrich_lease(l, db) for l in leases]


# ─── Get Lease ───

@router.get("/{lease_id}")
def get_lease(
    lease_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    return enrich_lease(lease, db)


# ─── Update Lease ───

@router.put("/{lease_id}")
def update_lease(
    lease_id: str,
    payload: LeaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if lease.status != "active":
        raise HTTPException(status_code=400, detail="Can only update active leases")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lease, key, value)

    db.commit()
    db.refresh(lease)

    return enrich_lease(lease, db)


# ─── Terminate Lease ───

@router.post("/{lease_id}/terminate")
def terminate_lease(
    lease_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if lease.status != "active":
        raise HTTPException(status_code=400, detail="Lease is not active")

    lease.status = "terminated"
    db.commit()

    return {
        "message": "Lease terminated",
        "lease_id": lease.id,
        "status": lease.status,
    }
