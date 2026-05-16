#backend\app\schemas\rental.py

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


# ─── Unit ───

class UnitCreate(BaseModel):
    property_id: str
    name: str
    description: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqm: Optional[float] = None
    rent_amount: float


class UnitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqm: Optional[float] = None
    rent_amount: Optional[float] = None
    is_active: Optional[bool] = None


class UnitOut(BaseModel):
    id: str
    property_id: str
    name: str
    description: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqm: Optional[float] = None
    rent_amount: float
    is_active: bool
    created_at: datetime
    occupancy_status: Optional[str] = None
    tenant_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Tenant ───

class TenantCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: str
    alternative_phone: Optional[str] = None
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None

    next_of_kin_name: Optional[str] = None
    next_of_kin_relationship: Optional[str] = None
    next_of_kin_phone: Optional[str] = None
    next_of_kin_alt_phone: Optional[str] = None
    next_of_kin_email: Optional[str] = None

    employer_name: Optional[str] = None
    employer_location: Optional[str] = None
    employer_phone: Optional[str] = None
    employer_email: Optional[str] = None


class TenantUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    alternative_phone: Optional[str] = None
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None

    next_of_kin_name: Optional[str] = None
    next_of_kin_relationship: Optional[str] = None
    next_of_kin_phone: Optional[str] = None
    next_of_kin_alt_phone: Optional[str] = None
    next_of_kin_email: Optional[str] = None

    employer_name: Optional[str] = None
    employer_location: Optional[str] = None
    employer_phone: Optional[str] = None
    employer_email: Optional[str] = None


class TenantOut(BaseModel):
    id: str
    organization_id: str
    full_name: str
    email: Optional[str] = None
    phone: str
    alternative_phone: Optional[str] = None
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None

    next_of_kin_name: Optional[str] = None
    next_of_kin_relationship: Optional[str] = None
    next_of_kin_phone: Optional[str] = None
    next_of_kin_alt_phone: Optional[str] = None
    next_of_kin_email: Optional[str] = None

    employer_name: Optional[str] = None
    employer_location: Optional[str] = None
    employer_phone: Optional[str] = None
    employer_email: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True


class TenantDocumentOut(BaseModel):
    id: str
    tenant_id: str
    document_type: str
    file_url: str
    original_filename: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ─── Lease ───

class LeaseCreate(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: Optional[date] = None
    rent_amount: float
    deposit_amount: Optional[float] = 0
    billing_day: Optional[int] = 1

    # New fields
    move_in_date: Optional[date] = None
    signed_on_behalf_of: Optional[str] = None


class LeaseUpdate(BaseModel):
    end_date: Optional[date] = None
    rent_amount: Optional[float] = None
    billing_day: Optional[int] = None
    move_in_date: Optional[date] = None
    signed_on_behalf_of: Optional[str] = None


class LeaseOut(BaseModel):
    id: str
    organization_id: str
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: Optional[date] = None
    move_in_date: Optional[date] = None
    rent_amount: float
    deposit_amount: Optional[float] = None
    billing_day: int
    signed_on_behalf_of: Optional[str] = None
    signed_lease_url: Optional[str] = None
    status: str
    created_at: datetime
    # Enriched fields
    tenant_name: Optional[str] = None
    unit_name: Optional[str] = None
    property_name: Optional[str] = None

    class Config:
        from_attributes = True
