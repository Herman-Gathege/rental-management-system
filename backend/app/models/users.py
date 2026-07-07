# backend/app/models/users.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import ForeignKey

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # organization_id = Column(String, ForeignKey("organizations.id"))
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)  # Profile name (Sprint 4.5 profile menu)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # ─── Phone verification (Sprint 6.2 #6) ───
    # phone captured at landlord signup; phone_verified gates access until the
    # OTP is confirmed. Existing users are backfilled to True by the migration
    # so no one already onboarded is locked out — only new signups start False.
    phone = Column(String, nullable=True)
    phone_verified = Column(Boolean, nullable=False, default=False)

    refresh_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    role_id = Column(String, ForeignKey("roles.id"))


    role = relationship("Role")
    memberships = relationship("OrganizationMember", back_populates="user")
    # organization = relationship("Organization")
