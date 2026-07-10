#backend\app\api\routes\inspections.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import uuid
import json

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.core.file_validation import read_image_upload
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.lease import Lease
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.lease_inspection import LeaseInspection
from app.models.inspection_item import InspectionItem
from app.models.inspection_note import InspectionNote
from app.core.roles import LANDLORD, PROPERTY_MANAGER, TENANT
from app.services.audit_service import log_action
from app.services.s3_service import upload_file

router = APIRouter(prefix="/inspections", tags=["Inspections"])


# ─── Who may fill / sign each inspection type ───
#
# Move-in:  the inspection can be filled and signed by the landlord, a
#           property manager, OR the tenant. Whoever signs it first locks
#           it; after that it is read-only for everyone.
#
# Move-out: filling and signing is restricted to the landlord or a property
#           manager. The tenant must NOT be able to fill a move-out inspection
#           because its deductions come out of the tenant's own deposit
#           (conflict of interest). The tenant can still VIEW it and their
#           signature is captured on the conductor's device.
#
# Viewing (GET endpoints) stays open to any member of the organization.

MOVE_IN_FILL_ROLES = {LANDLORD, PROPERTY_MANAGER, TENANT}
MOVE_OUT_FILL_ROLES = {LANDLORD, PROPERTY_MANAGER}


# ─── Schemas ───

class InspectionItemUpdate(BaseModel):
    condition: Optional[str] = None
    comments: Optional[str] = None
    deduction_amount: Optional[float] = None


class SignInspectionPayload(BaseModel):
    tenant_signed_name: str
    tenant_signature_data: str


class AddNotePayload(BaseModel):
    note: str


# ─── Helpers ───

def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def get_inspection_for_org(inspection_id: str, org_id: str, db: Session) -> LeaseInspection:
    inspection = (
        db.query(LeaseInspection)
        .join(Lease, LeaseInspection.lease_id == Lease.id)
        .filter(
            LeaseInspection.id == inspection_id,
            Lease.organization_id == org_id
        )
        .first()
    )
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


def assert_can_modify(membership: OrganizationMember, inspection: LeaseInspection):
    """
    Enforce who may fill or sign an inspection based on its type.

    Move-in:  landlord, property manager, or tenant.
    Move-out: landlord or property manager only.

    Raises 403 if the current member's role is not permitted. This is the
    backend enforcement of the permission matrix — the frontend hides the
    controls too, but the rule is enforced here so it can't be bypassed
    via the API.
    """
    role = membership.role.name if membership.role else None

    if inspection.inspection_type == "move_out":
        if role not in MOVE_OUT_FILL_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Only the landlord or a property manager can fill or sign a move-out inspection.",
            )
    else:
        if role not in MOVE_IN_FILL_ROLES:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to fill this inspection.",
            )


def item_dict(item: InspectionItem) -> dict:
    try:
        photo_urls = json.loads(item.photo_urls) if item.photo_urls else []
    except (json.JSONDecodeError, TypeError):
        photo_urls = []

    return {
        "id": item.id,
        "inspection_id": item.inspection_id,
        "item_name": item.item_name,
        "sort_order": item.sort_order,
        "condition": item.condition,
        "comments": item.comments,
        "photo_urls": photo_urls,
        "deduction_amount": float(item.deduction_amount) if item.deduction_amount else 0,
        "updated_at": item.updated_at,
    }


def inspection_dict(inspection: LeaseInspection, db: Session) -> dict:
    items = (
        db.query(InspectionItem)
        .filter(InspectionItem.inspection_id == inspection.id)
        .order_by(InspectionItem.sort_order.asc())
        .all()
    )

    notes = (
        db.query(InspectionNote)
        .filter(InspectionNote.inspection_id == inspection.id)
        .order_by(InspectionNote.created_at.asc())
        .all()
    )

    return {
        "id": inspection.id,
        "lease_id": inspection.lease_id,
        "inspection_type": inspection.inspection_type,
        "inspection_date": inspection.inspection_date,
        "inspector_user_id": inspection.inspector_user_id,
        "inspector_email": inspection.inspector.email if inspection.inspector else None,
        "tenant_signature_data": inspection.tenant_signature_data,
        "tenant_signed_name": inspection.tenant_signed_name,
        "tenant_signed_at": inspection.tenant_signed_at,
        "status": inspection.status,
        "total_deduction_amount": float(inspection.total_deduction_amount) if inspection.total_deduction_amount else 0,
        # Deposit settlement (Sprint 6.2 #7 Phase 3) — populated at move-out sign.
        "deposit_held": float(inspection.deposit_held) if inspection.deposit_held is not None else None,
        "deposit_refunded": float(inspection.deposit_refunded) if inspection.deposit_refunded is not None else None,
        "deposit_shortfall": float(inspection.deposit_shortfall) if inspection.deposit_shortfall is not None else None,
        "created_at": inspection.created_at,
        "updated_at": inspection.updated_at,
        "items": [item_dict(i) for i in items],
        "notes": [
            {
                "id": n.id,
                "note": n.note,
                "user_email": n.user.email if n.user else None,
                "created_at": n.created_at,
            }
            for n in notes
        ],
    }


# ─── Get Inspection ───

@router.get("/{inspection_id}")
def get_inspection(
    inspection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)
    return inspection_dict(inspection, db)


# ─── Get Move-In Comparison Data ───
#
# For a move-out inspection, this returns the matching SIGNED move-in
# inspection's items so the frontend can display them side-by-side.
# If no signed move-in inspection exists, returns null (frontend shows
# a warning banner).

@router.get("/{inspection_id}/move-in-comparison")
def get_move_in_comparison(
    inspection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)

    # Only meaningful for move-out inspections
    if inspection.inspection_type != "move_out":
        return {"signed_move_in": None, "items_by_name": {}}

    # Find the signed move-in inspection for this lease
    move_in = (
        db.query(LeaseInspection)
        .filter(
            LeaseInspection.lease_id == inspection.lease_id,
            LeaseInspection.inspection_type == "move_in",
            LeaseInspection.status == "signed"
        )
        .first()
    )

    if not move_in:
        return {"signed_move_in": None, "items_by_name": {}}

    # Pull move-in items and key them by item_name (so they can be matched
    # to move-out items by name — they share the same checklist template)
    move_in_items = (
        db.query(InspectionItem)
        .filter(InspectionItem.inspection_id == move_in.id)
        .all()
    )

    items_by_name = {item.item_name: item_dict(item) for item in move_in_items}

    return {
        "signed_move_in": {
            "id": move_in.id,
            "inspection_date": move_in.inspection_date,
            "tenant_signed_name": move_in.tenant_signed_name,
        },
        "items_by_name": items_by_name,
    }


# ─── Update Inspection Item ───

@router.put("/{inspection_id}/items/{item_id}")
def update_inspection_item(
    inspection_id: str,
    item_id: str,
    payload: InspectionItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)

    # Permission: who is allowed to fill this inspection type?
    assert_can_modify(membership, inspection)

    if inspection.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Inspection is locked. Add a note instead."
        )

    item = (
        db.query(InspectionItem)
        .filter(
            InspectionItem.id == item_id,
            InspectionItem.inspection_id == inspection_id
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inspection item not found")

    valid_conditions = ["working", "faulty", "needs_repair"]
    if payload.condition is not None and payload.condition not in valid_conditions:
        raise HTTPException(
            status_code=400,
            detail=f"condition must be one of: {valid_conditions}"
        )

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    inspection.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return item_dict(item)


# ─── Upload Photo for an Item ───

@router.post("/{inspection_id}/items/{item_id}/photos")
async def upload_item_photo(
    inspection_id: str,
    item_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)

    # Permission: who is allowed to fill this inspection type?
    assert_can_modify(membership, inspection)

    if inspection.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Inspection is locked. Cannot add photos."
        )

    item = (
        db.query(InspectionItem)
        .filter(
            InspectionItem.id == item_id,
            InspectionItem.inspection_id == inspection_id
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inspection item not found")

    try:
        existing_photos = json.loads(item.photo_urls) if item.photo_urls else []
    except (json.JSONDecodeError, TypeError):
        existing_photos = []

    if len(existing_photos) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 photos per item")

    # Sprint 7 follow-up: bounded read + extension + magic-byte + filename
    # sanitization. Images only (jpg/jpeg/png/webp) — inspection evidence is
    # never a PDF. See app/core/file_validation.py.
    validated = await read_image_upload(file)
    s3_key = (
        f"inspection-photos/{inspection_id}/{item_id}/"
        f"{uuid.uuid4()}-{validated.safe_filename}"
    )

    try:
        file_url = upload_file(s3_key, validated.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    existing_photos.append(file_url)
    item.photo_urls = json.dumps(existing_photos)
    inspection.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return item_dict(item)


# ─── Remove a Photo ───

@router.delete("/{inspection_id}/items/{item_id}/photos")
def remove_item_photo(
    inspection_id: str,
    item_id: str,
    url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)

    # Permission: who is allowed to fill this inspection type?
    assert_can_modify(membership, inspection)

    if inspection.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Inspection is locked. Cannot remove photos."
        )

    item = (
        db.query(InspectionItem)
        .filter(
            InspectionItem.id == item_id,
            InspectionItem.inspection_id == inspection_id
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inspection item not found")

    try:
        existing_photos = json.loads(item.photo_urls) if item.photo_urls else []
    except (json.JSONDecodeError, TypeError):
        existing_photos = []

    new_photos = [p for p in existing_photos if p != url]
    item.photo_urls = json.dumps(new_photos)
    inspection.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return item_dict(item)


# ─── Sign Inspection ───
#
# Locks the inspection. For move-out inspections, ALSO terminates the lease
# and computes the deposit reconciliation.

@router.post("/{inspection_id}/sign")
def sign_inspection(
    inspection_id: str,
    payload: SignInspectionPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)

    # Permission: who is allowed to sign this inspection type?
    assert_can_modify(membership, inspection)

    if inspection.status != "draft":
        raise HTTPException(status_code=400, detail="Inspection is already signed")

    if not payload.tenant_signed_name.strip():
        raise HTTPException(status_code=400, detail="Tenant name is required")

    if not payload.tenant_signature_data:
        raise HTTPException(status_code=400, detail="Signature is required")

    # All items must have a condition set
    items = (
        db.query(InspectionItem)
        .filter(InspectionItem.inspection_id == inspection_id)
        .all()
    )
    unset_items = [i for i in items if not i.condition]
    if unset_items:
        raise HTTPException(
            status_code=400,
            detail=f"All items must have a condition set. Missing: {len(unset_items)} item(s)"
        )

    # For move-out: calculate total deductions
    if inspection.inspection_type == "move_out":
        total = sum(float(i.deduction_amount or 0) for i in items)
        inspection.total_deduction_amount = total

    # Lock the inspection
    inspection.status = "signed"
    inspection.tenant_signed_name = payload.tenant_signed_name.strip()
    inspection.tenant_signature_data = payload.tenant_signature_data
    inspection.tenant_signed_at = datetime.utcnow()
    inspection.inspection_date = date.today()
    inspection.updated_at = datetime.utcnow()

    # ─── If this is a move-out, also terminate the lease + settle deposit ───
    lease_terminated = False
    if inspection.inspection_type == "move_out":
        lease = db.query(Lease).filter(Lease.id == inspection.lease_id).first()
        if lease and lease.status == "active":
            lease.status = "terminated"
            lease_terminated = True

            log_action(
                db=db,
                organization_id=membership.organization_id,
                user_id=current_user.id,
                action="terminate",
                entity_type="lease",
                entity_id=lease.id,
                description=f"Lease terminated via signed move-out inspection",
                old_values={"status": "active"},
                new_values={"status": "terminated"},
            )

        # ─── Deposit reconciliation (Sprint 6.2 #7 Phase 3) ───
        # deposit_held = total deposit-type payments made on this lease.
        # refund = max(held - deductions, 0); shortfall = max(deductions - held, 0).
        # If there's a shortfall (damages exceed the deposit), auto-create a
        # rent-type charge for the difference so it lands on the tenant's balance
        # and flows through outstanding / overdue like any other receivable.
        deductions = float(inspection.total_deduction_amount or 0)
        deposit_held = float(
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(
                Payment.lease_id == inspection.lease_id,
                Payment.payment_type == "deposit",
            )
            .scalar()
        )
        refunded = max(deposit_held - deductions, 0.0)
        shortfall = max(deductions - deposit_held, 0.0)

        inspection.deposit_held = deposit_held
        inspection.deposit_refunded = refunded
        inspection.deposit_shortfall = shortfall

        if shortfall > 0 and lease:
            today = date.today()
            shortfall_charge = Charge(
                id=str(uuid.uuid4()),
                organization_id=membership.organization_id,
                lease_id=lease.id,
                amount=shortfall,
                amount_paid=0,
                charge_type="rent",   # a real receivable — counts toward outstanding
                due_date=today,
                billing_month=today,
                status="pending",
            )
            db.add(shortfall_charge)
            log_action(
                db=db,
                organization_id=membership.organization_id,
                user_id=current_user.id,
                action="billing",
                entity_type="charge",
                entity_id=shortfall_charge.id,
                description=(
                    f"Move-out damages ({deductions}) exceeded deposit held "
                    f"({deposit_held}); billed shortfall of {shortfall} to tenant"
                ),
                new_values={"amount": shortfall, "reason": "deposit_shortfall"},
            )

    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="update",
        entity_type="inspection",
        entity_id=inspection.id,
        description=f"Signed {inspection.inspection_type} inspection for lease {inspection.lease_id}"
                    + (" — lease terminated" if lease_terminated else ""),
        new_values={
            "tenant_signed_name": payload.tenant_signed_name,
            "type": inspection.inspection_type,
            "lease_terminated": lease_terminated,
        },
    )

    db.commit()
    db.refresh(inspection)

    return inspection_dict(inspection, db)


# ─── Add Note (post-signature) ───
#
# Notes are append-only annotations and do not alter the checklist or its
# deductions, so they remain open to any organization member (a tenant can
# record a dispute, etc.) regardless of inspection type.

@router.post("/{inspection_id}/notes")
def add_inspection_note(
    inspection_id: str,
    payload: AddNotePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    inspection = get_inspection_for_org(inspection_id, membership.organization_id, db)

    if not payload.note.strip():
        raise HTTPException(status_code=400, detail="Note cannot be empty")

    note = InspectionNote(
        id=str(uuid.uuid4()),
        inspection_id=inspection_id,
        user_id=current_user.id,
        note=payload.note.strip(),
    )
    db.add(note)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="create",
        entity_type="inspection_note",
        entity_id=note.id,
        description=f"Added note to inspection {inspection_id}",
        new_values={"note": payload.note[:200]},
    )

    db.commit()
    db.refresh(note)

    return {
        "id": note.id,
        "inspection_id": note.inspection_id,
        "note": note.note,
        "user_email": current_user.email,
        "created_at": note.created_at,
    }