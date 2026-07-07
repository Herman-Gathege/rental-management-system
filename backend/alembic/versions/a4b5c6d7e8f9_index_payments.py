"""add indexes to payments for pagination performance

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-06-25 14:00:00.000000

Sprint 6.2 (#3) table performance. The payments list is filtered by
organization_id (+ optional lease/tenant/property) and ordered by
payment_date desc. Postgres does NOT auto-index foreign keys, so add:
  - ix_payments_organization_id  (every list query filters on it)
  - ix_payments_payment_date     (ORDER BY payment_date desc)
  - ix_payments_lease_id         (per-lease lookups + settlement sums)
  - ix_payments_tenant_id        (per-tenant lookups)
A composite (organization_id, payment_date) covers the common
"org list ordered by date" path in one index.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, Sequence[str], None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index("ix_payments_organization_id", "payments", ["organization_id"])
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"])
    op.create_index("ix_payments_lease_id", "payments", ["lease_id"])
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index(
        "ix_payments_org_date", "payments", ["organization_id", "payment_date"]
    )


def downgrade():
    op.drop_index("ix_payments_org_date", table_name="payments")
    op.drop_index("ix_payments_tenant_id", table_name="payments")
    op.drop_index("ix_payments_lease_id", table_name="payments")
    op.drop_index("ix_payments_payment_date", table_name="payments")
    op.drop_index("ix_payments_organization_id", table_name="payments")
