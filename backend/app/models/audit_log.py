#backend\app\models\audit_log.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Sprint 7 follow-up: organization_id is now nullable so we can log auth
    # events with no org context (failed login with unknown email, etc.).
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # create / update / delete / login / failed_login / password_change / ...
    entity_type = Column(String, nullable=False)  # user / property / unit / tenant / lease / charge / payment / ...
    entity_id = Column(String, nullable=False)
    description = Column(String, nullable=False)
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values
    # Sprint 7 follow-up: IP of the request that caused this event. Populated
    # for auth events via audit_service.get_client_ip(); older event types
    # (leases, payments, etc.) leave it null.
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    user = relationship("User")
