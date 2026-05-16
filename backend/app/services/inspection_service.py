#backend\app\services\inspection_service.py
import uuid
from sqlalchemy.orm import Session
from app.models.lease_inspection import LeaseInspection
from app.models.inspection_item import InspectionItem
from app.models.checklist_item_template import ChecklistItemTemplate


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
    template_items = (
        db.query(ChecklistItemTemplate)
        .filter(
            ChecklistItemTemplate.organization_id == organization_id,
            ChecklistItemTemplate.is_active == True,
        )
        .order_by(ChecklistItemTemplate.sort_order.asc())
        .all()
    )

    # Create one InspectionItem per template item
    for template_item in template_items:
        item = InspectionItem(
            id=str(uuid.uuid4()),
            inspection_id=inspection.id,
            item_name=template_item.item_name,
            sort_order=template_item.sort_order,
            condition=None,
            comments=None,
            photo_urls="[]",
            deduction_amount=0,
        )
        db.add(item)

    return inspection
