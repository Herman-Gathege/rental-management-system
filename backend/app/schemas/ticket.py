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


# ─── Config ───

class Config:
    from_attributes = True
