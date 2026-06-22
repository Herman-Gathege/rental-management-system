#backend\app\models\expense_attachment.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class ExpenseAttachment(Base):
    __tablename__ = "expense_attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    expense_id = Column(
        String, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )

    filename = Column(String, nullable=True)
    file_url = Column(String, nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    expense = relationship("Expense", back_populates="attachments")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
