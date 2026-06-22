#backend\app\services\expense_category_service.py
"""
Expense category business logic (Sprint 5).

Categories are configurable per organization. Landlord/Finance manage them;
Property Managers may read them (to populate the dropdown when creating an
expense); tenants have no access.

Categories are never hard-deleted — they're referenced by expenses, so they're
deactivated (is_active=False) instead, which hides them from new-expense pickers
while preserving historical expense labels.
"""
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.expense_category import ExpenseCategory
from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE
from app.services.audit_service import log_action

FULL_ACCESS_ROLES = {LANDLORD, FINANCE}


def _role(membership: OrganizationMember) -> str:
    return membership.role.name if membership.role else None


def _assert_can_read(membership: OrganizationMember):
    if _role(membership) not in FULL_ACCESS_ROLES and _role(membership) != PROPERTY_MANAGER:
        raise HTTPException(status_code=403, detail="You do not have access to expense categories")


def _assert_can_manage(membership: OrganizationMember):
    if _role(membership) not in FULL_ACCESS_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only a landlord or finance user can manage expense categories",
        )


def list_categories(db: Session, membership: OrganizationMember, include_inactive: bool = False) -> list:
    _assert_can_read(membership)
    query = db.query(ExpenseCategory).filter(
        ExpenseCategory.organization_id == membership.organization_id
    )
    if not include_inactive:
        query = query.filter(ExpenseCategory.is_active == True)  # noqa: E712
    return query.order_by(ExpenseCategory.name.asc()).all()


def create_category(db: Session, current_user: User, membership: OrganizationMember, payload) -> ExpenseCategory:
    _assert_can_manage(membership)
    org_id = membership.organization_id

    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name is required")

    existing = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.organization_id == org_id, ExpenseCategory.name == name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A category with this name already exists")

    category = ExpenseCategory(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        name=name,
        description=payload.description,
        is_active=True,
    )
    db.add(category)
    db.flush()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="create", entity_type="expense_category", entity_id=category.id,
        description=f"Created expense category: {name}",
        new_values={"name": name},
    )

    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, current_user: User, membership: OrganizationMember, category_id: str, payload) -> ExpenseCategory:
    _assert_can_manage(membership)
    org_id = membership.organization_id

    category = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.id == category_id, ExpenseCategory.organization_id == org_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")

    data = payload.dict(exclude_unset=True)

    if "name" in data:
        new_name = (data["name"] or "").strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Category name cannot be empty")
        if new_name != category.name:
            clash = (
                db.query(ExpenseCategory)
                .filter(ExpenseCategory.organization_id == org_id, ExpenseCategory.name == new_name)
                .first()
            )
            if clash:
                raise HTTPException(status_code=400, detail="A category with this name already exists")
        data["name"] = new_name

    old_values = {"name": category.name, "is_active": category.is_active}

    for key, value in data.items():
        setattr(category, key, value)
    category.updated_at = datetime.utcnow()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="update", entity_type="expense_category", entity_id=category.id,
        description=f"Updated expense category: {category.name}",
        old_values=old_values, new_values={k: str(v) for k, v in data.items()},
    )

    db.commit()
    db.refresh(category)
    return category
