# backend/app/services/billing_service.py
"""
Charge settlement (Sprint 4.5 partial-payment fix).

Single source of truth for how payments settle against charges. Payments are
recorded as lump sums against a lease (not allocated to a specific charge), so
we derive each charge's settled amount by allocating the lease's total payments
across its charges oldest-first (by due date).

Call this whenever a lease's money picture changes:
  - a payment is recorded            (payments.py)
  - monthly charges are generated    (charges.py) -> applies existing credit
                                      to the new charge immediately

Status rule:
  paid     -> fully covered          (amount_paid >= amount)
  partial  -> some covered, balance remaining (0 < amount_paid < amount)
  overdue  -> nothing covered AND past the due date
  pending  -> nothing covered, not yet due

A partially-paid charge stays "partial" even when it's past due: the remaining
balance is the useful signal, and the due date shown in the row already tells
the user it's late.
"""
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.charge import Charge
from app.models.payment import Payment


def recompute_lease_settlement(db: Session, lease_id: str) -> None:
    total_paid = float(
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.lease_id == lease_id)
        .scalar()
    )

    charges = (
        db.query(Charge)
        .filter(Charge.lease_id == lease_id)
        .order_by(Charge.due_date.asc())  # oldest first
        .all()
    )

    today = date.today()
    remaining = total_paid

    for charge in charges:
        amt = float(charge.amount)
        applied = min(remaining, amt) if remaining > 0 else 0.0
        charge.amount_paid = applied
        remaining -= applied

        if applied >= amt:
            charge.status = "paid"
        elif applied > 0:
            charge.status = "partial"
        elif charge.due_date < today:
            charge.status = "overdue"
        else:
            charge.status = "pending"
