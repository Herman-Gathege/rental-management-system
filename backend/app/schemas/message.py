#backend\app\schemas\message.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class MessageOut(BaseModel):
    id: str
    organization_id: str
    phone_number: str
    direction: str
    message_type: str
    content: str
    template_name: Optional[str] = None
    status: str
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    channel: str
    tenant_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SendTestMessageRequest(BaseModel):
    """Used by the manual test-send endpoint."""
    phone_number: str
    template_name: str
    variables: Dict[str, Any] = {}


class SendFreeformRequest(BaseModel):
    """Used by the manual free-form send endpoint."""
    phone_number: str
    body: str
