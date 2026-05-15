#backend\app\services\checklist_seed.py
import uuid
from sqlalchemy.orm import Session
from app.models.checklist_item_template import ChecklistItemTemplate


# ─── Default 13 items from the lease form Schedule 1: Move-In Condition Checklist ───
# These match exactly what's on the signed paper lease.
DEFAULT_CHECKLIST_ITEMS = [
    "Doors, windows, glass, handles, hinges, and locks",
    "Floor finishes (tiles/terrazzo)",
    "Walls and paint finish",
    "Door locks and keys issued (list keys)",
    "Electricity switches, sockets, and light fittings",
    "Water taps and plumbing visible fittings (note any defects/leaks)",
    "Hot water heater / shower",
    "Sinks and drain points (note any defects/leaks)",
    "Kitchen cabinets/cupboards, drawers, and shelves",
    "Bedroom wardrobes, drawers, and shelves",
    "Bathroom and bedroom mirrors",
    "Bathroom soap holder, toilet paper holder, and robe/towel holders",
    "Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)",
]


def seed_checklist_for_org(db: Session, organization_id: str) -> int:
    """
    Seed default checklist items for an organization.
    Idempotent — only seeds if the org has zero items yet.

    Returns the number of items created (0 if org already has items).
    """
    existing_count = (
        db.query(ChecklistItemTemplate)
        .filter(ChecklistItemTemplate.organization_id == organization_id)
        .count()
    )

    if existing_count > 0:
        return 0

    for idx, item_name in enumerate(DEFAULT_CHECKLIST_ITEMS):
        item = ChecklistItemTemplate(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            item_name=item_name,
            sort_order=idx,
            is_default=True,
            is_active=True,
        )
        db.add(item)

    return len(DEFAULT_CHECKLIST_ITEMS)


def seed_checklist_for_all_orgs(db: Session) -> int:
    """
    TEMPORARY: seed defaults for any existing orgs that don't have items yet.

    Called from main.py startup. Once all existing orgs are seeded, this
    function can be removed — new orgs get seeded at registration time
    via the auth route.

    Returns the total number of items created across all orgs.
    """
    from app.models.organization import Organization

    organizations = db.query(Organization).all()
    total_created = 0

    for org in organizations:
        created = seed_checklist_for_org(db, org.id)
        total_created += created

    if total_created > 0:
        db.commit()

    return total_created
