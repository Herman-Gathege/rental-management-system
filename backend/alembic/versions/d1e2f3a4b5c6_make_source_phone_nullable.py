"""make source_phone nullable on tickets

Revision ID: d1e2f3a4b5c6
Revises: c5d8f1a9e640
Create Date: 2026-06-24 20:00:00.000000

source_phone was NOT NULL from the WhatsApp Phase 2 schema. User-created
tickets (tenant portal, manager, landlord) have no phone number, so this
column must be nullable. WhatsApp-created tickets still populate it.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c5d8f1a9e640'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column("tickets", "source_phone", nullable=True)


def downgrade():
    # Back-fill empty string before re-adding NOT NULL so existing rows pass
    op.execute("UPDATE tickets SET source_phone = '' WHERE source_phone IS NULL")
    op.alter_column("tickets", "source_phone", nullable=False)
