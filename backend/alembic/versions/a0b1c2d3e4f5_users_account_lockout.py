"""users: failed_login_count + locked_until for account lockout

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c2d3e4
Create Date: 2026-07-09 23:00:00.000000

Sprint 7 (MVP-1 follow-up) — account lockout.

Adds two columns to users:
  - failed_login_count: int, default 0. Incremented on each wrong-password
    login; reset on successful login. Triggers a lockout at MAX_FAILURES=5
    (configured in app.services.account_lockout_service).
  - locked_until: datetime, nullable. Set to now+LOCK_DURATION when the
    counter crosses the threshold. Callers check "now < locked_until" to
    know if the account is currently locked.

Persistence rationale: kept in the users table (not Redis) so a Redis
flush can't accidentally unlock every account under active attack.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a0b1c2d3e4f5'
down_revision: Union[str, Sequence[str], None] = 'f9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")
