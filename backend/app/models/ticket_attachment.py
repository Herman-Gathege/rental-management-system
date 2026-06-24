#backend\app\models\ticket_attachment.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(
        String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)

    file_name = Column(String, nullable=True)
    file_url = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
