#backend\app\models\tenant.py

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


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
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    alternative_phone = Column(String, nullable=True)
    id_number = Column(String, nullable=True)

    # Legacy field — kept for backwards compatibility
    emergency_contact = Column(String, nullable=True)

    # ─── Next of Kin ───
    next_of_kin_name = Column(String, nullable=True)
    next_of_kin_relationship = Column(String, nullable=True)
    next_of_kin_phone = Column(String, nullable=True)
    next_of_kin_alt_phone = Column(String, nullable=True)
    next_of_kin_email = Column(String, nullable=True)

    # ─── Employer / Business ───
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