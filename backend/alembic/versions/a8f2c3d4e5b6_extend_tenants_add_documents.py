"""extend tenants and add tenant documents

Revision ID: a8f2c3d4e5b6
Revises: e5c3f2a18b47
Create Date: 2026-05-15 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8f2c3d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'e5c3f2a18b47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Extend tenants table ───
    op.add_column('tenants', sa.Column('alternative_phone', sa.String(), nullable=True))

    # Next of kin fields
    op.add_column('tenants', sa.Column('next_of_kin_name', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('next_of_kin_relationship', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('next_of_kin_phone', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('next_of_kin_alt_phone', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('next_of_kin_email', sa.String(), nullable=True))

    # Employer fields
    op.add_column('tenants', sa.Column('employer_name', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('employer_location', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('employer_phone', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('employer_email', sa.String(), nullable=True))

    # ─── Create tenant_documents table ───
    op.create_table(
        'tenant_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('uploaded_by_user_id', sa.String(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    # Drop tenant_documents table
    op.drop_table('tenant_documents')

    # Drop tenant columns
    op.drop_column('tenants', 'employer_email')
    op.drop_column('tenants', 'employer_phone')
    op.drop_column('tenants', 'employer_location')
    op.drop_column('tenants', 'employer_name')

    op.drop_column('tenants', 'next_of_kin_email')
    op.drop_column('tenants', 'next_of_kin_alt_phone')
    op.drop_column('tenants', 'next_of_kin_phone')
    op.drop_column('tenants', 'next_of_kin_relationship')
    op.drop_column('tenants', 'next_of_kin_name')

    op.drop_column('tenants', 'alternative_phone')
