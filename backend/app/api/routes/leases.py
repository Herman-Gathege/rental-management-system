from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.property import Property
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.lease_inspection import LeaseInspection
from app.schemas.rental import LeaseCreate, LeaseUpdate
from app.services.audit_service import log_action
from app.services.inspection_service import create_inspection_for_lease
from app.services.s3_service import upload_file

router = APIRouter(prefix="/leases", tags=["Leases"])


def get_user_org(user: User, db: Session):
    """Helper: get the current user's org membership or raise 403."""
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def enrich_lease(lease, db):
    """Add tenant_name, unit_name, property_name + inspection summary to lease response."""
    tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
    prop = db.query(Property).filter(Property.id == unit.property_id).first() if unit else None

    # Summarize inspections for this lease
    inspections = (
        db.query(LeaseInspection)
        .filter(LeaseInspection.lease_id == lease.id)
        .all()
    )

    move_in_inspection = next((i for i in inspections if i.inspection_type == "move_in"), None)
    move_out_inspection = next((i for i in inspections if i.inspection_type == "move_out"), None)

    return {
        "id": lease.id,
        "organization_id": lease.organization_id,
        "unit_id": lease.unit_id,
        "tenant_id": lease.tenant_id,
        "start_date": lease.start_date,
        "end_date": lease.end_date,
        "move_in_date": lease.move_in_date,
        "rent_amount": float(lease.rent_amount),
        "deposit_amount": float(lease.deposit_amount) if lease.deposit_amount else 0,
        "billing_day": lease.billing_day,
        "signed_on_behalf_of": lease.signed_on_behalf_of,
        # "signed_lease_url": lease.signed_lease_url,
        "signed_lease_urls": lease.signed_lease_urls or [],
        "status": lease.status,
        "created_at": lease.created_at,
        "tenant_name": tenant.full_name if tenant else None,
        "unit_name": unit.name if unit else None,
        "property_name": prop.name if prop else None,
        "move_in_inspection": {
            "id": move_in_inspection.id,
            "status": move_in_inspection.status,
            "inspection_date": move_in_inspection.inspection_date,
        } if move_in_inspection else None,
        "move_out_inspection": {
            "id": move_out_inspection.id,
            "status": move_out_inspection.status,
            "inspection_date": move_out_inspection.inspection_date,
        } if move_out_inspection else None,
    }


# ─── Create Lease ───

@router.post("/")
def create_lease(
    payload: LeaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id

    # Verify unit belongs to this org
    unit = (
        db.query(Unit)
        .join(Property, Unit.property_id == Property.id)
        .filter(
            Unit.id == payload.unit_id,
            Property.organization_id == org_id
        )
        .first()
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Verify tenant belongs to this org
    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.id == payload.tenant_id,
            Tenant.organization_id == org_id
        )
        .first()
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check unit doesn't already have an active lease
    existing = (
        db.query(Lease)
        .filter(Lease.unit_id == payload.unit_id, Lease.status == "active")
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Unit already has an active lease")

    # Create the lease
    lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        unit_id=payload.unit_id,
        tenant_id=payload.tenant_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        move_in_date=payload.move_in_date or payload.start_date,
        rent_amount=payload.rent_amount,
        deposit_amount=payload.deposit_amount or 0,
        billing_day=payload.billing_day or 1,
        signed_on_behalf_of=payload.signed_on_behalf_of,
        status="active",
    )
    db.add(lease)
    db.flush()

    # Auto-create draft move-in inspection
    inspection = create_inspection_for_lease(
        db=db,
        lease_id=lease.id,
        organization_id=org_id,
        inspection_type="move_in",
        inspector_user_id=current_user.id,
    )

    # Audit log
    log_action(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        action="create",
        entity_type="lease",
        entity_id=lease.id,
        description=f"Created lease: {tenant.full_name} → {unit.name}",
        new_values={
            "tenant": tenant.full_name,
            "unit": unit.name,
            "rent_amount": payload.rent_amount,
            "start_date": str(payload.start_date),
            "auto_created_inspection_id": inspection.id,
        },
    )

    db.commit()
    db.refresh(lease)

    return enrich_lease(lease, db)


# ─── List Leases ───

@router.get("/")
def list_leases(
    status: str = Query(None, description="Filter by status: active, ended, terminated"),
    property_id: str = Query(None, description="Filter by property"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(Lease).filter(
        Lease.organization_id == membership.organization_id
    )

    if status:
        query = query.filter(Lease.status == status)

    if property_id:
        unit_ids = (
            db.query(Unit.id)
            .filter(Unit.property_id == property_id)
            .subquery()
        )
        query = query.filter(Lease.unit_id.in_(unit_ids))

    leases = query.order_by(Lease.created_at.desc()).all()

    return [enrich_lease(l, db) for l in leases]


# ─── Get Lease ───

@router.get("/{lease_id}")
def get_lease(
    lease_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    return enrich_lease(lease, db)


# ─── Update Lease ───

@router.put("/{lease_id}")
def update_lease(
    lease_id: str,
    payload: LeaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if lease.status != "active":
        raise HTTPException(status_code=400, detail="Can only update active leases")

    old_values = {
        "rent_amount": float(lease.rent_amount),
        "end_date": str(lease.end_date),
        "billing_day": lease.billing_day,
        "move_in_date": str(lease.move_in_date) if lease.move_in_date else None,
        "signed_on_behalf_of": lease.signed_on_behalf_of,
    }

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lease, key, value)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="update",
        entity_type="lease",
        entity_id=lease.id,
        description=f"Updated lease {lease.id}",
        old_values=old_values,
        new_values={k: str(v) for k, v in update_data.items()},
    )

    db.commit()
    db.refresh(lease)

    return enrich_lease(lease, db)


# ─── Initiate Move-Out ───
#
# This is the new entry point that replaces direct termination.
# It creates a draft move-out inspection that must be completed
# and signed before the lease can be terminated.

@router.post("/{lease_id}/initiate-move-out")
def initiate_move_out(
    lease_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start the move-out process by creating a draft move-out inspection.

    The lease remains 'active' until the move-out inspection is signed.
    Returns the inspection so the frontend can redirect to it.

    If a draft move-out inspection already exists, returns that one
    (idempotent — safe to call twice).
    """
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if lease.status != "active":
        raise HTTPException(status_code=400, detail="Lease is not active")

    # If a move-out inspection already exists, return it
    existing_move_out = (
        db.query(LeaseInspection)
        .filter(
            LeaseInspection.lease_id == lease_id,
            LeaseInspection.inspection_type == "move_out"
        )
        .first()
    )

    if existing_move_out:
        return {
            "message": "Move-out inspection already exists",
            "inspection_id": existing_move_out.id,
            "status": existing_move_out.status,
        }

    # Create the move-out inspection (seeded with checklist items)
    inspection = create_inspection_for_lease(
        db=db,
        lease_id=lease_id,
        organization_id=membership.organization_id,
        inspection_type="move_out",
        inspector_user_id=current_user.id,
    )

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="create",
        entity_type="inspection",
        entity_id=inspection.id,
        description=f"Initiated move-out inspection for lease {lease_id}",
    )

    db.commit()
    db.refresh(inspection)

    return {
        "message": "Move-out inspection created. Conduct and sign it to complete termination.",
        "inspection_id": inspection.id,
        "status": inspection.status,
    }


# ─── Terminate Lease ───
#
# This now requires a SIGNED move-out inspection.
# If you want to terminate, call initiate-move-out first,
# fill out the inspection, and sign it. The sign endpoint
# will automatically terminate the lease.
#
# This endpoint remains as a safety check / direct call only
# fires when the move-out is already signed.

@router.post("/{lease_id}/terminate")
def terminate_lease(
    lease_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a lease as terminated.

    Guard: requires a SIGNED move-out inspection to exist.
    Returns 400 if no signed move-out inspection is found.
    """
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if lease.status != "active":
        raise HTTPException(status_code=400, detail="Lease is not active")

    # Termination guard: require a signed move-out inspection
    signed_move_out = (
        db.query(LeaseInspection)
        .filter(
            LeaseInspection.lease_id == lease_id,
            LeaseInspection.inspection_type == "move_out",
            LeaseInspection.status == "signed"
        )
        .first()
    )

    if not signed_move_out:
        raise HTTPException(
            status_code=400,
            detail="A signed move-out inspection is required before terminating this lease. "
                   "Initiate move-out and complete the inspection first."
        )

    lease.status = "terminated"

    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="terminate",
        entity_type="lease",
        entity_id=lease.id,
        description=f"Terminated lease {lease.id}",
        old_values={"status": "active"},
        new_values={"status": "terminated"},
    )

    db.commit()

    return {
        "message": "Lease terminated",
        "lease_id": lease.id,
        "status": lease.status,
    }


# ─── Upload Signed Lease Document ───

# @router.post("/{lease_id}/signed-document")
# async def upload_signed_lease(
#     lease_id: str,
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Upload the scanned signed lease PDF for a lease."""
#     membership = get_user_org(current_user, db)

#     lease = (
#         db.query(Lease)
#         .filter(
#             Lease.id == lease_id,
#             Lease.organization_id == membership.organization_id
#         )
#         .first()
#     )
#     if not lease:
#         raise HTTPException(status_code=404, detail="Lease not found")

#     file_bytes = await file.read()
#     s3_key = f"signed-leases/{lease_id}/{uuid.uuid4()}-{file.filename}"

#     try:
#         file_url = upload_file(s3_key, file_bytes)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

#     lease.signed_lease_url = file_url

#     log_action(
#         db=db,
#         organization_id=membership.organization_id,
#         user_id=current_user.id,
#         action="update",
#         entity_type="lease",
#         entity_id=lease.id,
#         description=f"Uploaded signed lease document for lease {lease.id}",
#         new_values={"signed_lease_url": file_url},
#     )

#     db.commit()
#     db.refresh(lease)

#     return {
#         "message": "Signed lease uploaded",
#         "lease_id": lease.id,
#         "signed_lease_url": file_url,
#     }

@router.post("/{lease_id}/signed-document")
async def upload_signed_lease(
    lease_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload up to 3 signed lease documents."""
    
    membership = get_user_org(current_user, db)

    lease = (
        db.query(Lease)
        .filter(
            Lease.id == lease_id,
            Lease.organization_id == membership.organization_id
        )
        .first()
    )

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if len(files) > 3:
        raise HTTPException(
            status_code=400,
            detail="Maximum 3 files allowed"
        )

    uploaded_urls = lease.signed_lease_urls or []

    remaining_slots = 3 - len(uploaded_urls)

    if len(files) > remaining_slots:
        raise HTTPException(
            status_code=400,
            detail=f"You can only upload {remaining_slots} more file(s)"
        )

    try:
        for file in files:
            file_bytes = await file.read()

            s3_key = (
                f"signed-leases/{lease_id}/"
                f"{uuid.uuid4()}-{file.filename}"
            )

            file_url = upload_file(s3_key, file_bytes)

            uploaded_urls.append(file_url)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

    lease.signed_lease_urls = uploaded_urls

    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="update",
        entity_type="lease",
        entity_id=lease.id,
        description=f"Uploaded signed lease documents for lease {lease.id}",
        new_values={"signed_lease_urls": uploaded_urls},
    )

    db.commit()
    db.refresh(lease)

    return {
        "message": "Signed lease documents uploaded",
        "lease_id": lease.id,
        "signed_lease_urls": uploaded_urls,
    }
