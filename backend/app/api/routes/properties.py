#backend\app\api\routes\properties.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from pydantic import BaseModel
from typing import Optional

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.property_manager import PropertyManager
from app.schemas.organization import PropertyCreate, PropertyOut, AssignManagerRequest
from app.core.roles import LANDLORD, PROPERTY_MANAGER
from app.services.audit_service import log_action

router = APIRouter(prefix="/properties", tags=["Properties"])


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


def get_user_org_membership(user, db):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You do not belong to any organization")
    return membership


@router.post("/", response_model=PropertyOut)
def create_property(payload: PropertyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org_membership(current_user, db)
    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can create properties")
    new_property = Property(id=str(uuid.uuid4()), name=payload.name, address=payload.address, city=payload.city, country=payload.country, organization_id=membership.organization_id)
    db.add(new_property)
    db.flush()
    log_action(db, membership.organization_id, current_user.id, "create", "property", new_property.id, f"Created property: {payload.name}", new_values={"name": payload.name, "address": payload.address, "city": payload.city, "country": payload.country})
    db.commit()
    db.refresh(new_property)
    return new_property


@router.get("/")
def list_properties(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org_membership(current_user, db)
    if membership.role.name == LANDLORD:
        properties = db.query(Property).filter(Property.organization_id == membership.organization_id).all()
    else:
        assigned_ids = db.query(PropertyManager.property_id).filter(PropertyManager.user_id == current_user.id).subquery()
        properties = db.query(Property).filter(Property.organization_id == membership.organization_id, Property.id.in_(assigned_ids)).all()
    return [{"id": p.id, "name": p.name, "address": p.address, "city": p.city, "country": p.country, "organization_id": p.organization_id, "created_at": p.created_at} for p in properties]


@router.get("/{property_id}")
def get_property(property_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org_membership(current_user, db)
    prop = db.query(Property).filter(Property.id == property_id, Property.organization_id == membership.organization_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    managers = db.query(PropertyManager).filter(PropertyManager.property_id == property_id).all()
    manager_list = []
    for pm in managers:
        user = db.query(User).filter(User.id == pm.user_id).first()
        if user:
            manager_list.append({"user_id": user.id, "email": user.email})
    return {"id": prop.id, "name": prop.name, "address": prop.address, "city": prop.city, "country": prop.country, "organization_id": prop.organization_id, "created_at": prop.created_at, "managers": manager_list}


@router.put("/{property_id}")
def update_property(property_id: str, payload: PropertyUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org_membership(current_user, db)
    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can edit properties")
    prop = db.query(Property).filter(Property.id == property_id, Property.organization_id == membership.organization_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    old_values = {"name": prop.name, "address": prop.address, "city": prop.city, "country": prop.country}
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prop, key, value)
    log_action(db, membership.organization_id, current_user.id, "update", "property", prop.id, f"Updated property: {prop.name}", old_values=old_values, new_values=update_data)
    db.commit()
    db.refresh(prop)
    return {"id": prop.id, "name": prop.name, "address": prop.address, "city": prop.city, "country": prop.country, "organization_id": prop.organization_id, "created_at": prop.created_at}


@router.post("/{property_id}/assign-manager")
def assign_manager(property_id: str, payload: AssignManagerRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org_membership(current_user, db)
    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can assign managers")
    prop = db.query(Property).filter(Property.id == property_id, Property.organization_id == membership.organization_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    target_membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == payload.user_id, OrganizationMember.organization_id == membership.organization_id).first()
    if not target_membership:
        raise HTTPException(status_code=404, detail="User is not a member of this organization")
    if target_membership.role.name != PROPERTY_MANAGER:
        raise HTTPException(status_code=400, detail="User must have the PROPERTY_MANAGER role")
    existing = db.query(PropertyManager).filter(PropertyManager.property_id == property_id, PropertyManager.user_id == payload.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Manager is already assigned")
    assignment = PropertyManager(id=str(uuid.uuid4()), property_id=property_id, user_id=payload.user_id)
    db.add(assignment)
    user = db.query(User).filter(User.id == payload.user_id).first()
    log_action(db, membership.organization_id, current_user.id, "create", "property_manager", assignment.id, f"Assigned {user.email} to {prop.name}")
    db.commit()
    return {"message": f"Manager {user.email} assigned to {prop.name}", "property_id": property_id, "user_id": payload.user_id}


@router.delete("/{property_id}/remove-manager/{user_id}")
def remove_manager(property_id: str, user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org_membership(current_user, db)
    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can remove managers")
    assignment = db.query(PropertyManager).filter(PropertyManager.property_id == property_id, PropertyManager.user_id == user_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    log_action(db, membership.organization_id, current_user.id, "delete", "property_manager", assignment.id, f"Removed manager from property {property_id}")
    db.delete(assignment)
    db.commit()
    return {"message": "Manager removed from property"}