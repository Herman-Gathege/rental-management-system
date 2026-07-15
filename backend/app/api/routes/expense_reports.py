#backend\app\api\routes\expense_reports.py
import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.services import expense_report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def _scope(db: Session, current_user: User, membership: OrganizationMember, property_id: str):
    """Resolve the role scope and apply an optional single-property filter."""
    scope = expense_report_service.resolve_scope(db, current_user, membership)
    return expense_report_service.narrow_scope(scope, property_id)


def _csv_response(rows: list, columns: list, filename: str) -> StreamingResponse:
    """Stream a list[dict] as a CSV download.
    columns = list of (dict_key, header_label) tuples in output order."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([label for _key, label in columns])
    for r in rows:
        writer.writerow([r.get(key, "") for key, _label in columns])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Expense reports ───

@router.get("/expenses/summary")
def expenses_summary(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.expense_summary(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


@router.get("/expenses/by-category")
def expenses_by_category(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.expenses_by_category(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


@router.get("/expenses/by-vendor")
def expenses_by_vendor(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.expenses_by_vendor(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


@router.get("/expenses/monthly")
def monthly_expenses(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.monthly_expenses(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


# ─── Profitability ───

@router.get("/profit-by-property")
def profit_by_property(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.profit_by_property(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


@router.get("/noi")
def noi(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.noi_summary(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


# ═══════════════════════════════════════════════════════════════════════
# Sprint 6.2 (#1) — Landlord reports (JSON + CSV)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/rent-roll")
def rent_roll(
    property_id: str = Query(None),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)

    return expense_report_service.rent_roll(
        db,
        org_id=membership.organization_id,
        property_ids=property_ids,
        active_only=active_only,
    )


@router.get("/rent-roll/csv")
def rent_roll_csv(
    property_id: str = Query(None),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)

    rows = expense_report_service.rent_roll(
        db,
        org_id=membership.organization_id,
        property_ids=property_ids,
        active_only=active_only,
    )

    columns = [
        ("tenant_name", "Tenant"),
        ("property_unit", "Property / Unit"),
        ("monthly_rent", "Monthly Rent"),
        ("deposit_held", "Deposit Held"),
        ("balance", "Balance"),
        ("balance_status", "Balance Status"),
        ("status", "Status"),
        ("lease_period", "Lease Period"),
    ]

    return _csv_response(rows, columns, "rent_roll.csv")

@router.get("/collection")
def collection(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.collection_report(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


@router.get("/collection/csv")
def collection_csv(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    rows = expense_report_service.collection_report(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )
    columns = [
        ("property_name", "Property"), ("expected_rent", "Expected Rent"),
        ("collected", "Collected"), ("outstanding", "Outstanding"),
        ("collection_rate", "Collection Rate %"),
    ]
    return _csv_response(rows, columns, "collection_report.csv")


@router.get("/vendor")
def vendor(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    return expense_report_service.vendor_report(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )


@router.get("/vendor/csv")
def vendor_csv(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    rows = expense_report_service.vendor_report(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )
    columns = [
        ("vendor_name", "Vendor"), ("invoices", "Invoices"),
        ("total_billed", "Total Billed"), ("total_paid", "Total Paid"),
        ("outstanding", "Outstanding"), ("average_cost", "Average Cost"),
    ]
    return _csv_response(rows, columns, "vendor_report.csv")


@router.get("/profit-by-property/csv")
def profit_by_property_csv(
    property_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    property_ids = _scope(db, current_user, membership, property_id)
    rows = expense_report_service.profit_by_property(
        db, org_id=membership.organization_id, property_ids=property_ids,
        start_date=start_date, end_date=end_date,
    )
    columns = [
        ("property_name", "Property"), ("income", "Income"),
        ("expenses", "Expenses"), ("profit", "Profit (NOI)"),
    ]
    return _csv_response(rows, columns, "profit_by_property.csv")
