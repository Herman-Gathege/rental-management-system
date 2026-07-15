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

Sprint 6.2 (#1) landlord reports: rent_roll, collection_report, vendor_report
added at the bottom. These count RENT ONLY for collected/expected figures
(Payment.payment_type == "rent", Charge.charge_type == "rent") to stay
consistent with the deposit split from #7.
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
from app.models.tenant import Tenant
from app.models.charge import Charge
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
    payment -> lease -> unit -> property. RENT payments only (Sprint 6.2 #7)."""
    query = (
        db.query(Property.id, func.coalesce(func.sum(Payment.amount), 0))
        .join(Unit, Unit.property_id == Property.id)
        .join(Lease, Lease.unit_id == Unit.id)
        .join(Payment, Payment.lease_id == Lease.id)
        .filter(Property.organization_id == org_id, Payment.payment_type == "rent")
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


# ═══════════════════════════════════════════════════════════════════════
# Sprint 6.2 (#1) — Landlord financial reports
# ═══════════════════════════════════════════════════════════════════════

def _scope_lease_ids(db, org_id, property_ids):
    """Active-and-any lease ids within scope. Returns None for org-wide so
    callers can skip the .in_() filter entirely."""
    if property_ids is None:
        return None
    if len(property_ids) == 0:
        return []
    rows = (
        db.query(Lease.id)
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Unit.property_id.in_(property_ids))
        .all()
    )
    return [r[0] for r in rows]


# def rent_roll(db, *, org_id, property_ids, active_only=True) -> list:
#     """
#     Rent roll — one row per lease (active by default): tenant, property, unit,
#     monthly rent, deposit held (deposit-type payments), current rent balance,
#     and status.

#     balance = rent charges - rent payments (rent-type only, so the deposit is
#     excluded from the rent balance and shown in its own column instead).
#     """
#     if property_ids is not None and len(property_ids) == 0:
#         return []

#     q = (
#         db.query(Lease, Tenant, Property, Unit)
#         .join(Unit, Unit.id == Lease.unit_id)
#         .join(Property, Property.id == Unit.property_id)
#         .outerjoin(Tenant, Tenant.id == Lease.tenant_id)
#         .filter(Lease.organization_id == org_id)
#     )
#     if property_ids is not None:
#         q = q.filter(Unit.property_id.in_(property_ids))
#     # if active_only:
#     #     q = q.filter(Lease.status == "active")
#     if active_only:
#           q = q.filter(Lease.status.in_(["active", "terminated"]))
#     q = q.order_by(Property.name.asc(), Unit.name.asc())
#     rows = q.all()

#     lease_ids = [l.id for l, _t, _p, _u in rows]
#     rent_charge_map = {}
#     rent_paid_map = {}
#     deposit_paid_map = {}
#     if lease_ids:
#         for lid, total in (
#             db.query(Charge.lease_id, func.coalesce(func.sum(Charge.amount), 0))
#             .filter(Charge.lease_id.in_(lease_ids), Charge.charge_type == "rent")
#             .group_by(Charge.lease_id).all()
#         ):
#             rent_charge_map[lid] = float(total)
#         for lid, total in (
#             db.query(Payment.lease_id, func.coalesce(func.sum(Payment.amount), 0))
#             .filter(Payment.lease_id.in_(lease_ids), Payment.payment_type == "rent")
#             .group_by(Payment.lease_id).all()
#         ):
#             rent_paid_map[lid] = float(total)
#         for lid, total in (
#             db.query(Payment.lease_id, func.coalesce(func.sum(Payment.amount), 0))
#             .filter(Payment.lease_id.in_(lease_ids), Payment.payment_type == "deposit")
#             .group_by(Payment.lease_id).all()
#         ):
#             deposit_paid_map[lid] = float(total)

#     result = []
#     for lease, tenant, prop, unit in rows:
#         rent_charged = rent_charge_map.get(lease.id, 0.0)
#         rent_paid = rent_paid_map.get(lease.id, 0.0)
#         balance = round(rent_charged - rent_paid, 2)
#         result.append({
#             "lease_id": lease.id,
#             "tenant_name": tenant.full_name if tenant else None,
#             "property_name": prop.name,
#             "unit_name": unit.name,
#             "monthly_rent": float(lease.rent_amount) if lease.rent_amount is not None else 0.0,
#             # "deposit_held": round(deposit_paid_map.get(lease.id, 0.0), 2),
#             "deposit_held": float(lease.deposit_amount or 0),
#             "balance": balance,
#             "status": lease.status,
#             "start_date": lease.start_date.isoformat() if lease.start_date else None,
#             "end_date": lease.end_date.isoformat() if lease.end_date else None,
#         })
#     return result


def rent_roll(db, *, org_id, property_ids, active_only=True) -> list:
    """
    Rent Roll Report

    Returns one row per lease within the selected scope.

    Includes:
      • Tenant
      • Property
      • Unit
      • Property/Unit display
      • Monthly rent
      • Deposit currently held
      • Rent balance
      • Balance status
      • Lease status
      • Active flag
      • Lease dates
      • Human-readable lease period

    Notes:
      - Rent balance only considers RENT charges/payments.
      - Deposit is displayed separately.
      - Terminated leases are assumed to have no deposit held.
    """

    if property_ids is not None and len(property_ids) == 0:
        return []

    # ------------------------------------------------------------------
    # Lease query
    # ------------------------------------------------------------------
    q = (
        db.query(Lease, Tenant, Property, Unit)
        .join(Unit, Unit.id == Lease.unit_id)
        .join(Property, Property.id == Unit.property_id)
        .outerjoin(Tenant, Tenant.id == Lease.tenant_id)
        .filter(Lease.organization_id == org_id)
    )

    if property_ids is not None:
        q = q.filter(Unit.property_id.in_(property_ids))

    # Active report includes active and terminated leases
    if active_only:
        q = q.filter(Lease.status.in_(["active", "terminated"]))

    q = q.order_by(
        Property.name.asc(),
        Unit.name.asc(),
        Lease.start_date.desc(),
    )

    rows = q.all()

    lease_ids = [lease.id for lease, _, _, _ in rows]

    # ------------------------------------------------------------------
    # Rent totals
    # ------------------------------------------------------------------
    rent_charge_map = {}
    rent_paid_map = {}

    if lease_ids:

        # Total rent charged
        for lease_id, total in (
            db.query(
                Charge.lease_id,
                func.coalesce(func.sum(Charge.amount), 0),
            )
            .filter(
                Charge.lease_id.in_(lease_ids),
                Charge.charge_type == "rent",
            )
            .group_by(Charge.lease_id)
            .all()
        ):
            rent_charge_map[lease_id] = float(total)

        # Total rent paid
        for lease_id, total in (
            db.query(
                Payment.lease_id,
                func.coalesce(func.sum(Payment.amount), 0),
            )
            .filter(
                Payment.lease_id.in_(lease_ids),
                Payment.payment_type == "rent",
            )
            .group_by(Payment.lease_id)
            .all()
        ):
            rent_paid_map[lease_id] = float(total)

    # ------------------------------------------------------------------
    # Build response
    # ------------------------------------------------------------------
    result = []

    for lease, tenant, prop, unit in rows:

        rent_charged = rent_charge_map.get(lease.id, 0.0)
        rent_paid = rent_paid_map.get(lease.id, 0.0)

        balance = round(rent_charged - rent_paid, 2)

        status = (lease.status or "").lower()

        # Deposit currently held
        deposit_held = (
            0.0
            if status == "terminated"
            else float(lease.deposit_amount or 0)
        )

        # Balance meaning
        if balance > 0:
            balance_status = "outstanding"
        elif balance < 0:
            balance_status = "credit"
        else:
            balance_status = "settled"

        # Display status
        status_display = {
            "active": "Active",
            "terminated": "Terminated",
            "pending": "Pending",
            "ended": "Ended",
        }.get(status, status.title())

        # Lease period
        start = (
            lease.start_date.strftime("%b %Y")
            if lease.start_date
            else "Unknown"
        )

        end = (
            lease.end_date.strftime("%b %Y")
            if lease.end_date
            else "Present"
        )

        lease_period = f"{start} - {end}"

        result.append(
            {
                "lease_id": lease.id,

                # Tenant
                "tenant_name": tenant.full_name if tenant else "Vacant",

                # Property
                "property_name": prop.name,
                "unit_name": unit.name,
                "property_unit": f"{prop.name} • {unit.name}",

                # Financials
                "monthly_rent": float(lease.rent_amount or 0),
                "deposit_held": deposit_held,
                "balance": balance,
                "balance_status": balance_status,

                # Status
                "status": status_display,
                "is_active": status == "active",

                # Dates
                "lease_start": (
                    lease.start_date.isoformat()
                    if lease.start_date
                    else None
                ),
                "lease_end": (
                    lease.end_date.isoformat()
                    if lease.end_date
                    else None
                ),
                "lease_period": lease_period,
            }
        )

    return result


def collection_report(db, *, org_id, property_ids, start_date=None, end_date=None) -> list:
    """
    Per-property rent collection: expected rent (active leases' monthly rent),
    collected (rent payments in the date range), outstanding (rent charged −
    rent paid, all-time), and a collection rate %.

    Note: 'expected' is the monthly rent run-rate (sum of active leases), while
    'collected' respects the date filter — this mirrors how the dashboards frame
    it. Outstanding is the true all-time rent balance per property.
    """
    if property_ids is not None and len(property_ids) == 0:
        return []

    properties = _scope_properties(db, org_id, property_ids)
    if not properties:
        return []
    prop_ids = [p.id for p in properties]

    # Expected = sum of active-lease monthly rent per property.
    expected_map = {}
    for pid, total in (
        db.query(Unit.property_id, func.coalesce(func.sum(Lease.rent_amount), 0))
        .join(Lease, Lease.unit_id == Unit.id)
        .filter(Unit.property_id.in_(prop_ids), Lease.status == "active")
        .group_by(Unit.property_id).all()
    ):
        expected_map[pid] = float(total)

    # Collected = rent payments (date-filtered) per property.
    collected_q = (
        db.query(Unit.property_id, func.coalesce(func.sum(Payment.amount), 0))
        .join(Lease, Lease.unit_id == Unit.id)
        .join(Payment, Payment.lease_id == Lease.id)
        .filter(Unit.property_id.in_(prop_ids), Payment.payment_type == "rent")
    )
    if start_date:
        collected_q = collected_q.filter(Payment.payment_date >= start_date)
    if end_date:
        collected_q = collected_q.filter(Payment.payment_date <= end_date)
    collected_map = {
        pid: float(total)
        for pid, total in collected_q.group_by(Unit.property_id).all()
    }

    # Outstanding = all-time rent charged − rent paid per property.
    charged_map = {
        pid: float(total)
        for pid, total in (
            db.query(Unit.property_id, func.coalesce(func.sum(Charge.amount), 0))
            .join(Lease, Lease.unit_id == Unit.id)
            .join(Charge, Charge.lease_id == Lease.id)
            .filter(Unit.property_id.in_(prop_ids), Charge.charge_type == "rent")
            .group_by(Unit.property_id).all()
        )
    }
    paid_all_map = {
        pid: float(total)
        for pid, total in (
            db.query(Unit.property_id, func.coalesce(func.sum(Payment.amount), 0))
            .join(Lease, Lease.unit_id == Unit.id)
            .join(Payment, Payment.lease_id == Lease.id)
            .filter(Unit.property_id.in_(prop_ids), Payment.payment_type == "rent")
            .group_by(Unit.property_id).all()
        )
    }

    result = []
    for p in properties:
        expected = round(expected_map.get(p.id, 0.0), 2)
        collected = round(collected_map.get(p.id, 0.0), 2)
        outstanding = round(charged_map.get(p.id, 0.0) - paid_all_map.get(p.id, 0.0), 2)
        rate = round((collected / expected * 100), 1) if expected > 0 else 0.0
        result.append({
            "property_id": p.id,
            "property_name": p.name,
            "expected_rent": expected,
            "collected": collected,
            "outstanding": outstanding,
            "collection_rate": rate,
        })
    return result


def vendor_report(db, *, org_id, property_ids, start_date=None, end_date=None) -> list:
    """
    Per-vendor spend: number of expenses (invoices), total billed (all non-draft
    expenses), total paid (status paid), outstanding (billed − paid), and average
    cost per expense. Ordered by total billed, largest first.
    """
    if property_ids is not None and len(property_ids) == 0:
        return []

    # Billed = all expenses with a vendor that are past draft (submitted,
    # approved, or paid). Paid = subset with status paid.
    def _sum(status=None, count=False):
        col = func.count(Expense.id) if count else func.coalesce(func.sum(Expense.amount), 0)
        q = db.query(Vendor.id, Vendor.vendor_name, col).join(Expense, Expense.vendor_id == Vendor.id)
        q = q.filter(Expense.organization_id == org_id)
        if status is not None:
            q = q.filter(Expense.status == status)
        else:
            q = q.filter(Expense.status != STATUS_DRAFT)
        if property_ids is not None:
            q = q.filter(Expense.property_id.in_(property_ids))
        if start_date:
            q = q.filter(Expense.expense_date >= start_date)
        if end_date:
            q = q.filter(Expense.expense_date <= end_date)
        return q.group_by(Vendor.id, Vendor.vendor_name).all()

    billed_rows = _sum()                       # (vid, name, sum) non-draft
    count_rows = _sum(count=True)              # (vid, name, count) non-draft
    paid_rows = _sum(status=STATUS_PAID)       # (vid, name, sum) paid

    billed_map = {vid: (name, float(total)) for vid, name, total in billed_rows}
    count_map = {vid: int(c) for vid, _n, c in count_rows}
    paid_map = {vid: float(total) for vid, _n, total in paid_rows}

    result = []
    for vid, (name, billed) in billed_map.items():
        paid = paid_map.get(vid, 0.0)
        cnt = count_map.get(vid, 0)
        result.append({
            "vendor_id": vid,
            "vendor_name": name,
            "invoices": cnt,
            "total_billed": round(billed, 2),
            "total_paid": round(paid, 2),
            "outstanding": round(billed - paid, 2),
            "average_cost": round(billed / cnt, 2) if cnt else 0.0,
        })
    result.sort(key=lambda r: r["total_billed"], reverse=True)
    return result
