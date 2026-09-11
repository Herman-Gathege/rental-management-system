import sys, uuid
sys.path.insert(0, "/app")

from app.db.session import SessionLocal
from app.core.security import hash_password
from app.core.roles import LANDLORD
from app.models.users import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role

# NOTE: keep this a normal, public TLD. The login schema validates with
# EmailStr, which rejects special-use domains such as .local / .test, so a
# "demo@landlord.local" style address fails with HTTP 422 before auth runs.
EMAIL = "demo@alphaone.africa"
PASSWORD = "Demo1234!"
FULL_NAME = "Demo Landlord"
PHONE = "+254700000000"
ORG_NAME = "Riverside Property Management"

db = SessionLocal()
try:
    if db.query(User).filter(User.email == EMAIL).first():
        print(f"User {EMAIL} already exists. Skipping.")
        sys.exit(0)

    role = db.query(Role).filter(Role.name == LANDLORD).first()
    if not role:
        print(f"Role '{LANDLORD}' not found. Run seed_roles first.")
        sys.exit(1)

    user = User(
        id=str(uuid.uuid4()),
        email=EMAIL, full_name=FULL_NAME,
        password_hash=hash_password(PASSWORD),
        is_active=True, phone=PHONE, phone_verified=True,
        role_id=role.id, failed_login_count=0,
    )
    db.add(user); db.flush()

    org = Organization(id=str(uuid.uuid4()), name=ORG_NAME, owner_id=user.id)
    db.add(org); db.flush()

    membership = OrganizationMember(
        id=str(uuid.uuid4()), user_id=user.id,
        organization_id=org.id, role_id=role.id,
    )
    db.add(membership); db.commit()

    print()
    print("=" * 60)
    print("DEMO ORG CREATED")
    print("=" * 60)
    print(f"Organization:  {ORG_NAME}")
    print(f"Org ID:        {org.id}")
    print(f"Landlord email: {EMAIL}")
    print(f"Password:       {PASSWORD}")
    print("=" * 60)
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    sys.exit(1)
finally:
    db.close()
