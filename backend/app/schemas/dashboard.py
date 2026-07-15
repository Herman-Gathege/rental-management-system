# backend/app/schemas/dashboard.py
"""
Response schemas for the role-based dashboard endpoints (Sprint 4.5).

These are intentionally thin. The dashboard service returns plain dicts of
already-computed values, and FastAPI coerces those dicts into these models for
the response -- so we never hand an ORM object to Pydantic and never need
orm_mode / from_attributes here. Keeping the fields scalar also means they
behave identically under Pydantic v1 and v2.
"""
from typing import Optional
from pydantic import BaseModel


class ManagerSummaryResponse(BaseModel):
    properties: int
    units: int
    occupied_units: int
    vacant_units: int
    tenants: int
    active_leases: int


class FinanceSummaryResponse(BaseModel):
    total_collected: float
    expected_rent: float
    outstanding_balance: float
    overdue_charges: int
    # Sprint 7 cleanup: deposits reported as two separate figures.
    # - deposits_expected  = sum of active-lease deposit_amount (obligation)
    # - deposits_collected = deposit-typed payments on active leases (received)
    # Default 0 so an older backend that only returns the legacy `deposits_held`
    # field still validates cleanly against this schema.
    deposits_expected: float = 0
    deposits_collected: float = 0


class TenantDashboardResponse(BaseModel):
    tenant: dict
    # Scalar unit/lease are the "primary" (newest active) lease, kept for
    # backward compatibility with the existing Dashboard page.
    unit: Optional[dict] = None
    lease: Optional[dict] = None
    # Aggregate account standing across ALL of the tenant's leases.
    balance: float
    amount_owed: float = 0
    credit: float = 0
    # Multi-lease: every lease this tenant holds, each with its own
    # property_name / unit_name / status / rent / balance.
    leases: list = []