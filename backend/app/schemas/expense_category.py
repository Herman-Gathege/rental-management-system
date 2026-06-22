#backend\app\schemas\expense_category.py

from pydantic import BaseModel
from typing import Optional


class ExpenseCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
