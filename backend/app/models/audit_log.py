#backend\app\models\audit_log.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # create / update / delete / terminate / payment / billing
    entity_type = Column(String, nullable=False)  # property / unit / tenant / lease / charge / payment
    entity_id = Column(String, nullable=False)
    description = Column(String, nullable=False)
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    user = relationship("User")
