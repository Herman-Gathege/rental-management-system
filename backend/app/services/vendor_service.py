#backend\app\services\vendor_service.py
"""
Vendor business logic (Sprint 5).

Landlord/Finance manage vendors; Property Managers may read them (to populate
the vendor dropdown when creating an expense); tenants have no access.

Vendors CAN be hard-deleted: expenses.vendor_id is ON DELETE SET NULL, so
deleting a vendor simply detaches it from any expenses (the expense record and
its amount are preserved).
"""
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.vendor import Vendor
from app.core.roles import LANDLORD, PROPERTY_MANAGER, FINANCE
from app.services.audit_service import log_action

FULL_ACCESS_ROLES = {LANDLORD, FINANCE}


def _role(membership: OrganizationMember) -> str:
    return membership.role.name if membership.role else None


def _assert_can_read(membership: OrganizationMember):
    if _role(membership) not in FULL_ACCESS_ROLES and _role(membership) != PROPERTY_MANAGER:
        raise HTTPException(status_code=403, detail="You do not have access to vendors")


def _assert_can_manage(membership: OrganizationMember):
    if _role(membership) not in FULL_ACCESS_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only a landlord or finance user can manage vendors",
        )


def _get_org_vendor(db: Session, org_id: str, vendor_id: str) -> Vendor:
    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id, Vendor.organization_id == org_id)
        .first()
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


def list_vendors(db: Session, membership: OrganizationMember) -> list:
    _assert_can_read(membership)
    return (
        db.query(Vendor)
        .filter(Vendor.organization_id == membership.organization_id)
        .order_by(Vendor.vendor_name.asc())
        .all()
    )


def create_vendor(db: Session, current_user: User, membership: OrganizationMember, payload) -> Vendor:
    _assert_can_manage(membership)
    org_id = membership.organization_id

    name = (payload.vendor_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Vendor name is required")

    vendor = Vendor(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        vendor_name=name,
        contact_person=payload.contact_person,
        phone=payload.phone,
        email=payload.email,
        kra_pin=payload.kra_pin,
        address=payload.address,
        notes=payload.notes,
    )
    db.add(vendor)
    db.flush()

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="create", entity_type="vendor", entity_id=vendor.id,
        description=f"Created vendor: {name}",
        new_values={"vendor_name": name},
    )

    db.commit()
    db.refresh(vendor)
    return vendor


def update_vendor(db: Session, current_user: User, membership: OrganizationMember, vendor_id: str, payload) -> Vendor:
    _assert_can_manage(membership)
    org_id = membership.organization_id
    vendor = _get_org_vendor(db, org_id, vendor_id)

    data = payload.dict(exclude_unset=True)
    if "vendor_name" in data:
        new_name = (data["vendor_name"] or "").strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Vendor name cannot be empty")
        data["vendor_name"] = new_name

    old_values = {"vendor_name": vendor.vendor_name}

    for key, value in data.items():
        setattr(vendor, key, value)

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="update", entity_type="vendor", entity_id=vendor.id,
        description=f"Updated vendor: {vendor.vendor_name}",
        old_values=old_values, new_values={k: str(v) for k, v in data.items()},
    )

    db.commit()
    db.refresh(vendor)
    return vendor


def delete_vendor(db: Session, current_user: User, membership: OrganizationMember, vendor_id: str):
    _assert_can_manage(membership)
    org_id = membership.organization_id
    vendor = _get_org_vendor(db, org_id, vendor_id)

    log_action(
        db=db, organization_id=org_id, user_id=current_user.id,
        action="delete", entity_type="vendor", entity_id=vendor.id,
        description=f"Deleted vendor: {vendor.vendor_name}",
        old_values={"vendor_name": vendor.vendor_name},
    )

    # expenses.vendor_id is ON DELETE SET NULL, so any linked expenses keep
    # their record and simply lose the vendor reference.
    db.delete(vendor)
    db.commit()
