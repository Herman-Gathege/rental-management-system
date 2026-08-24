"""add whatsapp_integrations table

Revision ID: f8a1b2c3d4e5
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 15:17:59.000000

Environment-aware WhatsApp configuration.

Introduces the ``whatsapp_integrations`` table which maps a Meta
``phone_number_id`` to an ``organization_id``, scoped by ``environment``
(sandbox/production).

This table is the foundation for the transition from a single hardcoded
organization (sandbox) to a multi-tenant SaaS architecture (production)
where ``phone_number_id → WhatsAppIntegration → organization_id`` resolves
tenant ownership.

No raw credentials (access tokens, app secrets) are stored in this table —
those remain in the environment / application configuration system.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_integrations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("meta_phone_number_id", sa.String(), nullable=False),
        sa.Column("meta_business_account_id", sa.String(), nullable=True),
        sa.Column("environment", sa.String(), nullable=False, server_default="sandbox"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_whatsapp_integrations_organization_id",
        "whatsapp_integrations",
        ["organization_id"],
    )
    op.create_index(
        "ix_whatsapp_integrations_environment",
        "whatsapp_integrations",
        ["environment"],
    )
    op.create_index(
        "ix_whatsapp_integrations_is_active",
        "whatsapp_integrations",
        ["is_active"],
    )
    op.create_index(
        "ix_whatsapp_integrations_env_phone_number",
        "whatsapp_integrations",
        ["environment", "meta_phone_number_id"],
    )
    op.create_unique_constraint(
        "uniq_whatsapp_integrations_env_phone_number",
        "whatsapp_integrations",
        ["environment", "meta_phone_number_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uniq_whatsapp_integrations_env_phone_number",
        "whatsapp_integrations",
        type_="unique",
    )
    op.drop_index(
        "ix_whatsapp_integrations_env_phone_number",
        table_name="whatsapp_integrations",
    )
    op.drop_index(
        "ix_whatsapp_integrations_is_active",
        table_name="whatsapp_integrations",
    )
    op.drop_index(
        "ix_whatsapp_integrations_environment",
        table_name="whatsapp_integrations",
    )
    op.drop_index(
        "ix_whatsapp_integrations_organization_id",
        table_name="whatsapp_integrations",
    )
    op.drop_table("whatsapp_integrations")
