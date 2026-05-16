"""extend leases and add inspection tables

Revision ID: c4e7a9d2f8b1
Revises: b9d3e7c8f1a2
Create Date: 2026-05-15 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e7a9d2f8b1'
down_revision: Union[str, Sequence[str], None] = 'b9d3e7c8f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Extend leases table ───
    op.add_column('leases', sa.Column('move_in_date', sa.Date(), nullable=True))
    op.add_column('leases', sa.Column('signed_on_behalf_of', sa.String(), nullable=True))
    op.add_column('leases', sa.Column('signed_lease_url', sa.String(), nullable=True))

    # ─── Create lease_inspections table ───
    op.create_table(
        'lease_inspections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('lease_id', sa.String(), nullable=False),
        sa.Column('inspection_type', sa.String(), nullable=False),
        sa.Column('inspection_date', sa.Date(), nullable=True),
        sa.Column('inspector_user_id', sa.String(), nullable=True),
        sa.Column('tenant_signature_data', sa.Text(), nullable=True),
        sa.Column('tenant_signed_name', sa.String(), nullable=True),
        sa.Column('tenant_signed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='draft'),
        sa.Column('total_deduction_amount', sa.Numeric(12, 2), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lease_id'], ['leases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspector_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ─── Create inspection_items table ───
    op.create_table(
        'inspection_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('inspection_id', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('condition', sa.String(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('photo_urls', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('deduction_amount', sa.Numeric(12, 2), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['lease_inspections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ─── Create inspection_notes table ───
    op.create_table(
        'inspection_notes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('inspection_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['lease_inspections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('inspection_notes')
    op.drop_table('inspection_items')
    op.drop_table('lease_inspections')

    op.drop_column('leases', 'signed_lease_url')
    op.drop_column('leases', 'signed_on_behalf_of')
    op.drop_column('leases', 'move_in_date')
