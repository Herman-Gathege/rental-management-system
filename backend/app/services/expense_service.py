#backend\app\services\expense_service.py
"""
Expense business logic (Sprint 5).

Routes stay thin: they resolve the caller's org membership and hand it here.
This module owns validation, the status workflow, role-based permissions, and
audit logging, and commits each operation. It returns ORM Expense objects; the
route serializes them (see enrich_expense in routes/expenses.py).

Status workflow:
    draft -> submitted -> approved -> paid   (-> archived, later)
    reject sends an expense back to draft.

Permissions:
    Landlord / Finance : full access across the organization.
    Property Manager   : create / edit / submit expenses for their ASSIGNED
                         properties only; cannot approve, reject, or pay, and
                         cannot delete an approved/paid expense.
    Tenant             : no access.
"""
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.property_manager import PropertyManager
from app.models.unit import Unit
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.expense_attachment import ExpenseAttachment
from app.models.vendor import Vendor
from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE
from app.services.audit_service import log_action
from app.services.s3_service import upload_file


# ─── Status constants ───

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_APPROVED = "approved"
STATUS_PAID = "paid"
STATUS_ARCHIVED = "archived"

# Roles with full, org-wide access to every expense.
FULL_ACCESS_ROLES = {LANDLORD, FINANCE}

# Expenses can only be edited while in these states (once approved/paid they're
# locked; reject back to draft to edit).
EDITABLE_STATUSES = {STATUS_DRAFT, STATUS_SUBMITTED}


# ─── Helpers ───

def _role(membership: OrganizationMember) -> str:
    return membership.role.name if membership.role else None


def _assert_not_tenant(membership: OrganizationMember):
    role = _role(membership)
    if role not in FULL_ACCESS_ROLES and role != PROPERTY_MANAGER:
        raise HTTPException(status_code=403, detail="You do not have access to expenses")


def get_pm_property_ids(db: Session, user_id: str, org_id: str) -> list:
    """Property IDs assigned to a property manager, scoped to their org."""
    rows = (
        db.query(PropertyManager.property_id)
        .join(Property, Property.id == PropertyManager.property_id)
        .filter(
            PropertyManager.user_id == user_id,
            Property.organization_id == org_id,
        )
        .all()
    )
    return [r[0] for r in rows]


def _ensure_property_access(db: Session, membership: OrganizationMember, property_id: str):
    """Landlord/Finance may touch any property in the org; a PM only their
    assigned properties; tenants never."""
    role = _role(membership)
    if role in FULL_ACCESS_ROLES:
        return
    if role == PROPERTY_MANAGER:
        if property_id not in get_pm_property_ids(db, membership.user_id, membership.organization_id):
            raise HTTPException(
                status_code=403,
                detail="You can only manage expenses for properties assigned to you",
            )
        return
    raise HTTPException(status_code=403, detail="You do not have access to expenses")


def _assert_approver(membership: OrganizationMember):
    """Only Landlord or Finance may approve / reject / pay."""
    if _role(membership) not in FULL_ACCESS_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only a landlord or finance user can approve, reject, or pay expenses",
        )


def _get_org_expense(db: Session, org_id: str, expense_id: str) -> Expense:
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.organization_id == org_id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


def _validate_refs(db: Session, org_id: str, *, property_id, category_id, vendor_id, unit_id):
    """Validate that referenced property/category/vendor/unit exist and are
    consistent (in the org, unit under the property)."""
    prop = (
        db.query(Property)
        .filter(Property.id == property_id, Property.organization_id == org_id)
        .first()
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    category = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.id == category_id, ExpenseCategory.organization_id == org_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")

    if vendor_id:
        vendor = (
            db.query(Vendor)
            .filter(Vendor.id == vendor_id, Vendor.organization_id == org_id)
            .first()
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

    if unit_id:
        unit = (
            db.query(Unit)
            .filter(Unit.id == unit_id, Unit.property_id == property_id)
            .first()
        )
        if not unit:
            raise HTTPException(
                status_code=400,
                detail="Unit does not belong to the selected property",
            )


def _validate_amount(amount):
    if amount is None or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")


# ─── Create / Read / Update / Delete ───

def create_expense(db: Session, current_user: User, membership: OrganizationMember, payload) -> Expense:
    org_id = membership.organization_id
    _assert_not_tenant(membership)
    _validate_amount(payload.amount)
    _ensure_property_access(db, membership, payload.property_id)
    _validate_refs(
        db, org_id,
        property_id=payload.property_id,
        category_id=payload.category_id,
        vendor_id=payload.vendor_id,
        unit_id=payload.unit_id,
    )

    expense = Expense(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        vendor_id=payload.vendor_id,
        category_id=payload.category_id,
        created_by=current_user.id,
        approved_by=None,
        title=payload.title,
        description=payload.description,
        amount=payload.amount,
        expense_date=payload.expense_date,
        payment_method=payload.payment_method,
        reference_number=payload.reference_number,
        status=STATUS_DRAFT,
        receipt_number=payload.receipt_number,
        notes=payload.notes,
    )
    db.add(expense)
    db.flush()

    log_action(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        action="create",
        entity_type="expense",
        entity_id=expense.id,
        description=f"Created expense: {expense.title}",
        new_values={
            "title": expense.title,
            "amount": float(expense.amount),
            "property_id": expense.property_id,
            "category_id": expense.category_id,
            "status": expense.status,
        },
    )

    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(
    db: Session,
    current_user: User,
    membership: OrganizationMember,
    *,
    property_id: str = None,
    status: str = None,
    category_id: str = None,
    vendor_id: str = None,
) -> list:
    org_id = membership.organization_id
    _assert_not_tenant(membership)

    query = db.query(Expense).filter(Expense.organization_id == org_id)

    # A property manager only ever sees expenses for their assigned properties.
    if _role(membership) == PROPERTY_MANAGER:
        pm_ids = get_pm_property_ids(db, membership.user_id, org_id)
        if not pm_ids:
            return []
        query = query.filter(Expense.property_id.in_(pm_ids))

    if property_id:
        query = query.filter(Expense.property_id == property_id)
    if status:
        query = query.filter(Expense.status == status)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if vendor_id:
        query = query.filter(Expense.vendor_id == vendor_id)

    return (
        query.order_by(Expense.expense_date.desc(), Expense.created_at.desc()).all()
    )


def get_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str) -> Expense:
    _assert_not_tenant(membership)
    expense = _get_org_expense(db, membership.organization_id, expense_id)
    _ensure_property_access(db, membership, expense.property_id)
    return expense


def update_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str, payload) -> Expense:
    org_id = membership.organization_id
    _assert_not_tenant(membership)
    expense = _get_org_expense(db, org_id, expense_id)
    _ensure_property_access(db, membership, expense.property_id)

    if expense.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"An expense that is {expense.status} cannot be edited. Reject it back to draft first.",
        )

    data = payload.dict(exclude_unset=True)

    # If a field is being changed, re-validate the affected references.
    if "amount" in data:
        _validate_amount(data["amount"])

    new_property_id = data.get("property_id", expense.property_id)
    new_category_id = data.get("category_id", expense.category_id)
    new_vendor_id = data.get("vendor_id", expense.vendor_id)
    new_unit_id = data.get("unit_id", expense.unit_id)

    # If moving to a different property, the caller must have access to it too.
    if "property_id" in data and data["property_id"] != expense.property_id:
        _ensure_property_access(db, membership, data["property_id"])

    _validate_refs(
        db, org_id,
        property_id=new_property_id,
        category_id=new_category_id,
        vendor_id=new_vendor_id,
        unit_id=new_unit_id,
    )

    old_values = {
        "title": expense.title,
        "amount": float(expense.amount),
        "category_id": expense.category_id,
        "status": expense.status,
    }

    for key, value in data.items():
        setattr(expense, key, value)
    expense.updated_at = datetime.utcnow()

    log_action(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        action="update",
        entity_type="expense",
        entity_id=expense.id,
        description=f"Updated expense: {expense.title}",
        old_values=old_values,
        new_values={k: (float(v) if k == "amount" else str(v)) for k, v in data.items()},
    )

    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str):
    org_id = membership.organization_id
    _assert_not_tenant(membership)
    expense = _get_org_expense(db, org_id, expense_id)
    _ensure_property_access(db, membership, expense.property_id)

    role = _role(membership)
    if role == PROPERTY_MANAGER and expense.status not in (STATUS_DRAFT, STATUS_SUBMITTED):
        raise HTTPException(
            status_code=403,
            detail="Property managers cannot delete an approved or paid expense",
        )
    if expense.status in (STATUS_PAID, STATUS_ARCHIVED):
        raise HTTPException(
            status_code=400,
            detail="A paid or archived expense cannot be deleted",
        )

    log_action(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        action="delete",
        entity_type="expense",
        entity_id=expense.id,
        description=f"Deleted expense: {expense.title}",
        old_values={"title": expense.title, "amount": float(expense.amount), "status": expense.status},
    )

    db.delete(expense)
    db.commit()


# ─── Workflow transitions ───

def submit_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str) -> Expense:
    org_id = membership.organization_id
    _assert_not_tenant(membership)
    expense = _get_org_expense(db, org_id, expense_id)
    _ensure_property_access(db, membership, expense.property_id)

    if expense.status != STATUS_DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Only a draft expense can be submitted (this one is {expense.status})",
        )

    expense.status = STATUS_SUBMITTED
    expense.updated_at = datetime.utcnow()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="update", entity_type="expense", entity_id=expense.id,
        description=f"Submitted expense for approval: {expense.title}",
        old_values={"status": STATUS_DRAFT}, new_values={"status": STATUS_SUBMITTED},
    )

    db.commit()
    db.refresh(expense)
    return expense


def approve_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str) -> Expense:
    org_id = membership.organization_id
    _assert_approver(membership)
    expense = _get_org_expense(db, org_id, expense_id)

    if expense.status != STATUS_SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Only a submitted expense can be approved (this one is {expense.status})",
        )

    expense.status = STATUS_APPROVED
    expense.approved_by = current_user.id
    expense.updated_at = datetime.utcnow()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="update", entity_type="expense", entity_id=expense.id,
        description=f"Approved expense: {expense.title}",
        old_values={"status": STATUS_SUBMITTED}, new_values={"status": STATUS_APPROVED},
    )

    db.commit()
    db.refresh(expense)
    return expense


def reject_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str, reason: str = None) -> Expense:
    org_id = membership.organization_id
    _assert_approver(membership)
    expense = _get_org_expense(db, org_id, expense_id)

    if expense.status != STATUS_SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Only a submitted expense can be rejected (this one is {expense.status})",
        )

    # Rejected expenses return to draft so they can be corrected and resubmitted.
    expense.status = STATUS_DRAFT
    expense.approved_by = None
    expense.updated_at = datetime.utcnow()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="update", entity_type="expense", entity_id=expense.id,
        description=f"Rejected expense: {expense.title}" + (f" — {reason}" if reason else ""),
        old_values={"status": STATUS_SUBMITTED},
        new_values={"status": STATUS_DRAFT, "reason": reason},
    )

    db.commit()
    db.refresh(expense)
    return expense


def pay_expense(db: Session, current_user: User, membership: OrganizationMember, expense_id: str, payload=None) -> Expense:
    org_id = membership.organization_id
    _assert_approver(membership)
    expense = _get_org_expense(db, org_id, expense_id)

    # Business rule: an expense cannot be paid unless it is approved.
    if expense.status != STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"An expense must be approved before it can be marked paid (this one is {expense.status})",
        )

    if payload is not None:
        if getattr(payload, "payment_method", None):
            expense.payment_method = payload.payment_method
        if getattr(payload, "reference_number", None):
            expense.reference_number = payload.reference_number

    expense.status = STATUS_PAID
    expense.updated_at = datetime.utcnow()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="update", entity_type="expense", entity_id=expense.id,
        description=f"Marked expense paid: {expense.title}",
        old_values={"status": STATUS_APPROVED}, new_values={"status": STATUS_PAID},
    )

    db.commit()
    db.refresh(expense)
    return expense


# ─── Attachments (receipts / invoices / etc.) ───
#
# An expense may carry several files. Anyone who can manage the expense (not a
# tenant, and within their property scope) may add or remove attachments,
# regardless of the expense's status — receipts are evidence and don't change
# the financial amount. As with leases/tenant docs, deleting an attachment drops
# the DB row and leaves the stored file for a later cleanup job.

def add_attachment(
    db: Session,
    current_user: User,
    membership: OrganizationMember,
    expense_id: str,
    *,
    file_bytes: bytes,
    filename: str,
) -> Expense:
    org_id = membership.organization_id
    _assert_not_tenant(membership)
    expense = _get_org_expense(db, org_id, expense_id)
    _ensure_property_access(db, membership, expense.property_id)

    s3_key = f"expense-receipts/{expense.id}/{uuid.uuid4()}-{filename}"
    try:
        file_url = upload_file(s3_key, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    attachment = ExpenseAttachment(
        id=str(uuid.uuid4()),
        expense_id=expense.id,
        filename=filename,
        file_url=file_url,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    db.flush()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="create", entity_type="expense_attachment", entity_id=attachment.id,
        description=f"Attached a receipt to expense: {expense.title}",
        new_values={"filename": filename},
    )

    db.commit()
    db.refresh(expense)
    return expense


def delete_attachment(db: Session, current_user: User, membership: OrganizationMember, attachment_id: str) -> Expense:
    org_id = membership.organization_id
    _assert_not_tenant(membership)

    attachment = (
        db.query(ExpenseAttachment)
        .filter(ExpenseAttachment.id == attachment_id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # _get_org_expense also guarantees the attachment's expense is in the
    # caller's organization (cross-org access -> 404).
    expense = _get_org_expense(db, org_id, attachment.expense_id)
    _ensure_property_access(db, membership, expense.property_id)

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="delete", entity_type="expense_attachment", entity_id=attachment.id,
        description=f"Removed a receipt from expense: {expense.title}",
        old_values={"filename": attachment.filename},
    )

    # Drop the DB reference; the stored file is left for a later cleanup job.
    db.delete(attachment)
    db.commit()
    db.refresh(expense)
    return expense