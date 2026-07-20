"""ticket message recipient

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-07-20

Sprint 7 cleanup: add nullable recipient_id column to ticket_messages so
internal notes can optionally target a specific staff user instead of
broadcasting to the whole staff team.

NULL means broadcast (visible to any staff who can see the ticket) — the
existing behaviour. A user ID means targeted (visible only to sender +
landlord + that specific user). All existing rows stay NULL so nothing
changes for them.
"""
from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ticket_messages",
        sa.Column("recipient_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_ticket_messages_recipient_id_users",
        "ticket_messages",
        "users",
        ["recipient_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ticket_messages_recipient_id",
        "ticket_messages",
        ["recipient_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ticket_messages_recipient_id",
        table_name="ticket_messages",
    )
    op.drop_constraint(
        "fk_ticket_messages_recipient_id_users",
        "ticket_messages",
        type_="foreignkey",
    )
    op.drop_column("ticket_messages", "recipient_id")
