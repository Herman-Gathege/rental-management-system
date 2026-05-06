#backend\app\models\lease.py

import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum


class LeaseStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"
    TERMINATED = "terminated"


class Lease(Base):
    __tablename__ = "leases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    unit_id = Column(String, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    rent_amount = Column(Numeric(10, 2), nullable=False)  # snapshot of rent at lease creation
    deposit_amount = Column(Numeric(10, 2), nullable=True, default=0)
    billing_day = Column(Integer, nullable=False, default=1)  # day of month rent is due
    status = Column(String, nullable=False, default=LeaseStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    unit = relationship("Unit", back_populates="leases")
    tenant = relationship("Tenant", back_populates="leases")
