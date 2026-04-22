#backend/app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.users import User
from app.models.organization import Organization
from app.schemas.user import UserRegister
from app.core.security import hash_password
from app.schemas.user import UserLogin
from app.core.security import verify_password
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.api.deps import get_current_user
from app.services.email_service import send_email
import uuid
from datetime import datetime, timedelta
from app.models.role import Role
from app.core.roles import LANDLORD



router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):

    try:
        # 1️⃣ check existing user
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2️⃣ create organization (portfolio container)
        org = Organization(name=user.organization_name)
        db.add(org)
        db.flush()  # get org.id without committing

        # 3️⃣ fetch LANDLORD role
        landlord_role = db.query(Role).filter(Role.name == LANDLORD).first()
        if not landlord_role:
            raise HTTPException(status_code=500, detail="Roles not seeded")

        # 4️⃣ create user (global identity only)
        new_user = User(
            email=user.email,
            password_hash=hash_password(user.password),
        )
        db.add(new_user)
        db.flush()  # get user.id

        # 5️⃣ create organization membership (THIS is the real role)
        from app.models.organization_member import OrganizationMember

        membership = OrganizationMember(
            user_id=new_user.id,
            organization_id=org.id,
            role_id=landlord_role.id,
        )

        db.add(membership)

        # 6️⃣ commit everything together
        db.commit()

        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "organization_id": org.id,
            "role": LANDLORD
        }

    except Exception as e:
        db.rollback()
        raise e

# @router.post("/register")
# def register(user: UserRegister, db: Session = Depends(get_db)):

#     # 1️⃣ Check if user already exists
#     existing = db.query(User).filter(User.email == user.email).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     # 2️⃣ Create organization (first user becomes landlord)
#     org = Organization(name=user.organization_name)
#     db.add(org)
#     db.commit()
#     db.refresh(org)

#     # 3️⃣ Fetch LANDLORD role from DB (seeded at startup)
#     landlord_role = db.query(Role).filter(Role.name == LANDLORD).first()
#     if not landlord_role:
#         raise HTTPException(status_code=500, detail="Roles not seeded")

#     # 4️⃣ Create user and attach role
#     new_user = User(
#         email=user.email,
#         password_hash=hash_password(user.password),
#         organization_id=org.id,
#         role_id=landlord_role.id
#     )

#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     return {
#         "message": "User registered successfully",
#         "user_id": new_user.id,
#         "organization_id": org.id,
#         "role": LANDLORD
#     }



@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.id})
    refresh_token = create_refresh_token({"sub": db_user.id})

    # store refresh token
    db_user.refresh_token = refresh_token
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# @router.get("/me")
# def get_me(current_user: User = Depends(get_current_user)):
    
#     return {
#         "id": current_user.id,
#         "email": current_user.email,
#         "organization_id": current_user.organization_id,
#         "role": current_user.role.name.upper() if current_user.role else None
#     }

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.organization_member import OrganizationMember

    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )

    return {
        "id": current_user.id,
        "email": current_user.email,
        "organization_id": membership.organization_id if membership else None,
        "role": membership.role.name.upper() if membership and membership.role else None
    }




@router.post("/refresh")
def refresh_token(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)

    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == user_id).first()

    if not user or user.refresh_token != token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token({"sub": user.id})

    return {
        "access_token": new_access_token
    }



@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # generate token
    token = str(uuid.uuid4())

    # store token + expiry
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    reset_link = f"http://localhost:3000/reset-password?token={token}"

    print("RESET TOKEN:", token)  # for debugging only

    send_email(
        user.email,
        "Password Reset",
        f"<p>Click here to reset: {reset_link}</p>"
    )

    return {"message": "Reset email sent"}



# @router.post("/reset-password")
# def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.reset_token == token).first()

#     if not user:
#         raise HTTPException(status_code=400, detail="Invalid token")

#     user.password_hash = hash_password(new_password)
#     user.reset_token = None
#     db.commit()

#     return {"message": "Password updated"}

@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):

    # find user by token
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    # check expiry
    if not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    # update password
    user.password_hash = hash_password(new_password)

    # invalidate token after use
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {"message": "Password updated successfully"}