"""add ticket_id to messages

Revision ID: f2a8c5e1d6b3
Revises: e7c2a9d4f1b8
Create Date: 2026-05-21 12:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2a8c5e1d6b3"
down_revision = "e7c2a9d4f1b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("ticket_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_messages_ticket_id_tickets",
        "messages",
        "tickets",
        ["ticket_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_messages_ticket_id", "messages", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_ticket_id", table_name="messages")
    op.drop_constraint(
        "fk_messages_ticket_id_tickets",
        "messages",
        type_="foreignkey",
    )
    op.drop_column("messages", "ticket_id")
