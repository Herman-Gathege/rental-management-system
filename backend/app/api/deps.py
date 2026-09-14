# backend/app/api/deps.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.core.jwt import decode_token
from app.core.roles import LANDLORD
from app.models.users import User
from app.models.organization_member import OrganizationMember

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_user_org_membership(user: User, db: Session) -> OrganizationMember:
    """Return the signed-in user's organization membership, or 403.

    Shared helper so every router resolves the caller's organization and role
    the same way. Memberships were originally one-per-user; we keep the
    ``.first()`` lookup semantics the existing routes already rely on.
    """
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def require_landlord(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Landlord-only dependency.

    Returns ``(user, membership, db)`` so routes can pull ``org_id`` straight
    off the membership without a second query — the same shape
    ``bulk_uploads.require_landlord`` already exposed.
    """
    membership = get_user_org_membership(user, db)
    if not membership.role or membership.role.name != LANDLORD:
        raise HTTPException(
            status_code=403,
            detail="Only landlords can perform this action",
        )
    return user, membership, db
    
