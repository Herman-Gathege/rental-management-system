#backend\app\api\routes\expense_categories.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate
from app.services import expense_category_service

router = APIRouter(prefix="/expense-categories", tags=["Expense Categories"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def category_dict(c: ExpenseCategory) -> dict:
    return {
        "id": c.id,
        "organization_id": c.organization_id,
        "name": c.name,
        "description": c.description,
        "is_active": c.is_active,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


@router.get("/")
def list_categories(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    categories = expense_category_service.list_categories(db, membership, include_inactive)
    return [category_dict(c) for c in categories]


@router.post("/")
def create_category(
    payload: ExpenseCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    category = expense_category_service.create_category(db, current_user, membership, payload)
    return category_dict(category)


@router.put("/{category_id}")
def update_category(
    category_id: str,
    payload: ExpenseCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    category = expense_category_service.update_category(db, current_user, membership, category_id, payload)
    return category_dict(category)
