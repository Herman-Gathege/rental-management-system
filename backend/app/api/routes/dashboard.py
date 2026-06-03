# backend/app/api/routes/dashboard.py
"""
Role-based dashboard endpoints (Sprint 4.5).

Each role gets its own slice of data:
  - PROPERTY_MANAGER   -> /dashboard/manager/*   (their assigned properties)
  - FINANCE / LANDLORD -> /dashboard/finance/*   (org-wide money)
  - TENANT             -> /dashboard/tenant/*    (their own records)

Authz lives here; the queries live in dashboard_service. We resolve the
caller's organization + role from their OrganizationMember row -- the same
authoritative, org-scoped role source organizations.py uses -- and reject
anyone whose role isn't allowed for the endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT
from app.schemas.dashboard import (
    ManagerSummaryResponse,
    FinanceSummaryResponse,
    TenantDashboardResponse,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _membership(db: Session, user: User) -> OrganizationMember:
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def _require(membership: OrganizationMember, *allowed_roles: str) -> None:
    role = membership.role.name if membership.role else None
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Access denied")


# ─── Property Manager ───

@router.get("/manager/summary", response_model=ManagerSummaryResponse)
def manager_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, PROPERTY_MANAGER)
    return dashboard_service.get_manager_summary(
        db, current_user.id, membership.organization_id
    )


@router.get("/manager/properties")
def manager_properties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, PROPERTY_MANAGER)
    return dashboard_service.get_manager_properties(
        db, current_user.id, membership.organization_id
    )


# ─── Finance (and Landlord, who can see everything) ───

@router.get("/finance/summary", response_model=FinanceSummaryResponse)
def finance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, FINANCE, LANDLORD)
    return dashboard_service.get_finance_summary(db, membership.organization_id)


@router.get("/finance/recent-payments")
def finance_recent_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, FINANCE, LANDLORD)
    return dashboard_service.get_finance_recent_payments(
        db, membership.organization_id
    )


# ─── Tenant ───

@router.get("/tenant/me", response_model=TenantDashboardResponse)
def tenant_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, TENANT)
    return dashboard_service.get_tenant_dashboard(
        db, current_user.id, membership.organization_id
    )


@router.get("/tenant/payments")
def tenant_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, TENANT)
    return dashboard_service.get_tenant_payments(
        db, current_user.id, membership.organization_id
    )


@router.get("/tenant/charges")
def tenant_charges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require(membership, TENANT)
    return dashboard_service.get_tenant_charges(
        db, current_user.id, membership.organization_id
    )