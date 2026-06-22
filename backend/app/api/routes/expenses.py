#backend\app\api\routes\expenses.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.unit import Unit
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.vendor import Vendor
from app.models.expense_attachment import ExpenseAttachment
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseRejectPayload,
    ExpensePayPayload,
)
from app.services import expense_service

router = APIRouter(prefix="/expenses", tags=["Expenses"])


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


def enrich_expense(expense: Expense, db: Session) -> dict:
    """Add category/vendor/property/unit names, creator/approver emails, and
    attachments to the expense response."""
    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == expense.category_id).first()
    vendor = db.query(Vendor).filter(Vendor.id == expense.vendor_id).first() if expense.vendor_id else None
    prop = db.query(Property).filter(Property.id == expense.property_id).first()
    unit = db.query(Unit).filter(Unit.id == expense.unit_id).first() if expense.unit_id else None
    creator = db.query(User).filter(User.id == expense.created_by).first()
    approver = db.query(User).filter(User.id == expense.approved_by).first() if expense.approved_by else None

    attachments = (
        db.query(ExpenseAttachment)
        .filter(ExpenseAttachment.expense_id == expense.id)
        .order_by(ExpenseAttachment.created_at.asc())
        .all()
    )

    return {
        "id": expense.id,
        "organization_id": expense.organization_id,
        "property_id": expense.property_id,
        "property_name": prop.name if prop else None,
        "unit_id": expense.unit_id,
        "unit_name": unit.name if unit else None,
        "vendor_id": expense.vendor_id,
        "vendor_name": vendor.vendor_name if vendor else None,
        "category_id": expense.category_id,
        "category_name": category.name if category else None,
        "created_by": expense.created_by,
        "created_by_email": creator.email if creator else None,
        "approved_by": expense.approved_by,
        "approved_by_email": approver.email if approver else None,
        "title": expense.title,
        "description": expense.description,
        "amount": float(expense.amount) if expense.amount is not None else 0,
        "expense_date": expense.expense_date,
        "payment_method": expense.payment_method,
        "reference_number": expense.reference_number,
        "status": expense.status,
        "receipt_number": expense.receipt_number,
        "notes": expense.notes,
        "created_at": expense.created_at,
        "updated_at": expense.updated_at,
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "file_url": a.file_url,
                "uploaded_at": a.created_at,
            }
            for a in attachments
        ],
    }


# ─── Create ───

@router.post("/")
def create_expense(
    payload: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.create_expense(db, current_user, membership, payload)
    return enrich_expense(expense, db)


# ─── List ───

@router.get("/")
def list_expenses(
    property_id: str = Query(None),
    status: str = Query(None),
    category_id: str = Query(None),
    vendor_id: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expenses = expense_service.list_expenses(
        db, current_user, membership,
        property_id=property_id, status=status,
        category_id=category_id, vendor_id=vendor_id,
    )
    return [enrich_expense(e, db) for e in expenses]


# ─── Get ───

@router.get("/{expense_id}")
def get_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.get_expense(db, current_user, membership, expense_id)
    return enrich_expense(expense, db)


# ─── Update ───

@router.put("/{expense_id}")
def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.update_expense(db, current_user, membership, expense_id, payload)
    return enrich_expense(expense, db)


# ─── Delete ───

@router.delete("/{expense_id}")
def delete_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense_service.delete_expense(db, current_user, membership, expense_id)
    return {"message": "Expense deleted"}


# ─── Workflow: submit / approve / reject / pay ───

@router.post("/{expense_id}/submit")
def submit_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.submit_expense(db, current_user, membership, expense_id)
    return enrich_expense(expense, db)


@router.post("/{expense_id}/approve")
def approve_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.approve_expense(db, current_user, membership, expense_id)
    return enrich_expense(expense, db)


@router.post("/{expense_id}/reject")
def reject_expense(
    expense_id: str,
    payload: ExpenseRejectPayload = ExpenseRejectPayload(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.reject_expense(
        db, current_user, membership, expense_id, reason=payload.reason
    )
    return enrich_expense(expense, db)


@router.post("/{expense_id}/pay")
def pay_expense(
    expense_id: str,
    payload: ExpensePayPayload = ExpensePayPayload(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.pay_expense(db, current_user, membership, expense_id, payload=payload)
    return enrich_expense(expense, db)


# ─── Attachments (receipts) ───

@router.post("/{expense_id}/attachments")
async def upload_attachment(
    expense_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    file_bytes = await file.read()
    expense = expense_service.add_attachment(
        db, current_user, membership, expense_id,
        file_bytes=file_bytes, filename=file.filename,
    )
    return enrich_expense(expense, db)


@router.delete("/{expense_id}/attachments/{attachment_id}")
def delete_attachment(
    expense_id: str,
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    expense = expense_service.delete_attachment(db, current_user, membership, attachment_id)
    return enrich_expense(expense, db)