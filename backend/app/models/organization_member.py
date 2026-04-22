# backend/app/models/organization_member.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))
    role_id = Column(Integer, ForeignKey("roles.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Prevent duplicate membership
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_org"),
    )

    # relationships
    user = relationship("User")
    role = relationship("Role")
    organization = relationship("Organization", back_populates="members")