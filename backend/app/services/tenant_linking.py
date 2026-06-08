# backend/app/services/tenant_linking.py
"""
Tenant <-> User account linking (Sprint 4.5 hardening).

A tenant can only see their portal data once their Tenant row is connected to
their login via tenants.user_id. Three places need to make that connection:
the invite-accept flow, the register-via-invite flow, and -- as a safety net --
login. They all funnel through link_tenant_to_user so the matching rule lives
in exactly one place and the three can never drift apart.

Matching rule: same organization, email equal after trimming + lowercasing
(so 'Essy@Gmail.com ' still matches 'essy@gmail.com'), and not already linked.
Best-effort and non-committing: the caller owns the transaction / commit.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def link_tenant_to_user(
    db: Session,
    *,
    organization_id: str,
    email: str,
    user_id: str,
) -> bool:
    """
    Link the matching, not-yet-linked Tenant row to user_id.

    Returns True if a link was made, False if no eligible tenant was found.
    Does NOT commit -- the caller commits as part of its own transaction.
    """
    normalized = (email or "").strip().lower()
    if not normalized:
        return False

    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.organization_id == organization_id,
            func.lower(func.trim(Tenant.email)) == normalized,
            Tenant.user_id.is_(None),
        )
        .first()
    )

    if tenant is None:
        return False

    tenant.user_id = user_id
    return True
