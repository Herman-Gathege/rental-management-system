#backend\app\models\charge.py
import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Charge(Base):
    __tablename__ = "charges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lease_id = Column(String, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    billing_month = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending / paid / overdue
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    lease = relationship("Lease")
