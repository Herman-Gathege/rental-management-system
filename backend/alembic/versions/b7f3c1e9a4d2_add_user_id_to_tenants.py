"""add user_id to tenants

Revision ID: b7f3c1e9a4d2
Revises: a4d7e2f9b5c8
Create Date: 2026-06-03

Sprint 4.5 -- link each Tenant to the User account it logs in with.

Why this migration exists
-------------------------
Until now the `tenants` table had no connection to `users`. A tenant who
accepts a portal invite becomes a User row (role TENANT) with an email, but
nothing tied that login back to their Tenant record. The tenant dashboard
needs that link to resolve "the logged-in tenant -> their lease / charges /
payments" reliably. Matching on email alone is fragile: it breaks the moment
the login email differs from the email typed into the tenant record, and
tenant.email is nullable.

What it does
-----------
1. Adds a nullable `user_id` FK column on `tenants`, ON DELETE SET NULL so
   deleting a user account never cascades away rental history (the tenant
   row, leases, charges and payments must survive account removal).
2. Backfills existing tenants: link a tenant to a user when their emails
   match AND that user is a TENANT member of the SAME organization. The org
   + role guard is what stops us mislinking a tenant row to, say, a landlord
   who happens to share an email -- the exact silent bug we chose this
   approach to avoid.

Going forward, the invite-accept flow sets user_id directly (see
organizations.py), so new tenants are linked the moment they register.

UPDATE ... FROM is Postgres-specific. That's fine -- this project is
Postgres 15 only.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7f3c1e9a4d2"
down_revision = "a4d7e2f9b5c8"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add the column (nullable -- existing rows have no link yet).
    op.add_column(
        "tenants",
        sa.Column("user_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tenants_user_id_users",
        source_table="tenants",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tenants_user_id", "tenants", ["user_id"])

    # 2. Backfill: email match, scoped to the same org, TENANT members only.
    op.execute(
        """
        UPDATE tenants AS t
        SET user_id = u.id
        FROM users AS u
        JOIN organization_members AS om ON om.user_id = u.id
        JOIN roles AS r ON r.id = om.role_id
        WHERE u.email = t.email
          AND om.organization_id = t.organization_id
          AND r.name = 'TENANT'
          AND t.email IS NOT NULL
          AND t.user_id IS NULL
        """
    )


def downgrade():
    op.drop_index("ix_tenants_user_id", table_name="tenants")
    op.drop_constraint("fk_tenants_user_id_users", "tenants", type_="foreignkey")
    op.drop_column("tenants", "user_id")