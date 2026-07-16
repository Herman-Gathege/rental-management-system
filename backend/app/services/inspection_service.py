#backend\app\services\inspection_service.py
"""
Inspection lifecycle helpers.

Two responsibilities:

  1. create_inspection_for_lease
     Called by lease routes to open a draft inspection (move-in on lease
     create, or a recovery move-in / move-out on demand). Pre-populates
     the inspection with the org's ACTIVE checklist template items at the
     moment of creation.

  2. ensure_items_seeded (Sprint 7 cleanup)
     Lazy-seed fallback for the case where an inspection was created
     BEFORE any checklist template items existed — very common on the
     first lease of a new organization, because the move-in inspection
     is auto-created by /leases/ POST but the checklist template is
     usually still empty at that point. Without this fallback, adding
     template items later doesn't retroactively populate that first
     inspection and the "Conduct Inspection" page shows a blank
     checklist forever.

     Called from the inspection GET route, so opening an empty draft
     inspection re-seeds it from the CURRENT template. Idempotent —
     inspections that already have items are left alone, and signed
     inspections are never touched.
"""
import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.lease_inspection import LeaseInspection
from app.models.inspection_item import InspectionItem
from app.models.checklist_item_template import ChecklistItemTemplate


def _load_active_template(db: Session, organization_id: str):
    """Active checklist template items for an org, ordered by sort_order."""
    return (
        db.query(ChecklistItemTemplate)
        .filter(
            ChecklistItemTemplate.organization_id == organization_id,
            ChecklistItemTemplate.is_active == True,  # noqa: E712
        )
        .order_by(ChecklistItemTemplate.sort_order.asc())
        .all()
    )


def _make_inspection_item(inspection_id: str, template_item: ChecklistItemTemplate) -> InspectionItem:
    """Build an InspectionItem row from a template row. Blank condition/
    comments/photos/deduction — the inspector fills these in during the walk."""
    return InspectionItem(
        id=str(uuid.uuid4()),
        inspection_id=inspection_id,
        item_name=template_item.item_name,
        sort_order=template_item.sort_order,
        condition=None,
        comments=None,
        photo_urls="[]",
        deduction_amount=0,
    )


def create_inspection_for_lease(
    db: Session,
    lease_id: str,
    organization_id: str,
    inspection_type: str,
    inspector_user_id: str = None,
):
    """
    Create a draft inspection for a lease, pre-populated with the org's
    active checklist items.

    inspection_type: 'move_in' or 'move_out'
    Returns the created LeaseInspection (not yet committed — caller commits).

    Note: if the checklist template is empty at this moment (common on the
    first lease of a new org), the inspection is created with ZERO items.
    ensure_items_seeded() lazy-seeds it on first GET once the template
    has been populated.
    """
    if inspection_type not in ("move_in", "move_out"):
        raise ValueError("inspection_type must be 'move_in' or 'move_out'")

    # Create the inspection record
    inspection = LeaseInspection(
        id=str(uuid.uuid4()),
        lease_id=lease_id,
        inspection_type=inspection_type,
        inspector_user_id=inspector_user_id,
        status="draft",
    )
    db.add(inspection)
    db.flush()

    # Pull active checklist items for this org, in sort order
    template_items = _load_active_template(db, organization_id)

    # Create one InspectionItem per template item
    for template_item in template_items:
        db.add(_make_inspection_item(inspection.id, template_item))

    return inspection


def ensure_items_seeded(
    db: Session,
    inspection: LeaseInspection,
    organization_id: str,
) -> int:
    """
    Sprint 7 cleanup: lazy-seed an empty draft inspection from the current
    checklist template.

    No-op unless ALL three conditions hold:
      - inspection is a draft (signed inspections are immutable)
      - inspection has zero items so far
      - the org has at least one active template item to seed from

    Commits any rows it creates so subsequent queries see them. Returns the
    number of items added (0 if nothing was seeded).
    """
    if inspection.status != "draft":
        return 0

    existing_count = (
        db.query(func.count(InspectionItem.id))
        .filter(InspectionItem.inspection_id == inspection.id)
        .scalar()
    ) or 0
    if existing_count > 0:
        return 0

    template_items = _load_active_template(db, organization_id)
    if not template_items:
        return 0

    for template_item in template_items:
        db.add(_make_inspection_item(inspection.id, template_item))

    db.commit()
    return len(template_items)
