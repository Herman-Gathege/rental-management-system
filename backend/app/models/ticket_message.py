#backend\app\models\ticket_message.py
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(
        String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id = Column(String, ForeignKey("users.id"), nullable=True)

    message = Column(Text, nullable=False)
    # Internal notes (is_internal=True) are hidden from tenants.
    is_internal = Column(Boolean, nullable=False, default=False)

    # ─── Sprint 7 cleanup: targeted internal notes ───
    # NULL  → broadcast (visible to all staff who can see the ticket).
    # UUID  → targeted; only sender + landlord + the chosen recipient
    #         can see this message. Landlord always sees everything.
    # Only meaningful when is_internal=True; on a public message it is
    # forced to NULL by the service layer.
    recipient_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
