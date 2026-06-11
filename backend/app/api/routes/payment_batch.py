# backend/app/api/routes/payment_batch.py
"""
CSV batch payment endpoints (Sprint 4.5 spinoff).

/preview — upload a statement CSV, get back a matched/flagged report. Read-only.
/commit  — record the rows the user confirmed (matched rows + any to which they
           assigned a lease). Each row goes through the SAME path as a manual
           payment: build Payment -> flush -> recompute_lease_settlement ->
           audit log -> WhatsApp receipt. Re-validates org ownership and skips
           duplicates server-side, so the client can't double-record.

Restricted to LANDLORD and FINANCE (money handling). Role is checked inline
from the caller's membership, so this doesn't depend on the pending
role-security pass.
"""
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.payment import Payment
from app.core.roles import LANDLORD, FINANCE
from app.services import payment_batch_service
from app.services.audit_service import log_action
from app.services.billing_service import recompute_lease_settlement
from app.services.messaging import notify_payment_received

router = APIRouter(prefix="/payments/batch", tags=["Payments - Batch"])


# ─── Schemas ───

class BatchPaymentRow(BaseModel):
    tenant_id: str
    lease_id: str
    amount: float
    reference: Optional[str] = None
    payment_date: date


class BatchCommitPayload(BaseModel):
    payments: List[BatchPaymentRow]
    notify: bool = True  # send WhatsApp receipts for recorded payments


# ─── Helpers ───

def _membership(db: Session, user: User) -> OrganizationMember:
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def _require_money_role(membership: OrganizationMember) -> None:
    role = membership.role.name if membership.role else None
    if role not in (LANDLORD, FINANCE):
        raise HTTPException(status_code=403, detail="Access denied")


# ─── Preview (read-only) ───

@router.post("/preview")
async def preview_batch(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require_money_role(membership)

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    content = await file.read()
    parsed = payment_batch_service.parse_statement(content)
    if not parsed:
        raise HTTPException(status_code=400, detail="No data rows found in the file")

    return payment_batch_service.build_preview(
        db, membership.organization_id, parsed
    )


# ─── Commit (records payments) ───

@router.post("/commit")
def commit_batch(
    payload: BatchCommitPayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _membership(db, current_user)
    _require_money_role(membership)
    org_id = membership.organization_id

    created = []
    skipped = []
    leases_to_settle = set()
    receipt_ids = []

    for row in payload.payments:
        ref = row.reference

        tenant = (
            db.query(Tenant)
            .filter(Tenant.id == row.tenant_id, Tenant.organization_id == org_id)
            .first()
        )
        lease = (
            db.query(Lease)
            .filter(Lease.id == row.lease_id, Lease.organization_id == org_id)
            .first()
        )
        if not tenant or not lease:
            skipped.append({"reference": ref, "reason": "tenant or lease not found"})
            continue
        if lease.tenant_id != tenant.id:
            skipped.append({"reference": ref, "reason": "lease does not belong to tenant"})
            continue
        if not row.amount or row.amount <= 0:
            skipped.append({"reference": ref, "reason": "invalid amount"})
            continue

        # Duplicate guard: same M-Pesa reference already recorded (also catches
        # an earlier row in this same batch, since it's flushed below).
        if ref:
            dup = (
                db.query(Payment.id)
                .filter(Payment.organization_id == org_id, Payment.reference == ref)
                .first()
            )
            if dup:
                skipped.append({"reference": ref, "reason": "duplicate reference"})
                continue

        payment = Payment(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            tenant_id=row.tenant_id,
            lease_id=row.lease_id,
            amount=row.amount,
            payment_method="mpesa",
            reference=ref,
            payment_date=row.payment_date,
        )
        db.add(payment)
        db.flush()  # visible to the next row's duplicate check + to settlement
        leases_to_settle.add(row.lease_id)

        log_action(
            db=db,
            organization_id=org_id,
            user_id=current_user.id,
            action="payment",
            entity_type="payment",
            entity_id=payment.id,
            description=(
                f"Batch payment of {row.amount} recorded for {tenant.full_name} "
                f"via mpesa (ref {ref})"
            ),
            new_values={
                "amount": float(row.amount),
                "payment_method": "mpesa",
                "reference": ref,
                "tenant": tenant.full_name,
                "batch": True,
            },
        )

        created.append({
            "payment_id": payment.id,
            "reference": ref,
            "tenant_name": tenant.full_name,
            "amount": float(row.amount),
        })
        receipt_ids.append(payment.id)

    # Re-settle each affected lease once, after all its payments are flushed.
    for lease_id in leases_to_settle:
        recompute_lease_settlement(db, lease_id)

    db.commit()

    if payload.notify:
        for pid in receipt_ids:
            background_tasks.add_task(notify_payment_received, pid)

    return {
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
    }