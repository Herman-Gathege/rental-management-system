"""add indexes to charges, audit_logs, tickets for pagination

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-06-25 15:00:00.000000

Sprint 6.2 (#3) table performance rollout. Same rationale as the payments
index migration: Postgres doesn't auto-index FKs, and these tables are all
filtered by organization_id and ordered by a date column.

IDEMPOTENT: uses CREATE INDEX IF NOT EXISTS / DROP INDEX IF EXISTS because some
indexes (e.g. ix_tickets_organization_id) may already exist from the original
table definition (SQLAlchemy index=True) or a prior partial run of this
migration. Without IF NOT EXISTS the whole migration aborts on the first
collision and the version pointer never advances.

  charges      : organization_id, lease_id, due_date, (org, due_date)
  audit_logs   : organization_id, entity_type, created_at, (org, created_at)
  tickets      : organization_id, property_id, tenant_id, created_at,
                 (org, created_at)
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'a4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (index_name, table, columns) — created with IF NOT EXISTS so pre-existing
# indexes are skipped instead of aborting the migration.
_INDEXES = [
    ("ix_charges_organization_id", "charges", "organization_id"),
    ("ix_charges_lease_id", "charges", "lease_id"),
    ("ix_charges_due_date", "charges", "due_date"),
    ("ix_charges_org_due", "charges", "organization_id, due_date"),
    ("ix_audit_logs_organization_id", "audit_logs", "organization_id"),
    ("ix_audit_logs_entity_type", "audit_logs", "entity_type"),
    ("ix_audit_logs_created_at", "audit_logs", "created_at"),
    ("ix_audit_logs_org_created", "audit_logs", "organization_id, created_at"),
    ("ix_tickets_organization_id", "tickets", "organization_id"),
    ("ix_tickets_property_id", "tickets", "property_id"),
    ("ix_tickets_tenant_id", "tickets", "tenant_id"),
    ("ix_tickets_created_at", "tickets", "created_at"),
    ("ix_tickets_org_created", "tickets", "organization_id, created_at"),
]


def upgrade():
    for name, table, cols in _INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})')


def downgrade():
    # Drop only the composite indexes this migration is responsible for; leave
    # single-column indexes that may predate it. IF EXISTS keeps this safe.
    for name in ("ix_tickets_org_created", "ix_audit_logs_org_created", "ix_charges_org_due"):
        op.execute(f'DROP INDEX IF EXISTS {name}')