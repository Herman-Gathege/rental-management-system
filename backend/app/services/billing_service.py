# backend/app/services/billing_service.py
"""
Charge settlement (Sprint 4.5 partial-payment fix; Sprint 6.2 deposit split).

Single source of truth for how payments settle against charges. Payments are
recorded as lump sums against a lease (not allocated to a specific charge), so
we derive each charge's settled amount by allocating the lease's payments
across its charges oldest-first (by due date).

Sprint 6.2 (#7) — deposits are separated from rent:
  - Payments are typed: payment_type in ("rent", "deposit").
  - Charges are typed:  charge_type  in ("rent", "deposit").
  - Rent payments settle ONLY rent charges (oldest-first).
  - Deposit payments settle ONLY the deposit charge(s).
  A rent payment can never absorb the deposit charge, and vice versa — the two
  money pools are allocated independently. This keeps dashboards honest:
  rent-collection figures never include deposit money.

Call this whenever a lease's money picture changes:
  - a payment is recorded            (payments.py)
  - monthly charges are generated    (charges.py) -> applies existing credit
                                      to the new charge immediately
  - a deposit charge is created      (leases.py create_lease)

Status rule (unchanged):
  paid     -> fully covered          (amount_paid >= amount)
  partial  -> some covered, balance remaining (0 < amount_paid < amount)
  overdue  -> nothing covered AND past the due date
  pending  -> nothing covered, not yet due
"""
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.charge import Charge
from app.models.payment import Payment


def _allocate(charges, total_paid, today):
    """Allocate a pool of money across a set of charges oldest-first,
    setting amount_paid + status on each. Mutates the charge objects."""
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


def recompute_lease_settlement(db: Session, lease_id: str) -> None:
    today = date.today()

    # ── Rent pool ──────────────────────────────────────────────────────
    rent_paid = float(
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.lease_id == lease_id, Payment.payment_type == "rent")
        .scalar()
    )
    rent_charges = (
        db.query(Charge)
        .filter(Charge.lease_id == lease_id, Charge.charge_type == "rent")
        .order_by(Charge.due_date.asc())  # oldest first
        .all()
    )
    _allocate(rent_charges, rent_paid, today)

    # ── Deposit pool ───────────────────────────────────────────────────
    deposit_paid = float(
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.lease_id == lease_id, Payment.payment_type == "deposit")
        .scalar()
    )
    deposit_charges = (
        db.query(Charge)
        .filter(Charge.lease_id == lease_id, Charge.charge_type == "deposit")
        .order_by(Charge.due_date.asc())
        .all()
    )
    _allocate(deposit_charges, deposit_paid, today)
