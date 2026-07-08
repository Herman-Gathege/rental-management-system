#backend\app\services\tenant_validation.py
"""
Tenant uniqueness validation (Sprint 6.2 #5, updated for Sprint 7 PII
encryption).

Enforces, PER ORGANIZATION, that these tenant fields don't collide:
  - phone / alternative_phone  (checked together — a number used as anyone's
    primary phone can't also be another tenant's alternative, and vice versa)
  - email
  - id_number

Blanks are ignored: only non-empty values are checked. A tenant may leave a
field blank, but any value they do provide must be unique within the org.

Sprint 7 change: the underlying columns are now encrypted (Fernet ciphertext),
which means `Tenant.phone == '0712...'` no longer works — two encryptions of
the same value produce different ciphertexts. We now query the *_hash columns
(deterministic HMAC-SHA256, populated by the model's before_insert /
before_update listeners) and compare against blind_index(candidate).
"""

from typing import Optional
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.encryption import blind_index
from app.models.tenant import Tenant


def _clean(v: Optional[str]) -> Optional[str]:
    """Normalise a candidate value: strip whitespace, treat empty as None."""
    if v is None:
        return None
    v = v.strip()
    return v or None


def check_tenant_uniqueness(
    db: Session,
    org_id: str,
    *,
    phone: Optional[str] = None,
    alternative_phone: Optional[str] = None,
    email: Optional[str] = None,
    id_number: Optional[str] = None,
    exclude_tenant_id: Optional[str] = None,
):
    """
    Raise HTTP 400 if any provided (non-empty) value already belongs to a
    DIFFERENT tenant in the same organization.

    Pass `exclude_tenant_id` on update so a tenant isn't flagged against itself.

    Phone checks span BOTH phone slots (phone + alternative_phone): the
    candidate phone and alternative_phone are each hashed and checked against
    existing phone_hash AND alternative_phone_hash, so a number can't be
    reused across either slot.
    """
    phone = _clean(phone)
    alternative_phone = _clean(alternative_phone)
    email = _clean(email)
    id_number = _clean(id_number)

    base = db.query(Tenant).filter(Tenant.organization_id == org_id)
    if exclude_tenant_id:
        base = base.filter(Tenant.id != exclude_tenant_id)

    # ─── Phone / alternative phone (shared pool) ───
    # Compute hashes for each provided phone candidate. blind_index normalises
    # (strip + lower) internally so callers don't have to.
    phone_hashes = {blind_index(p) for p in (phone, alternative_phone) if p}
    phone_hashes.discard(None)
    if phone_hashes:
        conflict = (
            base.filter(
                or_(
                    Tenant.phone_hash.in_(phone_hashes),
                    Tenant.alternative_phone_hash.in_(phone_hashes),
                )
            ).first()
        )
        if conflict:
            # Which candidate collided? Compare hashes back to the source
            # inputs to produce a specific message.
            existing_hashes = {conflict.phone_hash, conflict.alternative_phone_hash}
            clashed = None
            for cand in (phone, alternative_phone):
                if cand and blind_index(cand) in existing_hashes:
                    clashed = cand
                    break
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Phone number {clashed or ''} is already used by another "
                    f"tenant ({conflict.full_name})."
                ).strip(),
            )

    # ─── Email ───
    if email:
        conflict = base.filter(Tenant.email_hash == blind_index(email)).first()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Email {email} is already used by another tenant ({conflict.full_name}).",
            )

    # ─── ID number ───
    if id_number:
        conflict = base.filter(Tenant.id_number_hash == blind_index(id_number)).first()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"ID number {id_number} is already used by another tenant ({conflict.full_name}).",
            )
