#backend\app\api\routes\checklist_template.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.checklist_item_template import ChecklistItemTemplate
from app.core.roles import LANDLORD
from app.services.audit_service import log_action

router = APIRouter(prefix="/checklist-template", tags=["Checklist Template"])


# ─── Schemas ───

class ChecklistItemCreate(BaseModel):
    item_name: str
    sort_order: Optional[int] = None


class ChecklistItemUpdate(BaseModel):
    item_name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# ─── Helper ───

def get_user_org(user: User, db: Session):
    """Helper: get the current user's org membership or raise 403."""
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def item_dict(item):
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "item_name": item.item_name,
        "sort_order": item.sort_order,
        "is_default": item.is_default,
        "is_active": item.is_active,
        "created_at": item.created_at,
    }


# ─── List Checklist Items ───

@router.get("/")
def list_checklist_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    items = (
        db.query(ChecklistItemTemplate)
        .filter(ChecklistItemTemplate.organization_id == membership.organization_id)
        .order_by(ChecklistItemTemplate.sort_order.asc())
        .all()
    )

    return [item_dict(i) for i in items]


# ─── Create Checklist Item ───

@router.post("/")
def create_checklist_item(
    payload: ChecklistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    # Only landlords can manage checklist items
    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can manage checklist items")

    # Determine sort_order — append to end if not provided
    if payload.sort_order is None:
        max_order = (
            db.query(ChecklistItemTemplate)
            .filter(ChecklistItemTemplate.organization_id == membership.organization_id)
            .count()
        )
        sort_order = max_order
    else:
        sort_order = payload.sort_order

    item = ChecklistItemTemplate(
        id=str(uuid.uuid4()),
        organization_id=membership.organization_id,
        item_name=payload.item_name,
        sort_order=sort_order,
        is_default=False,
        is_active=True,
    )
    db.add(item)
    db.flush()

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="create",
        entity_type="checklist_item",
        entity_id=item.id,
        description=f"Added checklist item: {payload.item_name}",
        new_values={"item_name": payload.item_name},
    )

    db.commit()
    db.refresh(item)

    return item_dict(item)


# ─── Update Checklist Item ───

@router.put("/{item_id}")
def update_checklist_item(
    item_id: str,
    payload: ChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can manage checklist items")

    item = (
        db.query(ChecklistItemTemplate)
        .filter(
            ChecklistItemTemplate.id == item_id,
            ChecklistItemTemplate.organization_id == membership.organization_id
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    # Capture old values for audit
    old_values = {
        "item_name": item.item_name,
        "sort_order": item.sort_order,
        "is_active": item.is_active,
    }

    # Apply updates
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="update",
        entity_type="checklist_item",
        entity_id=item.id,
        description=f"Updated checklist item: {item.item_name}",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(item)

    return item_dict(item)


# ─── Delete Checklist Item ───

@router.delete("/{item_id}")
def delete_checklist_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can manage checklist items")

    item = (
        db.query(ChecklistItemTemplate)
        .filter(
            ChecklistItemTemplate.id == item_id,
            ChecklistItemTemplate.organization_id == membership.organization_id
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="delete",
        entity_type="checklist_item",
        entity_id=item.id,
        description=f"Deleted checklist item: {item.item_name}",
    )

    db.delete(item)
    db.commit()

    return {"message": "Checklist item deleted"}


# ─── Reset to Defaults ───

@router.post("/reset-defaults")
def reset_to_defaults(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Danger zone: deletes ALL items for this org and re-seeds the 13 defaults.
    Useful if the landlord wants to start over.
    """
    from app.services.checklist_seed import seed_checklist_for_org

    membership = get_user_org(current_user, db)

    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can reset the checklist")

    # Delete all existing items for this org
    db.query(ChecklistItemTemplate).filter(
        ChecklistItemTemplate.organization_id == membership.organization_id
    ).delete()

    # Re-seed defaults
    created = seed_checklist_for_org(db, membership.organization_id)

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="update",
        entity_type="checklist_item",
        entity_id="batch",
        description=f"Reset checklist to defaults ({created} items)",
    )

    db.commit()

    return {"message": f"Reset complete. {created} default items restored."}
