#backend\app\models\inspection_note.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class InspectionNote(Base):
    """
    Notes added to an inspection after it has been signed.

    Once an inspection is signed and locked, its items cannot be edited.
    Notes provide a way to add observations, disputes, or clarifications
    after the fact without modifying the original record.
    """
    __tablename__ = "inspection_notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String, ForeignKey("lease_inspections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    note = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inspection = relationship("LeaseInspection", back_populates="notes")
    user = relationship("User")
