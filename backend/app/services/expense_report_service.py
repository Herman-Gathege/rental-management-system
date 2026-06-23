#backend\app\services\expense_report_service.py
"""
Expense reporting & profitability (Sprint 5).

Read-only aggregation for the finance/landlord/manager dashboards. Everything
here is CASH BASIS and reconciles with get_finance_summary:

  income            = collected payments (Payment.amount)   -- cash in
  operating expense = PAID expenses (status == 'paid')       -- cash out
  profit / NOI      = income - operating expense

Expenses that are approved-but-not-yet-paid are reported separately as
"committed" (total_approved) rather than folded into NOI, so NOI reflects money
that actually left the business. Draft/submitted expenses never count.

Scoping mirrors the rest of the finance stack:
  Landlord          -> org-wide (scope = None)
  Finance           -> assigned properties (property_finance_managers)
  Property Manager  -> assigned properties (property_managers)
  Tenant            -> no access (403)

A scope of None means org-wide; an empty list means "assigned to nothing" =>
sees nothing (all zeros / empty).
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.vendor import Vendor
from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE
from app.services.finance_scope import assigned_finance_property_ids
from app.services.expense_service import (
    get_pm_property_ids,
    STATUS_PAID,
    STATUS_APPROVED,
    STATUS_SUBMITTED,
    STATUS_DRAFT,
)


# ─── Scope resolution ───

def resolve_scope(db: Session, current_user: User, membership: OrganizationMember):
    """Return the property scope for this caller:
       None  -> org-wide (landlord)
       list  -> restricted to these property ids (finance/PM; may be empty)
    Raises 403 for tenants / anyone else."""
    role = membership.role.name if membership.role else None
    org_id = membership.organization_id

    if role == LANDLORD:
        return None
    if role == FINANCE:
        return assigned_finance_property_ids(db, current_user.id, org_id)
    if role == PROPERTY_MANAGER:
        return get_pm_property_ids(db, current_user.id, org_id)
    raise HTTPException(status_code=403, detail="You do not have access to expense reports")


def narrow_scope(scope, property_id):
    """Apply an optional single-property filter on top of the role scope.
    A property_id outside the scope is ignored (keeps the role scope)."""
    if not property_id:
        return scope
    if scope is None:
        return [property_id]
    if property_id in scope:
        return [property_id]
    return scope


# ─── Internal query helpers ───

def _apply_expense_filters(query, *, org_id, property_ids, start_date, end_date, status=None):
    query = query.filter(Expense.organization_id == org_id)
    if status is not None:
        query = query.filter(Expense.status == status)
    if property_ids is not None:
        query = query.filter(Expense.property_id.in_(property_ids))
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    return query


def _income_by_property(db, org_id, property_ids, start_date, end_date) -> dict:
    """{property_id: collected_income} from payments, joined property via
    payment -> lease -> unit -> property."""
    query = (
        db.query(Property.id, func.coalesce(func.sum(Payment.amount), 0))
        .join(Unit, Unit.property_id == Property.id)
        .join(Lease, Lease.unit_id == Unit.id)
        .join(Payment, Payment.lease_id == Lease.id)
        .filter(Property.organization_id == org_id)
    )
    if property_ids is not None:
        query = query.filter(Property.id.in_(property_ids))
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    query = query.group_by(Property.id)
    return {pid: float(total) for pid, total in query.all()}


def _paid_expenses_by_property(db, org_id, property_ids, start_date, end_date) -> dict:
    """{property_id: paid_expense_total}."""
    query = db.query(Expense.property_id, func.coalesce(func.sum(Expense.amount), 0))
    query = _apply_expense_filters(
        query, org_id=org_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date, status=STATUS_PAID,
    )
    query = query.group_by(Expense.property_id)
    return {pid: float(total) for pid, total in query.all()}


def _scope_properties(db, org_id, property_ids):
    query = db.query(Property).filter(Property.organization_id == org_id)
    if property_ids is not None:
        query = query.filter(Property.id.in_(property_ids))
    return query.order_by(Property.name.asc()).all()


# ─── Reports ───

def expense_summary(db, *, org_id, property_ids, start_date=None, end_date=None) -> dict:
    """Per-status expense totals for the scope/date range."""
    if property_ids is not None and len(property_ids) == 0:
        return {
            "total_paid": 0.0, "total_approved": 0.0,
            "total_submitted": 0.0, "total_draft": 0.0, "count": 0,
        }

    query = db.query(
        Expense.status,
        func.coalesce(func.sum(Expense.amount), 0),
        func.count(Expense.id),
    )
    query = _apply_expense_filters(
        query, org_id=org_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )
    rows = query.group_by(Expense.status).all()

    by_status = {status: (float(total), int(cnt)) for status, total, cnt in rows}
    return {
        "total_paid": by_status.get(STATUS_PAID, (0.0, 0))[0],
        "total_approved": by_status.get(STATUS_APPROVED, (0.0, 0))[0],
        "total_submitted": by_status.get(STATUS_SUBMITTED, (0.0, 0))[0],
        "total_draft": by_status.get(STATUS_DRAFT, (0.0, 0))[0],
        "count": sum(c for _, c in by_status.values()),
    }


def expenses_by_category(db, *, org_id, property_ids, start_date=None, end_date=None) -> list:
    """Paid expense totals grouped by category, largest first."""
    if property_ids is not None and len(property_ids) == 0:
        return []

    query = (
        db.query(
            ExpenseCategory.id,
            ExpenseCategory.name,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .join(Expense, Expense.category_id == ExpenseCategory.id)
    )
    query = _apply_expense_filters(
        query, org_id=org_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date, status=STATUS_PAID,
    )
    rows = (
        query.group_by(ExpenseCategory.id, ExpenseCategory.name)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    return [
        {"category_id": cid, "category_name": name, "total": float(total)}
        for cid, name, total in rows
    ]


def expenses_by_vendor(db, *, org_id, property_ids, start_date=None, end_date=None) -> list:
    """Paid expense totals grouped by vendor (only expenses that have a vendor),
    largest first — answers 'how much have we paid <vendor>?'."""
    if property_ids is not None and len(property_ids) == 0:
        return []

    query = (
        db.query(
            Vendor.id,
            Vendor.vendor_name,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .join(Expense, Expense.vendor_id == Vendor.id)
    )
    query = _apply_expense_filters(
        query, org_id=org_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date, status=STATUS_PAID,
    )
    rows = (
        query.group_by(Vendor.id, Vendor.vendor_name)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    return [
        {"vendor_id": vid, "vendor_name": name, "total": float(total)}
        for vid, name, total in rows
    ]


def monthly_expenses(db, *, org_id, property_ids, start_date=None, end_date=None) -> list:
    """Paid expense total per calendar month (YYYY-MM), oldest first."""
    if property_ids is not None and len(property_ids) == 0:
        return []

    month = func.to_char(Expense.expense_date, "YYYY-MM")
    query = db.query(month.label("month"), func.coalesce(func.sum(Expense.amount), 0))
    query = _apply_expense_filters(
        query, org_id=org_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date, status=STATUS_PAID,
    )
    rows = query.group_by(month).order_by(month).all()
    return [{"month": m, "total": float(total)} for m, total in rows]


def profit_by_property(db, *, org_id, property_ids, start_date=None, end_date=None) -> list:
    """Per-property income (collected) − expenses (paid) = profit. Includes
    every in-scope property, even those with no activity (zeros)."""
    if property_ids is not None and len(property_ids) == 0:
        return []

    income_map = _income_by_property(db, org_id, property_ids, start_date, end_date)
    expense_map = _paid_expenses_by_property(db, org_id, property_ids, start_date, end_date)
    properties = _scope_properties(db, org_id, property_ids)

    rows = []
    for p in properties:
        income = round(income_map.get(p.id, 0.0), 2)
        expenses = round(expense_map.get(p.id, 0.0), 2)
        rows.append({
            "property_id": p.id,
            "property_name": p.name,
            "income": income,
            "expenses": expenses,
            "profit": round(income - expenses, 2),
        })
    # Most profitable first.
    rows.sort(key=lambda r: r["profit"], reverse=True)
    return rows


def noi_summary(db, *, org_id, property_ids, start_date=None, end_date=None) -> dict:
    """Org/scope-wide Net Operating Income plus a per-property breakdown.
    NOI = collected income − paid operating expenses (cash basis)."""
    by_property = profit_by_property(
        db, org_id=org_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )
    total_income = round(sum(r["income"] for r in by_property), 2)
    total_expenses = round(sum(r["expenses"] for r in by_property), 2)

    return {
        "total_income": total_income,
        "total_operating_expenses": total_expenses,
        "noi": round(total_income - total_expenses, 2),
        "by_property": [
            {
                "property_id": r["property_id"],
                "property_name": r["property_name"],
                "income": r["income"],
                "expenses": r["expenses"],
                "noi": r["profit"],
            }
            for r in by_property
        ],
    }