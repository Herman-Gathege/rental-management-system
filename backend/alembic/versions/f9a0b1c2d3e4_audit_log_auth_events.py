"""audit_log: allow null organization_id, add ip_address for auth events

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-07-09 22:30:00.000000

Sprint 7 (MVP-1 follow-up) — auth event audit logging.

Auth events (login, failed login, password change/reset) don't always have
an organization context. A failed login with an unknown email has no user
and therefore no org; a legitimate user with no active membership can also
appear during migration windows. Two schema tweaks make audit_logs a fit
for both auth AND domain events:

  1. organization_id: NULL is now allowed. Existing rows stay as-is.
  2. ip_address: new nullable String. Populated for auth events via a
     get_client_ip() helper in audit_service. Older event types (leases,
     payments, tenants) leave it null — the schema is additive.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f9a0b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "audit_logs",
        "organization_id",
        existing_type=sa.String(),
        nullable=True,
    )
    op.add_column(
        "audit_logs",
        sa.Column("ip_address", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("audit_logs", "ip_address")
    # Note: reinstating NOT NULL would fail if any auth-event rows have a
    # null organization_id. In that case a manual cleanup (or a DELETE of
    # auth-event rows) is required before this downgrade will succeed.
    op.alter_column(
        "audit_logs",
        "organization_id",
        existing_type=sa.String(),
        nullable=False,
    )
