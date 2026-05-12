from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.schemas.rental import TenantCreate, TenantUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_user_org(user, db):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def tenant_dict(t):
    return {"id": t.id, "organization_id": t.organization_id, "full_name": t.full_name, "email": t.email, "phone": t.phone, "id_number": t.id_number, "emergency_contact": t.emergency_contact, "created_at": t.created_at}


@router.post("/")
def create_tenant(payload: TenantCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    tenant = Tenant(id=str(uuid.uuid4()), organization_id=membership.organization_id, full_name=payload.full_name, email=payload.email, phone=payload.phone, id_number=payload.id_number, emergency_contact=payload.emergency_contact)
    db.add(tenant)
    db.flush()
    log_action(db, membership.organization_id, current_user.id, "create", "tenant", tenant.id, f"Created tenant: {payload.full_name}", new_values={"full_name": payload.full_name, "phone": payload.phone})
    db.commit()
    db.refresh(tenant)
    return tenant_dict(tenant)


@router.get("/")
def list_tenants(search: str = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    query = db.query(Tenant).filter(Tenant.organization_id == membership.organization_id)
    if search:
        s = f"%{search}%"
        query = query.filter((Tenant.full_name.ilike(s)) | (Tenant.phone.ilike(s)) | (Tenant.id_number.ilike(s)) | (Tenant.email.ilike(s)))
    return [tenant_dict(t) for t in query.order_by(Tenant.created_at.desc()).all()]


@router.get("/{tenant_id}")
def get_tenant(tenant_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.organization_id == membership.organization_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_dict(tenant)


@router.put("/{tenant_id}")
def update_tenant(tenant_id: str, payload: TenantUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.organization_id == membership.organization_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    old_values = {"full_name": tenant.full_name, "phone": tenant.phone, "email": tenant.email, "id_number": tenant.id_number, "emergency_contact": tenant.emergency_contact}
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    log_action(db, membership.organization_id, current_user.id, "update", "tenant", tenant.id, f"Updated tenant: {tenant.full_name}", old_values=old_values, new_values=update_data)
    db.commit()
    db.refresh(tenant)
    return tenant_dict(tenant)


@router.delete("/{tenant_id}")
def delete_tenant(tenant_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.organization_id == membership.organization_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    from app.models.lease import Lease
    active = db.query(Lease).filter(Lease.tenant_id == tenant_id, Lease.status == "active").first()
    if active:
        raise HTTPException(status_code=400, detail="Cannot delete tenant with an active lease")
    log_action(db, membership.organization_id, current_user.id, "delete", "tenant", tenant.id, f"Deleted tenant: {tenant.full_name}")
    db.delete(tenant)
    db.commit()
    return {"message": "Tenant deleted"}