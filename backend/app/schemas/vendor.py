#backend\app\schemas\vendor.py

from pydantic import BaseModel
from typing import Optional


class VendorCreate(BaseModel):
    vendor_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    kra_pin: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    kra_pin: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
