"""add amount_paid to charges

Revision ID: c3a9f1e7b2d4
Revises: b7f3c1e9a4d2
Create Date: 2026-06-06

Sprint 4.5 partial-payment fix.

Why
---
Payments are recorded as lump sums against a lease, never allocated to a
specific charge, and charges only had a status (pending/paid/overdue) with no
record of how much had actually been applied. So a partial payment (e.g. 12,000
against a 15,000 charge) was invisible on the charge -- it sat at the full
amount while the money only showed in the payments table.

What it does
-----------
1. Adds `amount_paid` (Numeric) to charges, default 0.
2. Backfills every existing charge by allocating each lease's total payments
   across its charges oldest-first (by due date), setting amount_paid AND
   re-deriving status under the new rule:
     paid    -> amount_paid >= amount
     partial -> 0 < amount_paid < amount
     overdue -> amount_paid == 0 AND past due
     pending -> amount_paid == 0 AND not yet due
   This makes existing data (e.g. partially-paid or overpaid leases) correct
   immediately, not just on the next payment.
"""
from alembic import op
import sqlalchemy as sa
from datetime import date


revision = "c3a9f1e7b2d4"
down_revision = "b7f3c1e9a4d2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "charges",
        sa.Column("amount_paid", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )

    conn = op.get_bind()
    today = date.today()

    lease_rows = conn.execute(sa.text("SELECT DISTINCT lease_id FROM charges")).fetchall()

    for (lease_id,) in lease_rows:
        total_paid = conn.execute(
            sa.text("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE lease_id = :lid"),
            {"lid": lease_id},
        ).scalar()
        remaining = float(total_paid or 0)

        charge_rows = conn.execute(
            sa.text(
                "SELECT id, amount, due_date FROM charges "
                "WHERE lease_id = :lid ORDER BY due_date ASC"
            ),
            {"lid": lease_id},
        ).fetchall()

        for cid, amount, due_date in charge_rows:
            amt = float(amount)
            applied = min(remaining, amt) if remaining > 0 else 0.0
            remaining -= applied

            if applied >= amt:
                status = "paid"
            elif applied > 0:
                status = "partial"
            elif due_date < today:
                status = "overdue"
            else:
                status = "pending"

            conn.execute(
                sa.text("UPDATE charges SET amount_paid = :ap, status = :st WHERE id = :cid"),
                {"ap": applied, "st": status, "cid": cid},
            )


def downgrade():
    op.drop_column("charges", "amount_paid")
