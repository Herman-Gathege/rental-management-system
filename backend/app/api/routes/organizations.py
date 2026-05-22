#backend\app\api\routes\organizations.py

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.role import Role
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.organization_invitation import OrganizationInvitation
from app.schemas.organization import InviteRequest, InvitationOut
from app.core.roles import LANDLORD, ALL_ROLES
from app.services.messaging import notify_org_invite

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ─── Get My Organization ───

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
                "name": m.user.email.split("@")[0],
                "role": m.role.name
            }
            for m in members
        ],
        "my_role": membership.role.name
    }


# ─── Invite User to Organization ───


@router.post("/invite")
def invite_user(
    invite: InviteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verify current user is a LANDLORD in their org
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )

    if not membership:
        raise HTTPException(status_code=403, detail="You do not belong to any organization")

    if membership.role.name != LANDLORD:
        raise HTTPException(status_code=403, detail="Only landlords can invite users")

    org_id = membership.organization_id

    # 2. Validate the role
    if invite.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALL_ROLES}")

    if invite.role == LANDLORD:
        raise HTTPException(status_code=400, detail="Cannot invite another landlord")

    # 3. Check if user is already a member
    existing_user = db.query(User).filter(User.email == invite.email).first()
    if existing_user:
        existing_membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == existing_user.id,
                OrganizationMember.organization_id == org_id
            )
            .first()
        )
        if existing_membership:
            raise HTTPException(status_code=400, detail="User is already a member of this organization")

    # 4. Check for pending invitation
    pending = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.email == invite.email,
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.status == "pending"
        )
        .first()
    )
    if pending:
        raise HTTPException(status_code=400, detail="An invitation is already pending for this email")

    # 5. Get the role
    role = db.query(Role).filter(Role.name == invite.role).first()
    if not role:
        raise HTTPException(status_code=500, detail="Role not found")

    # 6. Create invitation
    invitation = OrganizationInvitation(
        id=str(uuid.uuid4()),
        email=invite.email,
        phone=invite.phone,                  # Phase 3 — optional WhatsApp delivery
        role_id=role.id,
        organization_id=org_id,
        token=str(uuid.uuid4()),
        status="pending"
    )
    db.add(invitation)
    db.commit()

    # Fire WhatsApp invite (best-effort, background). If phone is
    # missing, the helper logs a warning and returns without sending.
    if invite.phone:
        background_tasks.add_task(
            notify_org_invite,
            invitation.id,
            invite.phone,
        )

    return {
        "message": f"Invitation sent to {invite.email}",
        "invitation_id": invitation.id,
        "token": invitation.token,
        "whatsapp_queued": bool(invite.phone),
    }
   


# ─── Accept Invitation ───

@router.post("/accept-invite/{token}")
def accept_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.token == token,
            OrganizationInvitation.status == "pending"
        )
        .first()
    )

    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")

    # Check if user exists
    user = db.query(User).filter(User.email == invitation.email).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="User must register first before accepting the invitation"
        )

    # Check if already a member
    existing = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == invitation.organization_id
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    # Create membership
    member = OrganizationMember(
        user_id=user.id,
        organization_id=invitation.organization_id,
        role_id=invitation.role_id,
    )
    db.add(member)

    # Mark invitation as accepted
    invitation.status = "accepted"
    db.commit()

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()

    return {
        "message": f"Welcome to {org.name}!",
        "organization_id": org.id,
        "role": invitation.role.name
    }


# ─── List Pending Invitations ───

@router.get("/invitations")
def list_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )

    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")

    invitations = (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.organization_id == membership.organization_id)
        .all()
    )

    return [
        {
            "id": inv.id,
            "email": inv.email,
            "role": inv.role.name,
            "status": inv.status,
            "created_at": inv.created_at
        }
        for inv in invitations
    ]