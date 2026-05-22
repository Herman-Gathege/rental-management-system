"""add phone to organization_invitations

Revision ID: a4d7e2f9b5c8
Revises: 167323a571ac
Create Date: 2026-05-22 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a4d7e2f9b5c8"
down_revision = "167323a571ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organization_invitations",
        sa.Column("phone", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organization_invitations", "phone")
