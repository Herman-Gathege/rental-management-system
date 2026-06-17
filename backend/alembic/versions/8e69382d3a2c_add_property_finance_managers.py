"""add property_finance_managers

Revision ID: 8e69382d3a2c
Revises: 5283c8dcc0f9
Create Date: 2026-06-17 14:43:09.966940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e69382d3a2c'
down_revision: Union[str, Sequence[str], None] = '5283c8dcc0f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "property_finance_managers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("property_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id", "user_id", name="uq_property_finance_manager"),
    )

def downgrade():
    op.drop_table("property_finance_managers")
