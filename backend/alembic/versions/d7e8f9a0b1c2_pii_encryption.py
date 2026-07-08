"""add tenant blind-index hash columns for PII encryption

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-07-08 20:00:00.000000

Sprint 7 (MVP-1) — PII encryption.

WHY THIS MIGRATION IS SMALLER THAN YOU MIGHT EXPECT:
The plaintext columns (phone, email, id_number, alternative_phone, and the
next-of-kin + emergency contact fields) are being converted from plain String
to EncryptedString at the MODEL level, not by an ALTER COLUMN here. The
underlying Postgres type stays TEXT — encryption happens in the application
layer via a SQLAlchemy TypeDecorator. So no column-type change is needed.

WHAT THIS MIGRATION DOES:
  1. Adds four blind-index hash columns to `tenants` for uniqueness/lookup:
     phone_hash, alternative_phone_hash, email_hash, id_number_hash.
     Each is an indexed 64-char hex string (HMAC-SHA256).

  2. Does NOT encrypt existing rows in-place. In dev, we start from an empty
     tenants table (documented in the deploy sequence). In production, a
     separate one-off script would read each row, encrypt the fields, and
     UPDATE — but that migration would be authored against real prod state.

FOR PRODUCTION LATER:
The backfill would look like:
    for tenant in db.query(Tenant).all():
        # touch each field so the ORM re-writes it encrypted, and the
        # before_update listener recomputes the hashes:
        tenant.phone = tenant.phone
        tenant.email = tenant.email
        # ... etc for each encrypted field
    db.commit()
Because the encryption module's decrypt_value() falls back to returning the
raw value on InvalidToken, a plaintext value in an encrypted column reads
back as itself — so this loop safely re-encrypts without a two-column dance.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'c6d7e8f9a0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("tenants", sa.Column("phone_hash", sa.String(length=64), nullable=True))
    op.add_column("tenants", sa.Column("alternative_phone_hash", sa.String(length=64), nullable=True))
    op.add_column("tenants", sa.Column("email_hash", sa.String(length=64), nullable=True))
    op.add_column("tenants", sa.Column("id_number_hash", sa.String(length=64), nullable=True))

    op.create_index("ix_tenants_phone_hash", "tenants", ["phone_hash"])
    op.create_index("ix_tenants_alternative_phone_hash", "tenants", ["alternative_phone_hash"])
    op.create_index("ix_tenants_email_hash", "tenants", ["email_hash"])
    op.create_index("ix_tenants_id_number_hash", "tenants", ["id_number_hash"])


def downgrade():
    op.drop_index("ix_tenants_id_number_hash", table_name="tenants")
    op.drop_index("ix_tenants_email_hash", table_name="tenants")
    op.drop_index("ix_tenants_alternative_phone_hash", table_name="tenants")
    op.drop_index("ix_tenants_phone_hash", table_name="tenants")
    op.drop_column("tenants", "id_number_hash")
    op.drop_column("tenants", "email_hash")
    op.drop_column("tenants", "alternative_phone_hash")
    op.drop_column("tenants", "phone_hash")
