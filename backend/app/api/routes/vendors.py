#backend\app\api\routes\vendors.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate
from app.services import vendor_service

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def vendor_dict(v: Vendor) -> dict:
    return {
        "id": v.id,
        "organization_id": v.organization_id,
        "vendor_name": v.vendor_name,
        "contact_person": v.contact_person,
        "phone": v.phone,
        "email": v.email,
        "kra_pin": v.kra_pin,
        "address": v.address,
        "notes": v.notes,
        "created_at": v.created_at,
    }


@router.get("/")
def list_vendors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    vendors = vendor_service.list_vendors(db, membership)
    return [vendor_dict(v) for v in vendors]


@router.post("/")
def create_vendor(
    payload: VendorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    vendor = vendor_service.create_vendor(db, current_user, membership, payload)
    return vendor_dict(vendor)


@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: str,
    payload: VendorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    vendor = vendor_service.update_vendor(db, current_user, membership, vendor_id, payload)
    return vendor_dict(vendor)


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    vendor_service.delete_vendor(db, current_user, membership, vendor_id)
    return {"message": "Vendor deleted"}
