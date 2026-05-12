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
from app.services.audit_service import log_action

router = APIRouter(prefix="/units", tags=["Units"])


def get_user_org(user, db):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def unit_response(u, db):
    active_lease = db.query(Lease).filter(Lease.unit_id == u.id, Lease.status == "active").first()
    tenant_name = None
    occupancy = "vacant"
    if active_lease:
        occupancy = "occupied"
        tenant = db.query(Tenant).filter(Tenant.id == active_lease.tenant_id).first()
        if tenant:
            tenant_name = tenant.full_name
    return {
        "id": u.id, "property_id": u.property_id,
        "property_name": u.property.name if u.property else None,
        "name": u.name, "description": u.description,
        "bedrooms": u.bedrooms, "bathrooms": u.bathrooms,
        "size_sqm": u.size_sqm, "rent_amount": float(u.rent_amount),
        "is_active": u.is_active, "created_at": u.created_at,
        "occupancy_status": occupancy, "tenant_name": tenant_name,
    }


@router.post("/")
def create_unit(payload: UnitCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    prop = db.query(Property).filter(Property.id == payload.property_id, Property.organization_id == membership.organization_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    unit = Unit(id=str(uuid.uuid4()), property_id=payload.property_id, name=payload.name, description=payload.description, bedrooms=payload.bedrooms, bathrooms=payload.bathrooms, size_sqm=payload.size_sqm, rent_amount=payload.rent_amount)
    db.add(unit)
    db.flush()
    log_action(db, membership.organization_id, current_user.id, "create", "unit", unit.id, f"Created unit: {payload.name} in {prop.name}", new_values={"name": payload.name, "rent_amount": payload.rent_amount})
    db.commit()
    db.refresh(unit)
    return unit_response(unit, db)


@router.get("/")
def list_units(property_id: str = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    query = db.query(Unit).join(Property, Unit.property_id == Property.id).filter(Property.organization_id == membership.organization_id)
    if property_id:
        query = query.filter(Unit.property_id == property_id)
    return [unit_response(u, db) for u in query.all()]


@router.get("/{unit_id}")
def get_unit(unit_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    unit = db.query(Unit).join(Property, Unit.property_id == Property.id).filter(Unit.id == unit_id, Property.organization_id == membership.organization_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit_response(unit, db)


@router.put("/{unit_id}")
def update_unit(unit_id: str, payload: UnitUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    unit = db.query(Unit).join(Property, Unit.property_id == Property.id).filter(Unit.id == unit_id, Property.organization_id == membership.organization_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    old_values = {"name": unit.name, "rent_amount": float(unit.rent_amount), "description": unit.description, "bedrooms": unit.bedrooms, "bathrooms": unit.bathrooms}
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(unit, key, value)
    log_action(db, membership.organization_id, current_user.id, "update", "unit", unit.id, f"Updated unit: {unit.name}", old_values=old_values, new_values=update_data)
    db.commit()
    db.refresh(unit)
    return unit_response(unit, db)


@router.delete("/{unit_id}")
def delete_unit(unit_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    unit = db.query(Unit).join(Property, Unit.property_id == Property.id).filter(Unit.id == unit_id, Property.organization_id == membership.organization_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    active_lease = db.query(Lease).filter(Lease.unit_id == unit_id, Lease.status == "active").first()
    if active_lease:
        raise HTTPException(status_code=400, detail="Cannot delete unit with an active lease")
    log_action(db, membership.organization_id, current_user.id, "delete", "unit", unit.id, f"Deleted unit: {unit.name}")
    db.delete(unit)
    db.commit()
    return {"message": "Unit deleted"}