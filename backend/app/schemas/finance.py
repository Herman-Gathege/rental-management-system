#backend\app\schemas\finance.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


# ─── Charge ───

class ChargeOut(BaseModel):
    id: str
    organization_id: str
    lease_id: str
    amount: float
    due_date: date
    billing_month: date
    status: str
    created_at: datetime
    tenant_name: Optional[str] = None
    unit_name: Optional[str] = None
    property_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Payment ───

class PaymentCreate(BaseModel):
    tenant_id: str
    lease_id: str
    amount: float
    payment_method: str = "cash"  # cash / mpesa / bank

    # Sprint 7 cleanup: declare payment_type on the request schema.
    #
    # BUG THIS FIXES: previously this field was NOT declared here, so
    # Pydantic silently dropped whatever the frontend sent (Pydantic
    # default is to strip unknown fields). The endpoint then did
    # `getattr(payload, "payment_type", None) or "rent"`, which always
    # returned None → defaulted to "rent". Every payment — including
    # ones the user picked "deposit" for in the UI — was recorded as
    # rent. This made deposits collected appear as rent collected,
    # inflating rent-collection totals and leaving deposit charges
    # forever unpaid on the billing dashboard.
    #
    # Declaring it here lets Pydantic accept the field. The endpoint
    # still validates it against VALID_PAYMENT_TYPES = {"rent", "deposit"}.
    # Default stays "rent" so any caller (or older frontend build) that
    # omits the field still works — matches the original defensive behaviour.
    payment_type: str = "rent"

    reference: Optional[str] = None
    payment_date: date


class PaymentOut(BaseModel):
    id: str
    organization_id: str
    tenant_id: str
    lease_id: str
    amount: float
    payment_method: str
    payment_type: str = "rent"  # rent | deposit
    reference: Optional[str] = None
    payment_date: date
    created_at: datetime
    tenant_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Finance ───

class TenantBalance(BaseModel):
    tenant_id: str
    tenant_name: str
    total_charges: float
    total_payments: float
    balance: float        # signed: positive = owes, negative = in credit
    amount_owed: float    # max(0, balance)
    credit: float         # max(0, -balance)


class DashboardSummary(BaseModel):
    total_expected_rent: float
    total_collected: float
    total_overdue: float
    occupancy_rate: float
    total_units: int
    occupied_units: int