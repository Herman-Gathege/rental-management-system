"""add communication and support hub (sprint 6)

Revision ID: c5d8f1a9e640
Revises: a7e1c4b9f203
Create Date: 2026-06-24 10:00:00.000000

Sprint 6 evolves the existing `tickets` table (introduced for WhatsApp Phase 2
auto-ticketing) into the full support hub, and adds five new tables:
ticket_messages, ticket_attachments, ticket_assignments, notifications,
notification_preferences.

The tickets evolution is additive + a subject->title rename:
  - add property_id, unit_id, created_by, assigned_to, priority, category,
    opened_at, resolved_at, closed_at (all nullable; priority has a default)
  - add title, backfill title <- subject, backfill opened_at <- created_at,
    then drop subject
WhatsApp intake (source_phone, source_message_id, tenant_id, status, source,
description) is left intact so inbound auto-ticketing keeps working.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c5d8f1a9e640'
down_revision: Union[str, Sequence[str], None] = 'a7e1c4b9f203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ── evolve tickets ──
    op.add_column("tickets", sa.Column("property_id", sa.String(), nullable=True))
    op.add_column("tickets", sa.Column("unit_id", sa.String(), nullable=True))
    op.add_column("tickets", sa.Column("created_by", sa.String(), nullable=True))
    op.add_column("tickets", sa.Column("assigned_to", sa.String(), nullable=True))
    op.add_column("tickets", sa.Column("priority", sa.String(), nullable=False, server_default="medium"))
    op.add_column("tickets", sa.Column("category", sa.String(), nullable=True))
    op.add_column("tickets", sa.Column("opened_at", sa.DateTime(), nullable=True))
    op.add_column("tickets", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.add_column("tickets", sa.Column("closed_at", sa.DateTime(), nullable=True))

    # title: add nullable, backfill from subject, then enforce NOT NULL
    op.add_column("tickets", sa.Column("title", sa.String(), nullable=True))
    op.execute("UPDATE tickets SET title = subject WHERE title IS NULL")
    # existing rows: seed opened_at from created_at so lifecycle timestamps exist
    op.execute("UPDATE tickets SET opened_at = created_at WHERE opened_at IS NULL")
    op.alter_column("tickets", "title", nullable=False)

    # subject is now fully replaced by title
    op.drop_column("tickets", "subject")

    # FKs for the new scope/people columns
    op.create_foreign_key(
        "fk_tickets_property_id", "tickets", "properties",
        ["property_id"], ["id"], ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tickets_unit_id", "tickets", "units",
        ["unit_id"], ["id"], ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tickets_created_by", "tickets", "users",
        ["created_by"], ["id"],
    )
    op.create_foreign_key(
        "fk_tickets_assigned_to", "tickets", "users",
        ["assigned_to"], ["id"],
    )
    op.create_index("ix_tickets_property_id", "tickets", ["property_id"])
    op.create_index("ix_tickets_assigned_to", "tickets", ["assigned_to"])

    # ── ticket_messages ──
    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("ticket_id", sa.String(), nullable=False),
        sa.Column("sender_id", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])

    # ── ticket_attachments ──
    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("ticket_id", sa.String(), nullable=False),
        sa.Column("uploaded_by", sa.String(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_attachments_ticket_id", "ticket_attachments", ["ticket_id"])

    # ── ticket_assignments ──
    op.create_table(
        "ticket_assignments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("ticket_id", sa.String(), nullable=False),
        sa.Column("assigned_from", sa.String(), nullable=True),
        sa.Column("assigned_to", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_from"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_assignments_ticket_id", "ticket_assignments", ["ticket_id"])

    # ── notifications ──
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("notification_type", sa.String(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_organization_id", "notifications", ["organization_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    # ── notification_preferences ──
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user"),
    )


def downgrade():
    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_organization_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_ticket_assignments_ticket_id", table_name="ticket_assignments")
    op.drop_table("ticket_assignments")
    op.drop_index("ix_ticket_attachments_ticket_id", table_name="ticket_attachments")
    op.drop_table("ticket_attachments")
    op.drop_index("ix_ticket_messages_ticket_id", table_name="ticket_messages")
    op.drop_table("ticket_messages")

    # ── revert tickets evolution ──
    # Re-add subject, backfill from title, then drop the Sprint 6 columns.
    op.add_column("tickets", sa.Column("subject", sa.String(), nullable=True))
    op.execute("UPDATE tickets SET subject = title WHERE subject IS NULL")

    op.drop_index("ix_tickets_assigned_to", table_name="tickets")
    op.drop_index("ix_tickets_property_id", table_name="tickets")
    op.drop_constraint("fk_tickets_assigned_to", "tickets", type_="foreignkey")
    op.drop_constraint("fk_tickets_created_by", "tickets", type_="foreignkey")
    op.drop_constraint("fk_tickets_unit_id", "tickets", type_="foreignkey")
    op.drop_constraint("fk_tickets_property_id", "tickets", type_="foreignkey")

    op.drop_column("tickets", "title")
    op.drop_column("tickets", "closed_at")
    op.drop_column("tickets", "resolved_at")
    op.drop_column("tickets", "opened_at")
    op.drop_column("tickets", "category")
    op.drop_column("tickets", "priority")
    op.drop_column("tickets", "assigned_to")
    op.drop_column("tickets", "created_by")
    op.drop_column("tickets", "unit_id")
    op.drop_column("tickets", "property_id")
