#backend\app\models\lease.py

import uuid
from sqlalchemy import Column, String, Date, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Lease(Base):
    __tablename__ = "leases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # ─── Term ───
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Possession / handover date — may differ from start_date
    # if keys are issued later (e.g. after rent + deposit are paid)
    move_in_date = Column(Date, nullable=True)

    # ─── Financial ───
    rent_amount = Column(Numeric(12, 2), nullable=False)
    deposit_amount = Column(Numeric(12, 2), nullable=True, default=0)
    billing_day = Column(Integer, default=1)

    # ─── Signing details ───
    # If the lease is signed by someone acting on behalf of the actual landlord
    # (e.g. "Adam Sirali signing for Erick Sirali"), this records that
    signed_on_behalf_of = Column(String, nullable=True)

    # URL to the scanned signed lease document (uploaded after signing)
    signed_lease_url = Column(String, nullable=True)

    # ─── Status ───
    # active / ended / terminated / pending_inspection
    status = Column(String, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    unit = relationship("Unit")
    tenant = relationship("Tenant", back_populates="leases")
    charges = relationship("Charge", back_populates="lease", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="lease", cascade="all, delete-orphan")
    inspections = relationship("LeaseInspection", back_populates="lease", cascade="all, delete-orphan")
