#backend\app\api\routes\units.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.tenant import Tenant
from app.schemas.rental import UnitCreate, UnitUpdate
from app.core.roles import LANDLORD

router = APIRouter(prefix="/units", tags=["Units"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


# ─── Create Unit ───

@router.post("/")
def create_unit(
    payload: UnitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    # Verify property belongs to this org
    prop = (
        db.query(Property)
        .filter(
            Property.id == payload.property_id,
            Property.organization_id == membership.organization_id
        )
        .first()
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    unit = Unit(
        id=str(uuid.uuid4()),
        property_id=payload.property_id,
        name=payload.name,
        description=payload.description,
        bedrooms=payload.bedrooms,
        bathrooms=payload.bathrooms,
        size_sqm=payload.size_sqm,
        rent_amount=payload.rent_amount,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    return {
        "id": unit.id,
        "property_id": unit.property_id,
        "name": unit.name,
        "description": unit.description,
        "bedrooms": unit.bedrooms,
        "bathrooms": unit.bathrooms,
        "size_sqm": unit.size_sqm,
        "rent_amount": float(unit.rent_amount),
        "is_active": unit.is_active,
        "created_at": unit.created_at,
        "occupancy_status": "vacant",
        "tenant_name": None,
    }


# ─── List Units ───

@router.get("/")
def list_units(
    property_id: str = Query(None, description="Filter by property"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = (
        db.query(Unit)
        .join(Property, Unit.property_id == Property.id)
        .filter(Property.organization_id == membership.organization_id)
    )

    if property_id:
        query = query.filter(Unit.property_id == property_id)

    units = query.all()

    result = []
    for u in units:
        # Check if unit has an active lease
        active_lease = (
            db.query(Lease)
            .filter(Lease.unit_id == u.id, Lease.status == "active")
            .first()
        )

        tenant_name = None
        occupancy = "vacant"
        if active_lease:
            occupancy = "occupied"
            tenant = db.query(Tenant).filter(Tenant.id == active_lease.tenant_id).first()
            if tenant:
                tenant_name = tenant.full_name

        result.append({
            "id": u.id,
            "property_id": u.property_id,
            "property_name": u.property.name if u.property else None,
            "name": u.name,
            "description": u.description,
            "bedrooms": u.bedrooms,
            "bathrooms": u.bathrooms,
            "size_sqm": u.size_sqm,
            "rent_amount": float(u.rent_amount),
            "is_active": u.is_active,
            "created_at": u.created_at,
            "occupancy_status": occupancy,
            "tenant_name": tenant_name,
        })

    return result


# ─── Get Unit ───

@router.get("/{unit_id}")
def get_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    unit = (
        db.query(Unit)
        .join(Property, Unit.property_id == Property.id)
        .filter(
            Unit.id == unit_id,
            Property.organization_id == membership.organization_id
        )
        .first()
    )

    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    active_lease = (
        db.query(Lease)
        .filter(Lease.unit_id == unit.id, Lease.status == "active")
        .first()
    )

    tenant_name = None
    occupancy = "vacant"
    if active_lease:
        occupancy = "occupied"
        tenant = db.query(Tenant).filter(Tenant.id == active_lease.tenant_id).first()
        if tenant:
            tenant_name = tenant.full_name

    return {
        "id": unit.id,
        "property_id": unit.property_id,
        "property_name": unit.property.name if unit.property else None,
        "name": unit.name,
        "description": unit.description,
        "bedrooms": unit.bedrooms,
        "bathrooms": unit.bathrooms,
        "size_sqm": unit.size_sqm,
        "rent_amount": float(unit.rent_amount),
        "is_active": unit.is_active,
        "created_at": unit.created_at,
        "occupancy_status": occupancy,
        "tenant_name": tenant_name,
    }


# ─── Update Unit ───

@router.put("/{unit_id}")
def update_unit(
    unit_id: str,
    payload: UnitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    unit = (
        db.query(Unit)
        .join(Property, Unit.property_id == Property.id)
        .filter(
            Unit.id == unit_id,
            Property.organization_id == membership.organization_id
        )
        .first()
    )

    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(unit, key, value)

    db.commit()
    db.refresh(unit)

    return {
        "id": unit.id,
        "property_id": unit.property_id,
        "name": unit.name,
        "description": unit.description,
        "bedrooms": unit.bedrooms,
        "bathrooms": unit.bathrooms,
        "size_sqm": unit.size_sqm,
        "rent_amount": float(unit.rent_amount),
        "is_active": unit.is_active,
        "created_at": unit.created_at,
    }


# ─── Delete Unit ───

@router.delete("/{unit_id}")
def delete_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    unit = (
        db.query(Unit)
        .join(Property, Unit.property_id == Property.id)
        .filter(
            Unit.id == unit_id,
            Property.organization_id == membership.organization_id
        )
        .first()
    )

    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Check for active leases
    active_lease = (
        db.query(Lease)
        .filter(Lease.unit_id == unit_id, Lease.status == "active")
        .first()
    )
    if active_lease:
        raise HTTPException(status_code=400, detail="Cannot delete unit with an active lease")

    db.delete(unit)
    db.commit()

    return {"message": "Unit deleted"}
