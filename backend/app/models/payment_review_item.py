#backend\app\models\payment_review_item.py
"""
Payment review item — Sprint 7 cleanup (Batch 3).

A candidate payment awaiting a decision from the reconciliation queue.
See migration c2d3e4f5a6b7 for the fuller design rationale.

Lifecycle:
    pending_review  →  applied   (linked to a new Payment via resolution_payment_id)
    pending_review  →  rejected  (rejection_reason captures why)
    pending_review  →  (deleted) (hard delete for pending / rejected junk;
                                  applied items cannot be deleted since they're
                                  linked to a real Payment)
"""
import uuid
from sqlalchemy import Column, String, Text, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class PaymentReviewItem(Base):
    __tablename__ = "payment_review_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Original payment data — captured from the CSV row or manual entry.
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, nullable=True)
    reference = Column(String, nullable=True)
    payer_phone = Column(String, nullable=True)
    payer_name = Column(String, nullable=True)
    raw_transaction = Column(Text, nullable=True)

    # Best-guess matches (nullable). Depending on flag_reason one or both
    # may be null — e.g. an "unmatched" row has no tenant at all.
    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    lease_id = Column(
        String,
        ForeignKey("leases.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Review state.
    status = Column(String, nullable=False, default="pending_review")
    flag_reason = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    # Resolution.
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_user_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_payment_id = Column(
        String,
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason = Column(String, nullable=True)

    # Metadata.
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_user_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships.
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    lease = relationship("Lease", foreign_keys=[lease_id])
    resolution_payment = relationship("Payment", foreign_keys=[resolution_payment_id])
