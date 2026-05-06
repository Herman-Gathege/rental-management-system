#backend\app\api\routes\tenants.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.schemas.rental import TenantCreate, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


# ─── Create Tenant ───

@router.post("/")
def create_tenant(
    payload: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_id=membership.organization_id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        id_number=payload.id_number,
        emergency_contact=payload.emergency_contact,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "organization_id": tenant.organization_id,
        "full_name": tenant.full_name,
        "email": tenant.email,
        "phone": tenant.phone,
        "id_number": tenant.id_number,
        "emergency_contact": tenant.emergency_contact,
        "created_at": tenant.created_at,
    }


# ─── List Tenants ───

@router.get("/")
def list_tenants(
    search: str = Query(None, description="Search by name, phone, or ID number"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(Tenant).filter(
        Tenant.organization_id == membership.organization_id
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Tenant.full_name.ilike(search_term)) |
            (Tenant.phone.ilike(search_term)) |
            (Tenant.id_number.ilike(search_term)) |
            (Tenant.email.ilike(search_term))
        )

    tenants = query.order_by(Tenant.created_at.desc()).all()

    return [
        {
            "id": t.id,
            "organization_id": t.organization_id,
            "full_name": t.full_name,
            "email": t.email,
            "phone": t.phone,
            "id_number": t.id_number,
            "emergency_contact": t.emergency_contact,
            "created_at": t.created_at,
        }
        for t in tenants
    ]


# ─── Get Tenant ───

@router.get("/{tenant_id}")
def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.id == tenant_id,
            Tenant.organization_id == membership.organization_id
        )
        .first()
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "id": tenant.id,
        "organization_id": tenant.organization_id,
        "full_name": tenant.full_name,
        "email": tenant.email,
        "phone": tenant.phone,
        "id_number": tenant.id_number,
        "emergency_contact": tenant.emergency_contact,
        "created_at": tenant.created_at,
    }


# ─── Update Tenant ───

@router.put("/{tenant_id}")
def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.id == tenant_id,
            Tenant.organization_id == membership.organization_id
        )
        .first()
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "organization_id": tenant.organization_id,
        "full_name": tenant.full_name,
        "email": tenant.email,
        "phone": tenant.phone,
        "id_number": tenant.id_number,
        "emergency_contact": tenant.emergency_contact,
        "created_at": tenant.created_at,
    }


# ─── Delete Tenant ───

@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.id == tenant_id,
            Tenant.organization_id == membership.organization_id
        )
        .first()
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check for active leases
    from app.models.lease import Lease
    active_lease = (
        db.query(Lease)
        .filter(Lease.tenant_id == tenant_id, Lease.status == "active")
        .first()
    )
    if active_lease:
        raise HTTPException(status_code=400, detail="Cannot delete tenant with an active lease")

    db.delete(tenant)
    db.commit()

    return {"message": "Tenant deleted"}
