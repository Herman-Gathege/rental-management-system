from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.users import User
from app.models.organization import Organization
from app.schemas.user import UserRegister
from app.core.security import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    # check existing user
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # create organization
    org = Organization(name=user.organization_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    # create user
    new_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        organization_id=org.id
    )
    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}