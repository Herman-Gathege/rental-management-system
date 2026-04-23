from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/me")
def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )

    if not membership:
        raise HTTPException(status_code=404, detail="User has no organization")

    org = db.query(Organization).filter(
        Organization.id == membership.organization_id
    ).first()

    members = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.organization_id == org.id)
        .all()
    )

    return {
        "organization": {
            "id": org.id,
            "name": org.name,
            "created_at": org.created_at
        },
        "members": [
            {
                "user_id": m.user.id,
                "email": m.user.email,
                "role": m.role.name
            }
            for m in members
        ],
        "my_role": membership.role.name
    }