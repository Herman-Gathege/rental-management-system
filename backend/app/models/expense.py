#backend\app\models\expense.py
import uuid
from sqlalchemy import Column, String, Text, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )

    # Scope
    property_id = Column(
        String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    unit_id = Column(String, ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    vendor_id = Column(
        String, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True
    )
    category_id = Column(
        String, ForeignKey("expense_categories.id"), nullable=False
    )

    # People
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    payment_method = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)

    # Workflow: draft -> submitted -> approved -> paid -> archived
    # (rejected returns to draft)
    status = Column(String, nullable=False, default="draft")

    receipt_number = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("ExpenseCategory", back_populates="expenses")
    vendor = relationship("Vendor", back_populates="expenses")
    attachments = relationship(
        "ExpenseAttachment",
        back_populates="expense",
        cascade="all, delete-orphan",
    )
    # Two FKs point at users, so disambiguate with foreign_keys. These are
    # one-directional (no back_populates on User) so the User model is untouched.
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
