"""org settings, automation runs, message channel columns

Revision ID: c9d0e1f2a3b4
Revises: f8a1b2c3d4e5
Create Date: 2026-09-14 09:00:00.000000

System-wide upgrade foundation:

  * ``organization_settings`` - per-org invoice/reminder configuration and
    communication channel mode. Created lazily with defaults that match the
    behaviour that existed before this table (invoice on the 1st, reminder on
    the 10th, WhatsApp only), so nothing changes until an admin edits it.

  * ``automation_runs`` - one audit row per (organisation, job, run date).
    The unique constraint is the first idempotency layer for the scheduled
    jobs; the counters/message column are what make failures diagnosable.

  * ``messages.email_address`` + ``messages.idempotency_key`` and relaxing
    ``messages.phone_number`` to NULL, for the WhatsApp-first / SMTP-optional
    communication pipeline.

No existing data is rewritten and no column is dropped.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "f8a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization_settings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("invoice_generation_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "invoice_automation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("reminder_day", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "reminder_automation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("timezone", sa.String(), nullable=False, server_default="Africa/Nairobi"),
        sa.Column("channel_mode", sa.String(), nullable=False, server_default="whatsapp_only"),
        sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "email_payment_receipts",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_organization_settings_organization_id",
        "organization_settings",
        ["organization_id"],
        unique=True,
    )

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job", sa.String(), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="success"),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "organization_id",
            "job",
            "run_date",
            name="uq_automation_run_org_job_date",
        ),
    )
    op.create_index(
        "ix_automation_runs_organization_id",
        "automation_runs",
        ["organization_id"],
    )

    # ── Messages: multi-channel support ─────────────────────────────────────
    op.add_column(
        "messages",
        sa.Column("email_address", sa.String(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("idempotency_key", sa.String(), nullable=True),
    )
    op.create_index("ix_messages_email_address", "messages", ["email_address"])
    op.create_index("ix_messages_idempotency_key", "messages", ["idempotency_key"])
    # An email-only delivery legitimately has no phone number.
    op.alter_column("messages", "phone_number", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.drop_index("ix_messages_idempotency_key", table_name="messages")
    op.drop_index("ix_messages_email_address", table_name="messages")
    op.drop_column("messages", "idempotency_key")
    op.drop_column("messages", "email_address")
    op.drop_index("ix_automation_runs_organization_id", table_name="automation_runs")
    op.drop_table("automation_runs")
    op.drop_index(
        "ix_organization_settings_organization_id",
        table_name="organization_settings",
    )
    op.drop_table("organization_settings")
