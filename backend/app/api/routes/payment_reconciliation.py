#backend\app\api\routes\payment_reconciliation.py
"""
Payment reconciliation endpoints — Sprint 7 cleanup (Batch 3).

Landlord + Finance only (money handling).

  POST   /payments/reconciliation                    → bulk save items
  GET    /payments/reconciliation                    → list (default: pending_review only)
  GET    /payments/reconciliation/{item_id}          → single item
  POST   /payments/reconciliation/{item_id}/apply    → create Payment, mark applied
  POST   /payments/reconciliation/{item_id}/reject   → mark rejected
  DELETE /payments/reconciliation/{item_id}          → hard delete (not applied)
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.core.roles import LANDLORD, FINANCE
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.services import payment_reconciliation_service as rec
from app.services.messaging import notify_payment_received

router = APIRouter(
    prefix="/payments/reconciliation",
    tags=["Payments - Reconciliation"],
)


# ─── Schemas ─────────────────────────────────────────────────────────────

class ReviewItemInput(BaseModel):
    amount: float
    payment_date: Optional[date] = None
    reference: Optional[str] = None
    payer_phone: Optional[str] = None
    payer_name: Optional[str] = None
    raw_transaction: Optional[str] = None
    tenant_id: Optional[str] = None
    lease_id: Optional[str] = None
    flag_reason: str
    notes: Optional[str] = None


class SaveReviewItemsPayload(BaseModel):
    items: List[ReviewItemInput]


class ApplyReviewItemPayload(BaseModel):
    tenant_id: str
    lease_id: str
    amount: float
    payment_date: date
    reference: Optional[str] = None
    payment_method: str = "mpesa"
    payment_type: str = "rent"
    notes: Optional[str] = None
    notify: bool = False   # send WhatsApp receipt after apply


class RejectReviewItemPayload(BaseModel):
    reason: Optional[str] = None


# ─── Access control ─────────────────────────────────────────────────────

def require_money_role(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reconciliation is money handling — Landlord + Finance only.
    (PM and Tenant have no reason to see or modify the review queue.)"""
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    role = membership.role.name if membership.role else None
    if role not in (LANDLORD, FINANCE):
        raise HTTPException(status_code=403, detail="Access denied")
    return user, membership, db


# ─── Endpoints ──────────────────────────────────────────────────────────

@router.post("")
def save_items(
    payload: SaveReviewItemsPayload,
    deps=Depends(require_money_role),
):
    user, membership, db = deps
    items_data = [i.dict() for i in payload.items]
    saved = rec.save_review_items(
        db, membership.organization_id, user.id, items_data
    )
    return {
        "saved_count": len(saved),
        "items": [rec.to_dict(i) for i in saved],
    }


@router.get("")
def list_items(
    status: Optional[str] = Query(
        None,
        description="Filter: pending_review | applied | rejected | all. Default: pending_review.",
    ),
    deps=Depends(require_money_role),
):
    user, membership, db = deps
    items = rec.list_review_items(
        db, membership.organization_id, status=status,
    )
    return [rec.to_dict(i) for i in items]


@router.get("/{item_id}")
def get_item(
    item_id: str,
    deps=Depends(require_money_role),
):
    user, membership, db = deps
    item = rec.get_review_item(db, membership.organization_id, item_id)
    return rec.to_dict(item)


@router.post("/{item_id}/apply")
def apply_item(
    item_id: str,
    payload: ApplyReviewItemPayload,
    background_tasks: BackgroundTasks,
    deps=Depends(require_money_role),
):
    user, membership, db = deps
    item, payment = rec.apply_review_item(
        db=db,
        organization_id=membership.organization_id,
        user_id=user.id,
        item_id=item_id,
        tenant_id=payload.tenant_id,
        lease_id=payload.lease_id,
        amount=payload.amount,
        payment_date=payload.payment_date,
        reference=payload.reference,
        payment_method=payload.payment_method,
        payment_type=payload.payment_type,
        notes=payload.notes,
    )

    # Fire-and-forget WhatsApp receipt if requested, same pattern as
    # the manual /payments/ endpoint.
    if payload.notify:
        background_tasks.add_task(notify_payment_received, payment.id)

    return {
        "item": rec.to_dict(item),
        "payment_id": payment.id,
    }


@router.post("/{item_id}/reject")
def reject_item(
    item_id: str,
    payload: RejectReviewItemPayload,
    deps=Depends(require_money_role),
):
    user, membership, db = deps
    item = rec.reject_review_item(
        db=db,
        organization_id=membership.organization_id,
        user_id=user.id,
        item_id=item_id,
        reason=payload.reason,
    )
    return rec.to_dict(item)


@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    deps=Depends(require_money_role),
):
    user, membership, db = deps
    rec.delete_review_item(
        db=db,
        organization_id=membership.organization_id,
        user_id=user.id,
        item_id=item_id,
    )
    return {"message": "Review item deleted"}
