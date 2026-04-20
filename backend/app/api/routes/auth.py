from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.users import User
from app.models.organization import Organization
from app.schemas.user import UserRegister
from app.core.security import hash_password
from app.schemas.user import UserLogin
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.api.deps import get_current_user

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


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "organization_id": current_user.organization_id
    }