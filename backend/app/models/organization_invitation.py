# backend\app\models\organization_invitation.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False)

    # Phase 3: WhatsApp phone for sending the invite link.
    # Nullable because existing invitations were created without it,
    # and admins may still want to use the email-only flow if a
    # phone isn't known yet.
    phone = Column(String, nullable=True)

    role_id = Column(String, ForeignKey("roles.id"))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"))
    token = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")  # pending / accepted / expired
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role")
    organization = relationship("Organization")
