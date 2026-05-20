"""add messages table

Revision ID: d5f8b3e9c7a1
Revises: c4e7a9d2f8b1
Create Date: 2026-05-19 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f8b3e9c7a1'
down_revision: Union[str, Sequence[str], None] = 'c4e7a9d2f8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),

        # Recipient / sender
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),

        # Content
        sa.Column('message_type', sa.String(), nullable=False, server_default='notification'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('template_name', sa.String(), nullable=True),

        # Status
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Metadata
        sa.Column('channel', sa.String(), nullable=False, server_default='whatsapp'),
        sa.Column('triggered_by_user_id', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Helpful indexes for the queries we run most
    op.create_index('ix_messages_phone_number', 'messages', ['phone_number'])
    op.create_index('ix_messages_provider_message_id', 'messages', ['provider_message_id'])


def downgrade() -> None:
    op.drop_index('ix_messages_provider_message_id', table_name='messages')
    op.drop_index('ix_messages_phone_number', table_name='messages')
    op.drop_table('messages')
