# backend\app\schemas\organization.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ─── Organization ───

class OrganizationOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationDetail(BaseModel):
    organization: OrganizationOut
    members: list
    my_role: str


# ─── Invitation ───

class InviteRequest(BaseModel):
    email: EmailStr
    role: str  # e.g. "PROPERTY_MANAGER", "FINANCE"

    # Phase 3: optional WhatsApp phone so the invite link can be
    # delivered via WhatsApp Cloud API. If omitted, the invitation
    # is still created with a token, but no notification fires —
    # the admin must share the token manually.
    phone: Optional[str] = None


class InvitationOut(BaseModel):
    id: str
    email: str
    phone: Optional[str] = None
    role: str
    status: str
    created_at: datetime


# ─── Property ───

class PropertyCreate(BaseModel):
    name: str
    address: str
    city: str
    country: str


class PropertyOut(BaseModel):
    id: str
    name: str
    address: str
    city: str
    country: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Property Manager Assignment ───

class AssignManagerRequest(BaseModel):
    user_id: str
