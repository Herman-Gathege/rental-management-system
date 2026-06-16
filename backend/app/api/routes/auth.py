#backend/app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

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
from app.core.roles import LANDLORD, TENANT
from app.models.organization_member import OrganizationMember
from app.services.tenant_linking import link_tenant_to_user



router = APIRouter(prefix="/auth", tags=["Auth"])


# ─── Profile request bodies (Sprint 4.5 profile menu) ───
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


def _me_payload(user: User, db: Session) -> dict:
    """Shared shape for GET /me and PUT /me so the frontend always gets the
    same fields (now including full_name)."""
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "organization_id": membership.organization_id if membership else None,
        "role": membership.role.name.upper() if membership and membership.role else None,
    }


@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):

    try:
        # 1️⃣ check existing user
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2️⃣ create user FIRST
        new_user = User(
            email=user.email,
            password_hash=hash_password(user.password),
        )
        db.add(new_user)
        db.flush()  # ✅ now we have new_user.id

        # 3️⃣ create organization WITH owner_id
        org = Organization(
            name=user.organization_name,
            owner_id=new_user.id   # 🔥 FIX HERE
        )
        db.add(org)
        db.flush()

        # 4️⃣ fetch LANDLORD role
        landlord_role = db.query(Role).filter(Role.name == LANDLORD).first()
        if not landlord_role:
            raise HTTPException(status_code=500, detail="Roles not seeded")

        # 5️⃣ create membership
        from app.models.organization_member import OrganizationMember

        membership = OrganizationMember(
            user_id=new_user.id,
            organization_id=org.id,
            role_id=landlord_role.id,
        )
        db.add(membership)

        # 6️⃣ commit everything
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


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.id})
    refresh_token = create_refresh_token({"sub": db_user.id})

    # store refresh token (critical login path — commit this first)
    db_user.refresh_token = refresh_token
    db.commit()

    # ─── Sprint 4.5 safety net: self-heal tenant linking on login ───
    # If this account is a TENANT in an org but its Tenant row was never
    # linked (e.g. created outside the invite flow, like a hand-added tenant),
    # connect it now via the shared helper (same-org, same-email after
    # trim+lower, not already linked). Idempotent: a no-op once linked.
    # Fully isolated and best-effort — login already succeeded above, so a
    # linking hiccup must never turn into a failed login.
    try:
        memberships = (
            db.query(OrganizationMember)
            .filter(OrganizationMember.user_id == db_user.id)
            .all()
        )
        linked_any = False
        for m in memberships:
            if m.role and m.role.name == TENANT:
                if link_tenant_to_user(
                    db,
                    organization_id=m.organization_id,
                    email=db_user.email,
                    user_id=db_user.id,
                ):
                    linked_any = True
        if linked_any:
            db.commit()
    except Exception:
        db.rollback()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _me_payload(current_user, db)


@router.put("/me")
def update_me(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the signed-in user's profile (currently just their name)."""
    if payload.full_name is not None:
        # Trim; store NULL rather than an empty string.
        current_user.full_name = payload.full_name.strip() or None
    db.commit()
    db.refresh(current_user)
    return _me_payload(current_user, db)


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the signed-in user's password. Requires the current password."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="New password must be at least 8 characters"
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


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