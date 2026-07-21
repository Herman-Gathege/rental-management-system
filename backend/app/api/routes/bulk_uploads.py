#backend\app\api\routes\bulk_uploads.py
"""
Bulk upload endpoints — Sprint 7 cleanup (Batch 2).

Landlord only. Two entities supported now: properties, units. Payment
bulk upload (with bank / M-Pesa format mapping) is deferred to its own
session per Anne's roadmap.

  GET  /bulk-uploads/properties/template   → download CSV template
  POST /bulk-uploads/properties            → upload properties CSV
  GET  /bulk-uploads/units/template        → download CSV template
  POST /bulk-uploads/units                 → upload units CSV
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.core.roles import LANDLORD
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.services import bulk_upload_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/bulk-uploads", tags=["Bulk Uploads"])

# 2 MB cap. A properties or units CSV is tiny — hundreds of KB tops even
# for large portfolios. Anything bigger is either a mistake (wrong file
# type) or abuse. Keeps memory bounded.
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


# ─── Dep: landlord only ──────────────────────────────────────────────────

def require_landlord(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk uploads are admin work — only landlords are allowed for MVP.
    Returns (user, membership, db) so the route can pull org_id from
    membership without a second lookup."""
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    if membership.role.name != LANDLORD:
        raise HTTPException(
            status_code=403,
            detail="Only landlords can perform bulk uploads",
        )
    return user, membership, db


async def _read_upload(file: UploadFile) -> bytes:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_BYTES // 1024 // 1024} MB",
        )
    return contents


# ─── Templates ───────────────────────────────────────────────────────────

@router.get("/properties/template")
def download_properties_template(deps=Depends(require_landlord)):
    """Returns a CSV with the header row and a couple of example rows so
    the user has a concrete starting point."""
    csv_text = bulk_upload_service.get_properties_template_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="properties-template.csv"'
        },
    )


@router.get("/units/template")
def download_units_template(deps=Depends(require_landlord)):
    csv_text = bulk_upload_service.get_units_template_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="units-template.csv"'
        },
    )


# ─── Uploads ─────────────────────────────────────────────────────────────

@router.post("/properties")
async def upload_properties(
    file: UploadFile = File(...),
    deps=Depends(require_landlord),
):
    user, membership, db = deps
    contents = await _read_upload(file)

    result = bulk_upload_service.parse_and_import_properties(
        db, membership.organization_id, contents
    )

    # Audit the bulk operation itself (individual entities aren't logged —
    # the aggregate is what matters for a bulk import).
    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=user.id,
        action="bulk_create",
        entity_type="property",
        entity_id=str(uuid.uuid4()),
        description=(
            f"Bulk property upload: {len(result.imported)} imported, "
            f"{len(result.skipped)} skipped, {result.total_rows} total"
        ),
        new_values={
            "imported_count": len(result.imported),
            "skipped_count": len(result.skipped),
            "total_rows": result.total_rows,
        },
    )

    db.commit()
    return result.to_dict()


@router.post("/units")
async def upload_units(
    file: UploadFile = File(...),
    deps=Depends(require_landlord),
):
    user, membership, db = deps
    contents = await _read_upload(file)

    result = bulk_upload_service.parse_and_import_units(
        db, membership.organization_id, contents
    )

    log_action(
        db=db,
        organization_id=membership.organization_id,
        user_id=user.id,
        action="bulk_create",
        entity_type="unit",
        entity_id=str(uuid.uuid4()),
        description=(
            f"Bulk unit upload: {len(result.imported)} imported, "
            f"{len(result.skipped)} skipped, {result.total_rows} total"
        ),
        new_values={
            "imported_count": len(result.imported),
            "skipped_count": len(result.skipped),
            "total_rows": result.total_rows,
        },
    )

    db.commit()
    return result.to_dict()
