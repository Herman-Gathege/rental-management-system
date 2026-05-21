"""merge migration heads

Revision ID: c01b66b37b2b
Revises: 604e7c13abcc, d5f8b3e9c7a1
Create Date: 2026-05-21 09:08:43.959909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c01b66b37b2b'
down_revision: Union[str, Sequence[str], None] = ('604e7c13abcc', 'd5f8b3e9c7a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
