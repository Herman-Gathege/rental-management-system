#backend\app\models\tenant.py

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, event
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.db.types import EncryptedString
from app.core.encryption import blind_index


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # ─── Linked login (Sprint 4.5) ───
    # The User account this tenant logs in with. Nullable: a tenant record can
    # exist long before that person ever accepts a portal invite. Set at
    # invite-accept (organizations.py) and via the one-time email backfill in
    # migration b7f3c1e9a4d2. SET NULL on user delete so removing an account
    # never cascades away the tenant's leases / charges / payments.
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # ─── Personal Information ───
    # Sprint 7 MVP-1: sensitive fields moved to EncryptedString. Names + roles
    # stay plaintext (see the design notes in app/core/encryption.py). Fields
    # used for uniqueness/lookup (phone, alternative_phone, email, id_number)
    # get a companion *_hash blind-index column below.
    full_name = Column(String, nullable=False)
    email = Column(EncryptedString, nullable=True)
    phone = Column(EncryptedString, nullable=False)
    alternative_phone = Column(EncryptedString, nullable=True)
    id_number = Column(EncryptedString, nullable=True)

    # Legacy field — kept for backwards compatibility. Encrypted; not searched.
    emergency_contact = Column(EncryptedString, nullable=True)

    # Blind-index hashes for the fields we search / enforce uniqueness on.
    # Populated automatically by the before_insert / before_update listeners
    # at the bottom of this module — do NOT set these by hand in application
    # code. See app/services/tenant_validation.py for how they're queried.
    phone_hash = Column(String(64), nullable=True, index=True)
    alternative_phone_hash = Column(String(64), nullable=True, index=True)
    email_hash = Column(String(64), nullable=True, index=True)
    id_number_hash = Column(String(64), nullable=True, index=True)

    # ─── Next of Kin ───
    # Relationship (spouse/parent/etc.) stays plaintext — not sensitive.
    next_of_kin_name = Column(EncryptedString, nullable=True)
    next_of_kin_relationship = Column(String, nullable=True)
    next_of_kin_phone = Column(EncryptedString, nullable=True)
    next_of_kin_alt_phone = Column(EncryptedString, nullable=True)
    next_of_kin_email = Column(EncryptedString, nullable=True)

    # ─── Employer / Business ───
    # Not encrypted — business records, not personal PII.
    employer_name = Column(String, nullable=True)
    employer_location = Column(String, nullable=True)
    employer_phone = Column(String, nullable=True)
    employer_email = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
    leases = relationship("Lease", back_populates="tenant")
    documents = relationship("TenantDocument", back_populates="tenant", cascade="all, delete-orphan")


# ─── Hash sync (Sprint 7 MVP-1) ───
#
# Keeps the blind-index columns aligned with their source columns without
# every route having to remember. On insert/update we look at what phone /
# alternative_phone / email / id_number will land in the row and recompute the
# corresponding hash. Empty/null → null hash so we don't accidentally collide
# many "blank" tenants together via a shared hash of ''.

_HASH_MAP = {
    "phone": "phone_hash",
    "alternative_phone": "alternative_phone_hash",
    "email": "email_hash",
    "id_number": "id_number_hash",
}


def _sync_hashes(target: Tenant) -> None:
    for src_attr, hash_attr in _HASH_MAP.items():
        value = getattr(target, src_attr, None)
        setattr(target, hash_attr, blind_index(value))


@event.listens_for(Tenant, "before_insert")
def _tenant_before_insert(mapper, connection, target):
    _sync_hashes(target)


@event.listens_for(Tenant, "before_update")
def _tenant_before_update(mapper, connection, target):
    _sync_hashes(target)
