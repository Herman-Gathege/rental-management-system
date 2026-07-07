"""add otp_verifications table and user phone/phone_verified

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-06-26 10:00:00.000000

Sprint 6.2 (#6) WhatsApp OTP phone verification at landlord signup.

- users.phone            : landlord's phone captured at signup (nullable)
- users.phone_verified   : gate flag. Backfilled to TRUE for all EXISTING
                           users so no one already onboarded is locked out;
                           column default is FALSE so new signups must verify.
- otp_verifications      : transient one-time-code store (hashed codes).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c6d7e8f9a0b1'
down_revision: Union[str, Sequence[str], None] = 'b5c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ─── users: phone + phone_verified ───
    op.add_column("users", sa.Column("phone", sa.String(), nullable=True))
    # Add phone_verified with a server_default so existing rows get a value,
    # then backfill existing users to True, then drop the default so the
    # application default (False) governs new inserts.
    op.add_column(
        "users",
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Existing users predate verification — treat them as already verified.
    op.execute("UPDATE users SET phone_verified = TRUE")
    op.alter_column("users", "phone_verified", server_default=None)

    # ─── otp_verifications ───
    op.create_table(
        "otp_verifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False, server_default="phone_verification"),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_otp_verifications_user_id", "otp_verifications", ["user_id"])


def downgrade():
    op.drop_index("ix_otp_verifications_user_id", table_name="otp_verifications")
    op.drop_table("otp_verifications")
    op.drop_column("users", "phone_verified")
    op.drop_column("users", "phone")
