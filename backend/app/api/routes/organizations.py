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
from app.schemas.auth import RegisterInviteSchema
from app.core.roles import LANDLORD, ALL_ROLES, TENANT
from app.services.messaging import notify_org_invite
from app.services.tenant_linking import link_tenant_to_user
from app.core.security import hash_password
from app.core.jwt import create_access_token


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
        return {
            "requires_registration": True,
            "redirect": f"/register-invite/{token}"
        }

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

    # ─── Sprint 4.5: link the tenant record to this login ───
    # If this invite is for a TENANT, connect the matching Tenant row
    # (same org + same email, not already linked) so the tenant dashboard
    # can resolve their lease / charges / payments. Email is matched
    # case-insensitively + trimmed inside the helper, so casing/whitespace
    # can't silently break linking. Best-effort: skipped if no tenant matches.
    if invitation.role and invitation.role.name == TENANT:
        link_tenant_to_user(
            db,
            organization_id=invitation.organization_id,
            email=invitation.email,
            user_id=user.id,
        )

    # Mark invitation as accepted
    invitation.status = "accepted"
    db.commit()

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()

    return {
        "message": f"Welcome to {org.name}!",
        "organization_id": org.id,
        "role": invitation.role.name
    }


@router.post("/register-invite/{token}")
def register_invited_user(
    token: str,
    payload: RegisterInviteSchema,
    db: Session = Depends(get_db)
):
    # 1. Validate invitation
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.token == token,
            OrganizationInvitation.status == "pending"
        )
        .first()
    )

    if not invitation:
        raise HTTPException(
            status_code=404,
            detail="Invalid or expired invitation"
        )

    # 2. Ensure user does NOT already exist
    existing_user = (
        db.query(User)
        .filter(User.email == invitation.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # 3. Create user (FIXED PASSWORD BUG)
    user = User(
        email=invitation.email,
        password_hash=hash_password(payload.password),  # IMPORTANT FIX
        is_active=True,
        role_id=invitation.role_id
    )

    db.add(user)
    db.flush()  # ensures user.id is available

    # 4. Create organization membership
    membership = OrganizationMember(
        user_id=user.id,
        organization_id=invitation.organization_id,
        role_id=invitation.role_id
    )

    db.add(membership)

    # ─── Sprint 4.5: link the tenant record to this new login ───
    # New tenant accounts are created here (WhatsApp invite -> register).
    # Connect the matching Tenant row (same org + same email, not already
    # linked) so the dashboard resolves their data. Email is matched
    # case-insensitively + trimmed inside the helper. user.id is available
    # because db.flush() was already called above.
    if invitation.role and invitation.role.name == TENANT:
        link_tenant_to_user(
            db,
            organization_id=invitation.organization_id,
            email=invitation.email,
            user_id=user.id,
        )

    # 5. Mark invitation as accepted
    invitation.status = "accepted"

    db.commit()

    # 6. Create JWT
    access_token = create_access_token({
        "sub": user.id
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": invitation.role.name,
        "organization_id": invitation.organization_id
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
