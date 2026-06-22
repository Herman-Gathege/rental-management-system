#backend\app\services\expense_category_seed.py
"""
Default expense categories (Sprint 5).

Every organization gets a standard set of categories so reports are consistent
across orgs. Seeding is idempotent — it only inserts names that aren't already
present for that org (matched against the (organization_id, name) unique
constraint), so it's safe to run repeatedly and safe alongside any categories
created manually or via the API.

Two entry points:
  - seed_expense_categories_for_org(db, org_id): used when a NEW org is created
    (called inside the register() transaction; does NOT commit — the caller does).
  - seed_expense_categories_for_all_orgs(db): one-time backfill for EXISTING orgs,
    run on startup; commits its own work.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.expense_category import ExpenseCategory


DEFAULT_EXPENSE_CATEGORIES = [
    "Repairs",
    "Maintenance",
    "Cleaning",
    "Water",
    "Electricity",
    "Security",
    "Salaries",
    "Marketing",
    "Internet",
    "Legal",
    "Insurance",
    "Fuel",
    "Office Supplies",
    "Landscaping",
    "Waste Collection",
    "Other",
]


def seed_expense_categories_for_org(db: Session, org_id: str) -> int:
    """Insert any default categories missing for this org. Adds to the session
    but does NOT commit — the caller commits (so it can run inside another
    transaction, e.g. org registration). Returns the number created."""
    existing_names = {
        row[0]
        for row in (
            db.query(ExpenseCategory.name)
            .filter(ExpenseCategory.organization_id == org_id)
            .all()
        )
    }

    created = 0
    for name in DEFAULT_EXPENSE_CATEGORIES:
        if name in existing_names:
            continue
        db.add(
            ExpenseCategory(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                name=name,
                is_active=True,
            )
        )
        created += 1

    return created


def seed_expense_categories_for_all_orgs(db: Session) -> int:
    """Backfill defaults for every existing org. Commits its own work.
    Returns the total number of categories created across all orgs."""
    org_ids = [r[0] for r in db.query(Organization.id).all()]
    total = 0
    for org_id in org_ids:
        total += seed_expense_categories_for_org(db, org_id)
    if total:
        db.commit()
    return total
