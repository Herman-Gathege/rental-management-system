#backend\app\models\lease_inspection.py
import uuid
from sqlalchemy import Column, String, Date, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class LeaseInspection(Base):
    __tablename__ = "lease_inspections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lease_id = Column(String, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False)

    # move_in or move_out
    inspection_type = Column(String, nullable=False)

    # When the inspection was conducted
    inspection_date = Column(Date, nullable=True)

    # Who conducted it (typically a property manager or landlord)
    inspector_user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # ─── Signature data ───
    # Tenant's drawn signature as a base64-encoded PNG data URL
    tenant_signature_data = Column(Text, nullable=True)
    tenant_signed_name = Column(String, nullable=True)
    tenant_signed_at = Column(DateTime, nullable=True)

    # ─── Status ───
    # draft   — inspector is still filling it out (editable)
    # signed  — tenant has signed, locked from edits (only notes can be added)
    # disputed — flagged via a note; still locked
    status = Column(String, default="draft")

    # ─── Move-out financial reconciliation ───
    # Only relevant for move_out inspections. Sum of all item deductions.
    total_deduction_amount = Column(Numeric(12, 2), nullable=True, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lease = relationship("Lease", back_populates="inspections")
    inspector = relationship("User")
    items = relationship("InspectionItem", back_populates="inspection", cascade="all, delete-orphan")
    notes = relationship("InspectionNote", back_populates="inspection", cascade="all, delete-orphan")
