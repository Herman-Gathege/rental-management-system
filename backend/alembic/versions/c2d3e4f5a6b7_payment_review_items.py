"""payment review items

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-20

Sprint 7 cleanup (Batch 3): new table for the payment reconciliation queue.

A payment_review_item is a CANDIDATE payment awaiting a decision — most
commonly a row from a CSV batch upload that couldn't be auto-matched
(unmatched tenant, multiple leases, duplicate reference, etc.). The
reviewer either applies it (creates a real Payment) or rejects it.

Not modelled on the payments table because a rejected candidate is not a
payment — we don't want it polluting revenue / collected / outstanding
queries. Applied items keep a resolution_payment_id link so the audit
trail is intact.
"""
from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_review_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), nullable=False),

        # Payment data as observed from the source (CSV row or manual entry).
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("payer_phone", sa.String(), nullable=True),
        sa.Column("payer_name", sa.String(), nullable=True),
        sa.Column("raw_transaction", sa.Text(), nullable=True),

        # Best-guess matches. Nullable — that's the whole point of review.
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("lease_id", sa.String(), nullable=True),

        # Review state.
        sa.Column("status", sa.String(), nullable=False, server_default="pending_review"),
        sa.Column("flag_reason", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),

        # Resolution.
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_user_id", sa.String(), nullable=True),
        sa.Column("resolution_payment_id", sa.String(), nullable=True),
        sa.Column("rejection_reason", sa.String(), nullable=True),

        # Metadata.
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by_user_id", sa.String(), nullable=True),

        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["lease_id"], ["leases.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["resolution_payment_id"], ["payments.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_payment_review_items_org_status",
        "payment_review_items",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_review_items_org_status",
        table_name="payment_review_items",
    )
    op.drop_table("payment_review_items")
