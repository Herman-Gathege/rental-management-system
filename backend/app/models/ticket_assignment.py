#backend\app\models\ticket_assignment.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(
        String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # assigned_from is null on the first assignment (was unassigned).
    assigned_from = Column(String, ForeignKey("users.id"), nullable=True)
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)

    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="assignments")
    from_user = relationship("User", foreign_keys=[assigned_from])
    to_user = relationship("User", foreign_keys=[assigned_to])
