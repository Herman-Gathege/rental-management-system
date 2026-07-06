#backend\app\models\payment.py
import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    lease_id = Column(String, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String, nullable=False, default="cash")  # cash / mpesa / bank
    reference = Column(String, nullable=True)

    # Sprint 6.2 (#7): which obligation this payment settles.
    # "rent" (default) — settles rent charges; counted in collected/expected.
    # "deposit" — settles the one-time security-deposit charge; tracked
    # separately (deposits_held) so it never inflates rent-collection figures.
    payment_type = Column(String, nullable=False, default="rent")

    payment_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    tenant = relationship("Tenant")
    lease = relationship("Lease")
