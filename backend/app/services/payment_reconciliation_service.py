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
    "unmatched",
    "multiple_leases",
    "no_active_lease",
    "duplicate",
    "parse_error",
    "amount_mismatch",
    "manual_flag",
}

VALID_STATUSES = {"pending_review", "applied", "rejected"}


def to_dict(item: PaymentReviewItem) -> dict:
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
) -> tuple[List[PaymentReviewItem], List[dict]]:
    """Bulk-save flagged items. Returns (saved, skipped) so the caller can
    tell the user WHY nothing was saved when dedup catches everything —
    otherwise "Saved 0" looks like a bug.

    Skips:
      - reference already exists in a pending review row (already queued)
      - reference matches an already-recorded payment (already resolved)
      - amount missing / non-positive (backend requires it)
    """
    saved: list[PaymentReviewItem] = []
    skipped: list[dict] = []

    # Existing pending references — used to skip duplicates from repeated
    # 'save' clicks on the same CSV.
    existing_pending_refs: set[str] = set()
    rows = (
        db.query(PaymentReviewItem.reference)
        .filter(
            PaymentReviewItem.organization_id == organization_id,
            PaymentReviewItem.status == "pending_review",
            PaymentReviewItem.reference.isnot(None),
        )
        .all()
    )
    existing_pending_refs = {r for (r,) in rows if r}

    # References that are already recorded as real payments — no point
    # queueing those for review either; they're settled.
    existing_payment_refs: set[str] = set()
    if items:
        candidate_refs = {i.get("reference") for i in items if i.get("reference")}
        if candidate_refs:
            rows = (
                db.query(Payment.reference)
                .filter(
                    Payment.organization_id == organization_id,
                    Payment.reference.in_(list(candidate_refs)),
                )
                .all()
            )
            existing_payment_refs = {r for (r,) in rows if r}

    for input_item in items:
        ref = input_item.get("reference")

        # Amount is required — defensive check even though frontend filters.
        try:
            amount = float(input_item.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            skipped.append({
                "reference": ref,
                "reason": "invalid or missing amount",
            })
            continue

        if ref and ref in existing_pending_refs:
            skipped.append({
                "reference": ref,
                "reason": "already in review queue",
            })
            continue

        if ref and ref in existing_payment_refs:
            skipped.append({
                "reference": ref,
                "reason": "already recorded as a payment",
            })
            continue

        flag_reason = input_item.get("flag_reason") or "manual_flag"
        if flag_reason not in VALID_FLAG_REASONS:
            flag_reason = "manual_flag"

        # Parse date if it came in as an ISO string.
        pd = input_item.get("payment_date")
        if isinstance(pd, str):
            try:
                pd = date.fromisoformat(pd)
            except ValueError:
                pd = None

        item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            amount=amount,
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
            existing_pending_refs.add(ref)
        saved.append(item)

    log_action(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        action="save_for_review",
        entity_type="payment_review",
        entity_id=str(uuid.uuid4()),
        description=(
            f"Saved {len(saved)} payment(s) for later review "
            f"(skipped {len(skipped)})"
        ),
        new_values={"saved": len(saved), "skipped": len(skipped)},
    )

    db.commit()
    return saved, skipped


# ─── List / Get ──────────────────────────────────────────────────────────

def list_review_items(
    db: Session,
    organization_id: str,
    status: Optional[str] = None,
) -> List[PaymentReviewItem]:
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

    recompute_lease_settlement(db, lease_id)

    item.status = "applied"
    item.resolved_at = datetime.utcnow()
    item.resolved_by_user_id = user_id
    item.resolution_payment_id = payment.id
    if notes:
        item.notes = notes

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
