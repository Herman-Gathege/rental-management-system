from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.property_manager import PropertyManager
from app.models.property_finance_manager import PropertyFinanceManager
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.tenant import Tenant
from app.schemas.rental import UnitCreate, UnitUpdate
from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT
from app.services.audit_service import log_action

router = APIRouter(prefix="/units", tags=["Units"])


def get_user_org(user, db):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def require_landlord_membership(membership):
    """Property + unit lifecycle is a portfolio-owner action.

    Property managers keep read access to their assigned properties and
    finance users keep read access to theirs, but only a LANDLORD may create,
    edit or delete a unit — mirroring the rule properties.py already applied.
    """
    role = membership.role.name if membership.role else None
    if role != LANDLORD:
        raise HTTPException(
            status_code=403,
            detail="Only landlords can manage units",
        )


def authorized_unit_ids(db: Session, user, membership) -> set | None:
    """Unit IDs the caller is allowed to read.

    Returns ``None`` for a landlord (meaning "no restriction"). Otherwise
    returns the explicit set of unit IDs scoped by the existing assignment
    tables — property managers and finance users see their assigned
    properties only, tenants see only units they hold a lease on.
    """
    org_id = membership.organization_id
    role = membership.role.name if membership.role else None

    if role == LANDLORD:
        return None

    if role == PROPERTY_MANAGER:
        rows = (
            db.query(Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .join(PropertyManager, PropertyManager.property_id == Property.id)
            .filter(
                Property.organization_id == org_id,
                PropertyManager.user_id == user.id,
            )
            .all()
        )
        return {r[0] for r in rows}

    if role == FINANCE:
        rows = (
            db.query(Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .join(
                PropertyFinanceManager,
                PropertyFinanceManager.property_id == Property.id,
            )
            .filter(
                Property.organization_id == org_id,
                PropertyFinanceManager.user_id == user.id,
            )
            .all()
        )
        return {r[0] for r in rows}

    if role == TENANT:
        rows = (
            db.query(Lease.unit_id)
            .join(Tenant, Tenant.id == Lease.tenant_id)
            .filter(
                Lease.organization_id == org_id,
                Tenant.user_id == user.id,
            )
            .all()
        )
        return {r[0] for r in rows}

    return set()


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
    require_landlord_membership(membership)
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
    allowed = authorized_unit_ids(db, current_user, membership)
    if allowed is not None:
        if not allowed:
            return []
        query = query.filter(Unit.id.in_(allowed))
    return [unit_response(u, db) for u in query.all()]


@router.get("/{unit_id}")
def get_unit(unit_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    allowed = authorized_unit_ids(db, current_user, membership)
    if allowed is not None and unit_id not in allowed:
        raise HTTPException(status_code=404, detail="Unit not found")
    unit = db.query(Unit).join(Property, Unit.property_id == Property.id).filter(Unit.id == unit_id, Property.organization_id == membership.organization_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit_response(unit, db)


@router.put("/{unit_id}")
def update_unit(unit_id: str, payload: UnitUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    require_landlord_membership(membership)
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
    require_landlord_membership(membership)
    unit = db.query(Unit).join(Property, Unit.property_id == Property.id).filter(Unit.id == unit_id, Property.organization_id == membership.organization_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    active_lease = db.query(Lease).filter(Lease.unit_id == unit_id, Lease.status == "active").first()
    if active_lease:
        raise HTTPException(status_code=400, detail="Cannot delete unit with an active lease")
    # A unit with any lease history carries charges/payments (and inspections)
    # that would be cascaded away with it. Financial history must survive, so
    # the unit is restricted rather than deleted — the same "restrict, never
    # cascade financial data" rule the property delete endpoint applies.
    historic_lease = db.query(Lease).filter(Lease.unit_id == unit_id).first()
    if historic_lease:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete a unit with lease or payment history. "
                "Deactivate the unit instead."
            ),
        )
    log_action(db, membership.organization_id, current_user.id, "delete", "unit", unit.id, f"Deleted unit: {unit.name}")
    db.delete(unit)
    db.commit()
    return {"message": "Unit deleted"}
