# backend/app/models/organization_invitation.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))

    token = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")  # pending / accepted / expired

    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role")
    organization = relationship("Organization")