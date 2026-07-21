#backend\app\services\payment_reconciliation_service.py
"""
Payment reconciliation service — Sprint 7 cleanup (Batch 3).

A "payment review item" is a candidate payment awaiting a decision.
Sources:
  - CSV batch upload rows that couldn't be auto-matched (unmatched tenant,
    multiple active leases, no active lease, duplicate reference, parse
    error). See payment_batch_service.build_preview for the origin of
    these statuses — the reason strings map directly here.
  - Manually flagged rows (future).

Lifecycle:
  pending_review  →  applied   (creates a real Payment; item links to it)
  pending_review  →  rejected  (item marked with rejection_reason)
  pending_review  →  (deleted) (hard delete only if not applied)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment_review_item import PaymentReviewItem
from app.models.payment import Payment
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.services.audit_service import log_action
from app.services.billing_service import recompute_lease_settlement


VALID_FLAG_REASONS = {
    "unmatched",         # no tenant matched the payer phone
    "multiple_leases",   # tenant matched but has multiple active leases
    "no_active_lease",   # tenant matched but has no active lease
    "duplicate",         # reference matches an existing recorded payment
    "parse_error",       # couldn't read amount / phone from the source row
    "amount_mismatch",   # amount doesn't match any expected rent (future)
    "manual_flag",       # human decided to hold this for review
}

VALID_STATUSES = {"pending_review", "applied", "rejected"}


def to_dict(item: PaymentReviewItem) -> dict:
    """Serialise for API responses. Includes tenant name when we have one so
    the review UI has enough context to act without a second lookup."""
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "amount": float(item.amount) if item.amount is not None else 0,
        "payment_date": item.payment_date.isoformat() if item.payment_date else None,
        "reference": item.reference,
        "payer_phone": item.payer_phone,
        "payer_name": item.payer_name,
        "raw_transaction": item.raw_transaction,
        "tenant_id": item.tenant_id,
        "tenant_name": item.tenant.full_name if item.tenant else None,
        "lease_id": item.lease_id,
        "status": item.status,
        "flag_reason": item.flag_reason,
        "notes": item.notes,
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        "resolved_by_user_id": item.resolved_by_user_id,
        "resolution_payment_id": item.resolution_payment_id,
        "rejection_reason": item.rejection_reason,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


# ─── Save (bulk) ─────────────────────────────────────────────────────────

def save_review_items(
    db: Session,
    organization_id: str,
    user_id: str,
    items: List[dict],
) -> List[PaymentReviewItem]:
    """Bulk-save flagged items. Called from the batch upload flow when the
    user clicks 'Save unresolved for review'.

    Skips items whose reference already exists in a pending review row —
    saving the same CSV twice shouldn't clone the queue.
    """
    saved: list[PaymentReviewItem] = []

    # Existing pending references — used to skip duplicates from repeated
    # 'save' clicks on the same CSV.
    existing_refs: set[str] = set()
    if any(i.get("reference") for i in items):
        rows = (
            db.query(PaymentReviewItem.reference)
            .filter(
                PaymentReviewItem.organization_id == organization_id,
                PaymentReviewItem.status == "pending_review",
                PaymentReviewItem.reference.isnot(None),
            )
            .all()
        )
        existing_refs = {r for (r,) in rows if r}

    for input_item in items:
        ref = input_item.get("reference")
        if ref and ref in existing_refs:
            continue

        flag_reason = input_item.get("flag_reason") or "manual_flag"
        if flag_reason not in VALID_FLAG_REASONS:
            flag_reason = "manual_flag"

        # Parse date if it came in as an ISO string (frontend usually sends str).
        pd = input_item.get("payment_date")
        if isinstance(pd, str):
            try:
                pd = date.fromisoformat(pd)
            except ValueError:
                pd = None

        item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            amount=input_item["amount"],
            payment_date=pd,
            reference=ref,
            payer_phone=input_item.get("payer_phone"),
            payer_name=input_item.get("payer_name"),
            raw_transaction=input_item.get("raw_transaction"),
            tenant_id=input_item.get("tenant_id"),
            lease_id=input_item.get("lease_id"),
            status="pending_review",
            flag_reason=flag_reason,
            notes=input_item.get("notes"),
            created_by_user_id=user_id,
        )
        db.add(item)
        db.flush()
        if ref:
            existing_refs.add(ref)
        saved.append(item)

    log_action(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        action="save_for_review",
        entity_type="payment_review",
        entity_id=str(uuid.uuid4()),
        description=f"Saved {len(saved)} payment(s) for later review",
        new_values={"count": len(saved)},
    )

    db.commit()
    return saved


# ─── List / Get ──────────────────────────────────────────────────────────

def list_review_items(
    db: Session,
    organization_id: str,
    status: Optional[str] = None,
) -> List[PaymentReviewItem]:
    """List review items. Default filters to `pending_review`. Pass
    status='all' to see everything (useful for audit / history view)."""
    q = db.query(PaymentReviewItem).filter(
        PaymentReviewItem.organization_id == organization_id
    )

    if status and status != "all":
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Choose from: {sorted(VALID_STATUSES | {'all'})}",
            )
        q = q.filter(PaymentReviewItem.status == status)
    elif not status:
        # Default view = pending only.
        q = q.filter(PaymentReviewItem.status == "pending_review")

    return q.order_by(PaymentReviewItem.created_at.desc()).all()


def get_review_item(
    db: Session,
    organization_id: str,
    item_id: str,
) -> PaymentReviewItem:
    item = (
        db.query(PaymentReviewItem)
        .filter(
            PaymentReviewItem.id == item_id,
            PaymentReviewItem.organization_id == organization_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    return item


# ─── Apply ───────────────────────────────────────────────────────────────

def apply_review_item(
    db: Session,
    organization_id: str,
    user_id: str,
    item_id: str,
    tenant_id: str,
    lease_id: str,
    amount: float,
    payment_date: date,
    reference: Optional[str] = None,
    payment_method: str = "mpesa",
    payment_type: str = "rent",
    notes: Optional[str] = None,
) -> tuple[PaymentReviewItem, Payment]:
    """Apply → create a real Payment, mark the item applied.

    Accepts finalized values from the caller rather than trusting the
    item's stored values — the reviewer may have corrected the
    tenant/lease/amount before applying (that's the whole point of the
    review flow). We validate the finalized tenant + lease belong to
    the calling org.
    """
    item = get_review_item(db, organization_id, item_id)
    if item.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail=f"Item is already {item.status}",
        )

    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == tenant_id, Tenant.organization_id == organization_id)
        .first()
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    lease = (
        db.query(Lease)
        .filter(Lease.id == lease_id, Lease.organization_id == organization_id)
        .first()
    )
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    if lease.tenant_id != tenant.id:
        raise HTTPException(
            status_code=400,
            detail="Lease does not belong to this tenant",
        )

    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if payment_type not in ("rent", "deposit"):
        raise HTTPException(
            status_code=400,
            detail="payment_type must be 'rent' or 'deposit'",
        )

    # Duplicate reference guard — same rule as manual + batch payments.
    if reference:
        dup = (
            db.query(Payment.id)
            .filter(
                Payment.organization_id == organization_id,
                Payment.reference == reference,
            )
            .first()
        )
        if dup:
            raise HTTPException(
                status_code=400,
                detail=f"A payment with reference '{reference}' already exists",
            )

    # Create the payment.
    payment = Payment(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        tenant_id=tenant_id,
        lease_id=lease_id,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        payment_date=payment_date,
        payment_type=payment_type,
    )
    db.add(payment)
    db.flush()

    # Re-settle the lease against its charges.
    recompute_lease_settlement(db, lease_id)

    # Mark the review item as applied.
    item.status = "applied"
    item.resolved_at = datetime.utcnow()
    item.resolved_by_user_id = user_id
    item.resolution_payment_id = payment.id
    if notes:
        item.notes = notes

    # Two audit entries: one for the payment creation (matches the audit
    # trail for manual and batch payments), one for the review resolution.
    log_action(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        action="payment",
        entity_type="payment",
        entity_id=payment.id,
        description=(
            f"{payment_type.capitalize()} payment of {amount} recorded for "
            f"{tenant.full_name} via {payment_method} (from review queue, "
            f"ref {reference or 'none'})"
        ),
        new_values={
            "amount": float(amount),
            "payment_method": payment_method,
            "payment_type": payment_type,
            "reference": reference,
            "tenant": tenant.full_name,
            "review_item_id": item.id,
        },
    )
    log_action(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        action="apply_review",
        entity_type="payment_review",
        entity_id=item.id,
        description=f"Applied review item — created payment {payment.id}",
        new_values={
            "payment_id": payment.id,
            "amount": float(amount),
            "tenant_id": tenant_id,
            "lease_id": lease_id,
        },
    )

    db.commit()
    db.refresh(item)
    db.refresh(payment)

    return item, payment


# ─── Reject ──────────────────────────────────────────────────────────────

def reject_review_item(
    db: Session,
    organization_id: str,
    user_id: str,
    item_id: str,
    reason: Optional[str] = None,
) -> PaymentReviewItem:
    """Reject → mark rejected with the reviewer's reason. No Payment is
    created. Item stays in the table (visible via the rejected filter)
    so the decision is auditable."""
    item = get_review_item(db, organization_id, item_id)
    if item.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail=f"Item is already {item.status}",
        )

    item.status = "rejected"
    item.resolved_at = datetime.utcnow()
    item.resolved_by_user_id = user_id
    item.rejection_reason = reason or ""

    log_action(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        action="reject_review",
        entity_type="payment_review",
        entity_id=item.id,
        description=(
            f"Rejected review item (amount {item.amount}) — "
            f"{reason or 'no reason given'}"
        ),
        new_values={"reason": reason},
    )

    db.commit()
    db.refresh(item)
    return item


# ─── Delete ──────────────────────────────────────────────────────────────

def delete_review_item(
    db: Session,
    organization_id: str,
    user_id: str,
    item_id: str,
) -> None:
    """Hard-delete a review item. Blocked for applied items — they're
    linked to a real Payment and the audit trail relies on them.
    Rejected and pending items can be cleaned up."""
    item = get_review_item(db, organization_id, item_id)
    if item.status == "applied":
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete an applied review item — "
                "it is linked to a recorded payment"
            ),
        )

    log_action(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        action="delete_review",
        entity_type="payment_review",
        entity_id=item.id,
        description=(
            f"Deleted review item (amount {item.amount}, "
            f"status {item.status})"
        ),
    )

    db.delete(item)
    db.commit()
