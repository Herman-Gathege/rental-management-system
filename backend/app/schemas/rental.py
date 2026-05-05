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
    # Computed fields added in the route
    occupancy_status: Optional[str] = None
    tenant_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Tenant ───

class TenantCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: str
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None


class TenantUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None


class TenantOut(BaseModel):
    id: str
    organization_id: str
    full_name: str
    email: Optional[str] = None
    phone: str
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime

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


class LeaseUpdate(BaseModel):
    end_date: Optional[date] = None
    rent_amount: Optional[float] = None
    billing_day: Optional[int] = None


class LeaseOut(BaseModel):
    id: str
    organization_id: str
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: Optional[date] = None
    rent_amount: float
    deposit_amount: Optional[float] = None
    billing_day: int
    status: str
    created_at: datetime
    # Enriched fields added in route
    tenant_name: Optional[str] = None
    unit_name: Optional[str] = None
    property_name: Optional[str] = None

    class Config:
        from_attributes = True
