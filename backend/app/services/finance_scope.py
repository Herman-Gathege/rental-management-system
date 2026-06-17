# backend/app/services/finance_scope.py
#
# Finance scoping (Sprint 4.5 owner portal #2b).
# A FINANCE user only sees money for the properties they're assigned to in
# property_finance_managers. Strict rule: no assignments => empty list => the
# caller treats that as "sees nothing". LANDLORD callers never use this (they
# stay org-wide).
from sqlalchemy.orm import Session

from app.models.property_finance_manager import PropertyFinanceManager
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease


def assigned_finance_property_ids(db: Session, user_id: str, org_id: str) -> list:
    """Property IDs a FINANCE user is assigned to, scoped to their org.
    Empty list => assigned to nothing (so, under strict scoping, sees nothing)."""
    rows = (
        db.query(PropertyFinanceManager.property_id)
        .join(Property, Property.id == PropertyFinanceManager.property_id)
        .filter(
            PropertyFinanceManager.user_id == user_id,
            Property.organization_id == org_id,
        )
        .all()
    )
    return [r[0] for r in rows]


def lease_ids_for_properties(db: Session, property_ids: list) -> list:
    """Lease IDs whose unit belongs to one of the given properties.
    Empty input => empty output."""
    if not property_ids:
        return []
    rows = (
        db.query(Lease.id)
        .join(Unit, Unit.id == Lease.unit_id)
        .filter(Unit.property_id.in_(property_ids))
        .all()
    )
    return [r[0] for r in rows]
