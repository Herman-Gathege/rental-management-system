#backend\app\schemas\ticket.py
"""
Ticket Pydantic schemas.

Phase 2 only uses TicketOut internally (e.g. in the inbound handler return
value and for logging). Phase 3 will use these in the /tickets API routes.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TicketBase(BaseModel):
    subject: str
    description: str
    status: str = "open"
    source: str = "whatsapp"


class TicketCreate(TicketBase):
    organization_id: str
    tenant_id: Optional[str] = None
    source_phone: str
    source_message_id: Optional[str] = None


class TicketOut(TicketBase):
    id: str
    organization_id: str
    tenant_id: Optional[str]
    source_phone: str
    source_message_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
