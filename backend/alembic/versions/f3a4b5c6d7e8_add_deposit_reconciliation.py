"""add deposit reconciliation fields to lease_inspections

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-06-25 12:00:00.000000

Sprint 6.2 (#7) Phase 3: deposit refund at move-out.
Adds three nullable numeric columns to lease_inspections, populated when a
move-out inspection is signed:
  deposit_held      — total deposit payments made on the lease
  deposit_refunded  — max(held - total_deduction_amount, 0)
  deposit_shortfall — max(total_deduction_amount - held, 0)
Nullable because move-in inspections and pre-existing rows never carry them.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, Sequence[str], None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("lease_inspections", sa.Column("deposit_held", sa.Numeric(12, 2), nullable=True))
    op.add_column("lease_inspections", sa.Column("deposit_refunded", sa.Numeric(12, 2), nullable=True))
    op.add_column("lease_inspections", sa.Column("deposit_shortfall", sa.Numeric(12, 2), nullable=True))


def downgrade():
    op.drop_column("lease_inspections", "deposit_shortfall")
    op.drop_column("lease_inspections", "deposit_refunded")
    op.drop_column("lease_inspections", "deposit_held")
