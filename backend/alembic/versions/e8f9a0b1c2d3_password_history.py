"""add password history table for reuse prevention

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-07-09 22:00:00.000000

Sprint 7 (MVP-1 follow-up) — password history.

Small table that stores each user's last N password hashes so we can reject
reuse on /auth/change-password and /auth/reset-password. Only bcrypt hashes
are stored — no plaintext, no reversibility. Pruning to N (configured in
password_history_service.KEEP_LAST) happens at write time, so this table
never grows beyond N * users rows.

Foreign key to users(id) with ondelete=CASCADE: if a user is deleted, their
history goes with them.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "password_history",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_password_history_user_id",
        "password_history",
        ["user_id"],
    )


def downgrade():
    op.drop_index("ix_password_history_user_id", table_name="password_history")
    op.drop_table("password_history")
