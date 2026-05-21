"""merge phase 2 with herman custom fields

Revision ID: 167323a571ac
Revises: bf148883c14e, f2a8c5e1d6b3
Create Date: 2026-05-21 19:32:01.443211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '167323a571ac'
down_revision: Union[str, Sequence[str], None] = ('bf148883c14e', 'f2a8c5e1d6b3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
