#backend\app\api\routes\tenants.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.models.tenant_document import TenantDocument
from app.models.lease import Lease
from app.schemas.rental import TenantCreate, TenantUpdate
from app.services.audit_service import log_action
from app.services.s3_service import upload_file

router = APIRouter(prefix="/tenants", tags=["Tenants"])


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


def tenant_dict(tenant, db=None):
    """Build tenant response dict — full profile including documents if db provided."""
    base = {
        "id": tenant.id,
        "organization_id": tenant.organization_id,

        # Personal
        "full_name": tenant.full_name,
        "email": tenant.email,
        "phone": tenant.phone,
        "alternative_phone": tenant.alternative_phone,
        "id_number": tenant.id_number,
        "emergency_contact": tenant.emergency_contact,

        # Next of kin
        "next_of_kin_name": tenant.next_of_kin_name,
        "next_of_kin_relationship": tenant.next_of_kin_relationship,
        "next_of_kin_phone": tenant.next_of_kin_phone,
        "next_of_kin_alt_phone": tenant.next_of_kin_alt_phone,
        "next_of_kin_email": tenant.next_of_kin_email,

        # Employer
        "employer_name": tenant.employer_name,
        "employer_location": tenant.employer_location,
        "employer_phone": tenant.employer_phone,
        "employer_email": tenant.employer_email,

        "created_at": tenant.created_at,
    }

    # Include documents if requested
    if db is not None:
        docs = (
            db.query(TenantDocument)
            .filter(TenantDocument.tenant_id == tenant.id)
            .order_by(TenantDocument.uploaded_at.desc())
            .all()
        )
        base["documents"] = [
            {
                "id": d.id,
                "document_type": d.document_type,
                "file_url": d.file_url,
                "original_filename": d.original_filename,
                "uploaded_at": d.uploaded_at,
            }
            for d in docs
        ]

    return base


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

        # Personal
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        alternative_phone=payload.alternative_phone,
        id_number=payload.id_number,
        emergency_contact=payload.emergency_contact,

        # Next of kin
        next_of_kin_name=payload.next_of_kin_name,
        next_of_kin_relationship=payload.next_of_kin_relationship,
        next_of_kin_phone=payload.next_of_kin_phone,
        next_of_kin_alt_phone=payload.next_of_kin_alt_phone,
        next_of_kin_email=payload.next_of_kin_email,

        # Employer
        employer_name=payload.employer_name,
        employer_location=payload.employer_location,
        employer_phone=payload.employer_phone,
        employer_email=payload.employer_email,
    )
    db.add(tenant)
    db.flush()

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="create",
        entity_type="tenant",
        entity_id=tenant.id,
        description=f"Created tenant: {payload.full_name}",
        new_values={
            "full_name": payload.full_name,
            "phone": payload.phone,
            "email": payload.email,
        },
    )

    db.commit()
    db.refresh(tenant)

    return tenant_dict(tenant, db)


# ─── List Tenants ───

@router.get("/")
def list_tenants(
    search: str = Query(None, description="Search by name, phone, ID, or email"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(Tenant).filter(
        Tenant.organization_id == membership.organization_id
    )

    if search:
        s = f"%{search}%"
        query = query.filter(
            (Tenant.full_name.ilike(s))
            | (Tenant.phone.ilike(s))
            | (Tenant.id_number.ilike(s))
            | (Tenant.email.ilike(s))
        )

    tenants = query.order_by(Tenant.created_at.desc()).all()

    return [tenant_dict(t) for t in tenants]


# ─── Get Single Tenant ───

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

    return tenant_dict(tenant, db)


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

    # Capture old values for audit
    old_values = {
        "full_name": tenant.full_name,
        "phone": tenant.phone,
        "email": tenant.email,
        "id_number": tenant.id_number,
    }

    # Apply updates
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="update",
        entity_type="tenant",
        entity_id=tenant.id,
        description=f"Updated tenant: {tenant.full_name}",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(tenant)

    return tenant_dict(tenant, db)


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

    # Don't delete tenants with active leases
    active_lease = (
        db.query(Lease)
        .filter(Lease.tenant_id == tenant_id, Lease.status == "active")
        .first()
    )
    if active_lease:
        raise HTTPException(status_code=400, detail="Cannot delete tenant with an active lease")

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="delete",
        entity_type="tenant",
        entity_id=tenant.id,
        description=f"Deleted tenant: {tenant.full_name}",
    )

    db.delete(tenant)
    db.commit()

    return {"message": "Tenant deleted"}


# ─── Upload Tenant Document ───

@router.post("/{tenant_id}/documents")
async def upload_tenant_document(
    tenant_id: str,
    document_type: str = Form(..., description="national_id_front, national_id_back, passport_biodata, other"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    # Verify tenant belongs to this org
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

    # Validate document type
    allowed_types = ["national_id_front", "national_id_back", "passport_biodata", "other"]
    if document_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Document type must be one of: {allowed_types}")

    # Read file bytes
    file_bytes = await file.read()

    # Build a unique S3 key
    s3_key = f"tenant-documents/{tenant_id}/{uuid.uuid4()}-{file.filename}"

    # Upload to S3
    try:
        file_url = upload_file(s3_key, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # Save record
    document = TenantDocument(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        document_type=document_type,
        file_url=file_url,
        original_filename=file.filename,
        uploaded_by_user_id=current_user.id,
    )
    db.add(document)
    db.flush()

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="create",
        entity_type="tenant_document",
        entity_id=document.id,
        description=f"Uploaded {document_type} for tenant {tenant.full_name}",
        new_values={"filename": file.filename, "document_type": document_type},
    )

    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "tenant_id": document.tenant_id,
        "document_type": document.document_type,
        "file_url": document.file_url,
        "original_filename": document.original_filename,
        "uploaded_at": document.uploaded_at,
    }


# ─── List Tenant Documents ───

@router.get("/{tenant_id}/documents")
def list_tenant_documents(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    # Verify tenant belongs to this org
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

    documents = (
        db.query(TenantDocument)
        .filter(TenantDocument.tenant_id == tenant_id)
        .order_by(TenantDocument.uploaded_at.desc())
        .all()
    )

    return [
        {
            "id": d.id,
            "tenant_id": d.tenant_id,
            "document_type": d.document_type,
            "file_url": d.file_url,
            "original_filename": d.original_filename,
            "uploaded_at": d.uploaded_at,
        }
        for d in documents
    ]


# ─── Delete Tenant Document ───

@router.delete("/{tenant_id}/documents/{document_id}")
def delete_tenant_document(
    tenant_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    # Verify tenant belongs to this org
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

    document = (
        db.query(TenantDocument)
        .filter(
            TenantDocument.id == document_id,
            TenantDocument.tenant_id == tenant_id
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Audit log
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        action="delete",
        entity_type="tenant_document",
        entity_id=document.id,
        description=f"Deleted {document.document_type} for tenant {tenant.full_name}",
    )

    # Note: we don't delete the actual S3 file here — that can be cleaned up
    # by a separate cleanup job if needed. Just remove the DB reference.
    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}
