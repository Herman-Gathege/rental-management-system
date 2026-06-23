#backend\app\api\routes\expense_reports.py
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
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