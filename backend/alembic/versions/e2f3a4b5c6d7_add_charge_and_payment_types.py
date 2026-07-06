"""add charge_type and payment_type for deposit separation

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-06-25 10:00:00.000000

Sprint 6.2 (#7): separate security deposits from rent.
  - charges.charge_type   : "rent" (default) | "deposit"
  - payments.payment_type : "rent" (default) | "deposit"

Both columns are NOT NULL with a server default of 'rent'. All existing rows
are therefore backfilled to 'rent' automatically by the server_default, which
matches how money was treated before this change (everything was rent).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add with a server_default so every existing row is backfilled to 'rent'.
    op.add_column(
        "charges",
        sa.Column("charge_type", sa.String(), nullable=False, server_default="rent"),
    )
    op.add_column(
        "payments",
        sa.Column("payment_type", sa.String(), nullable=False, server_default="rent"),
    )

    # Backfill is handled by server_default above; make it explicit for clarity
    # / any edge rows created mid-migration.
    op.execute("UPDATE charges SET charge_type = 'rent' WHERE charge_type IS NULL")
    op.execute("UPDATE payments SET payment_type = 'rent' WHERE payment_type IS NULL")

    # Drop the server_default now that existing rows are populated; the model
    # default (default="rent") handles new rows at the ORM layer. Keeping a DB
    # server_default is also fine, but dropping it keeps the schema clean and
    # forces the app to be explicit.
    op.alter_column("charges", "charge_type", server_default=None)
    op.alter_column("payments", "payment_type", server_default=None)


def downgrade():
    op.drop_column("payments", "payment_type")
    op.drop_column("charges", "charge_type")
