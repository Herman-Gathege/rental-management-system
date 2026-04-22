# backend/app/db/seed_roles.py
from sqlalchemy.orm import Session
from app.models.role import Role
from app.core.roles import ALL_ROLES

def seed_roles(db: Session):
    existing = db.query(Role).count()
    if existing > 0:
        return

    for role_name in ALL_ROLES:
        role = Role(name=role_name)
        db.add(role)

    db.commit()
    print("Roles seeded")