#backend\app\schemas\expense.py

from pydantic import BaseModel
from typing import Optional
from datetime import date


# ─── Expense ───

class ExpenseCreate(BaseModel):
    property_id: str
    category_id: str
    title: str
    amount: float
    expense_date: date

    unit_id: Optional[str] = None
    vendor_id: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    property_id: Optional[str] = None
    category_id: Optional[str] = None
    unit_id: Optional[str] = None
    vendor_id: Optional[str] = None
    title: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[date] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


# ─── Workflow action payloads ───

class ExpenseRejectPayload(BaseModel):
    reason: Optional[str] = None


class ExpensePayPayload(BaseModel):
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
