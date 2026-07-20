#backend\app\schemas\ticket.py
from typing import Optional
from pydantic import BaseModel


# ─── Ticket ───

class TicketCreate(BaseModel):
    property_id: str
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None
    title: str
    description: str
    priority: str = "medium"
    category: str
    source: str = "tenant_portal"


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None


class TicketAssignPayload(BaseModel):
    assigned_to: Optional[str] = None   # null = unassign
    reason: Optional[str] = None


class TicketStatusPayload(BaseModel):
    reason: Optional[str] = None        # optional note recorded in a message


# ─── Message ───

class TicketMessageCreate(BaseModel):
    message: str
    is_internal: bool = False
    # Sprint 7 cleanup: optionally target an internal note at a single staff
    # user. Only honoured when is_internal=True; the service silently
    # nulls it on public messages. Recipient must be staff (landlord / PM /
    # finance) in the same organization — the service validates.
    recipient_id: Optional[str] = None


# ─── Config ───

class Config:
    from_attributes = True
