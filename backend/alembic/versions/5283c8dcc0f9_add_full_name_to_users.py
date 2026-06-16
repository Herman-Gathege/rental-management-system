"""add full_name to users

Revision ID: 5283c8dcc0f9
Revises: 7e7bca84abec
Create Date: 2026-06-16 18:15:48.236525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5283c8dcc0f9'
down_revision: Union[str, Sequence[str], None] = '7e7bca84abec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("users", sa.Column("full_name", sa.String(), nullable=True))

def downgrade():
    op.drop_column("users", "full_name")