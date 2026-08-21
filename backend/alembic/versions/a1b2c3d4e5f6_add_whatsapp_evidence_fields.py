"""add whatsapp evidence fields to payment review items

Revision ID: a1b2c3d4e5f6
Revises: f9a0b1c2d3e4
Create Date: 2026-08-18

WhatsApp payment-evidence workflow (Phase 1): extend PaymentReviewItem
with columns that capture WhatsApp-originated evidence without creating
a parallel payment system.

WhatsApp remains a source of evidence; the existing PaymentReviewItem
remains the reconciliation boundary. The new columns are additive and
nullable so existing rows are unaffected.
"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_review_items",
        sa.Column("source", sa.String(), nullable=True),
    )
    op.add_column(
        "payment_review_items",
        sa.Column("source_message_id", sa.String(), nullable=True),
    )
    op.add_column(
        "payment_review_items",
        sa.Column("extracted_reference", sa.String(), nullable=True),
    )
    op.add_column(
        "payment_review_items",
        sa.Column("extracted_amount", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "payment_review_items",
        sa.Column("message_timestamp", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "payment_review_items",
        sa.Column("payer_phone_hash", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_payment_review_items_payer_phone_hash",
        "payment_review_items",
        ["payer_phone_hash"],
    )
    op.create_index(
        "ix_payment_review_items_source",
        "payment_review_items",
        ["source"],
    )
    op.create_foreign_key(
        "fk_payment_review_items_source_message_id",
        "payment_review_items",
        "messages",
        ["source_message_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_payment_review_items_source_message_id",
        "payment_review_items",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_payment_review_items_source",
        table_name="payment_review_items",
    )
    op.drop_index(
        "ix_payment_review_items_payer_phone_hash",
        table_name="payment_review_items",
    )
    op.drop_column("payment_review_items", "payer_phone_hash")
    op.drop_column("payment_review_items", "message_timestamp")
    op.drop_column("payment_review_items", "extracted_amount")
    op.drop_column("payment_review_items", "extracted_reference")
    op.drop_column("payment_review_items", "source_message_id")
    op.drop_column("payment_review_items", "source")
