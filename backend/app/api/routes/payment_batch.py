# backend/app/api/routes/payment_batch.py
"""
CSV batch payment endpoints (Sprint 4.5 spinoff).

/preview  — upload a statement CSV, get back a matched/flagged report. Read-only.
/commit   — record the rows the user confirmed (matched rows + any to which they
            assigned a lease). Each row goes through the SAME path as a manual
            payment: build Payment -> flush -> recompute_lease_settlement ->
            audit log -> WhatsApp receipt. Re-validates org ownership and skips
            duplicates server-side, so the client can't double-record.
/template — download an example CSV with the exact column order and
            Transaction format the parser expects (Sprint 7 cleanup).

Restricted to LANDLORD and FINANCE (money handling). Role is checked inline
from the caller's membership.

Sprint 6.2 (#7) — deposit-aware commit:
  When a lease still owes on its deposit, the batch commit:
    1) Rejects rows where row.amount < remaining deposit balance
       (skipped list, reason "insufficient_first_payment").
    2) Splits qualifying payments into TWO Payment rows sharing the same
       reference — one typed "deposit" for the remaining deposit balance,
       one typed "rent" for the excess (if any).
  Prior behaviour was to create a single "rent"-typed payment which silently
  bypassed billing_service's separate deposit pool, leaving deposits
  perpetually unpaid on the billing dashboard.
"""
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.charge import Charge
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


def _deposit_remaining_for_lease(db: Session, lease_id: str) -> float:
    """Return the remaining deposit balance for a lease (sum across all
    deposit-typed charges). 0.0 if fully paid or no deposit charge exists.
    Committed values only — this queries the DB, so caller must db.flush()
    any pending payments before calling if it wants them reflected."""
    remaining = float(
        db.query(func.coalesce(func.sum(Charge.amount - Charge.amount_paid), 0))
        .filter(
            Charge.lease_id == lease_id,
            Charge.charge_type == "deposit",
        )
        .scalar()
        or 0
    )
    return remaining if remaining > 0.01 else 0.0


# ─── Template (Sprint 7 cleanup) ───

@router.get("/template")
def download_template(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Downloadable M-Pesa statement CSV template. Headers + a few sample rows
    so the user knows what the parser expects (Date column, quoted Transaction
    with ACC / reference / TIMESTAMP payload, KES currency, Deposit amount)."""
    membership = _membership(db, current_user)
    _require_money_role(membership)

    csv_text = payment_batch_service.get_batch_payment_template_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="batch-payments-template.csv"'
        },
    )


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
    # One receipt per input row, not per Payment row. On a split (deposit +
    # rent), we notify with the DEPOSIT payment so the tenant sees "KES X
    # received" matching the full amount they sent for the deposit portion.
    # A trailing rent-only receipt would look like a partial acknowledgment.
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

        # ─── Sprint 6.2 (#7): deposit-first split + insufficient-first-payment reject ───
        deposit_remaining = _deposit_remaining_for_lease(db, row.lease_id)
        row_amount = float(row.amount)

        if deposit_remaining > 0 and row_amount < deposit_remaining:
            # First payment must cover the deposit in full. Partial deposits
            # aren't allowed. Landlord can save the row for review and clarify
            # with the tenant, or reject entirely.
            skipped.append({
                "reference": ref,
                "reason": (
                    f"insufficient first payment: KES {row_amount:,.0f} "
                    f"is less than deposit balance KES {deposit_remaining:,.0f}"
                ),
            })
            continue

        # Decide the payment shape. Three cases:
        #   (a) no deposit outstanding           -> one rent payment
        #   (b) deposit outstanding, exact cover -> one deposit payment
        #   (c) deposit outstanding, plus excess -> deposit payment + rent payment (share ref)
        payments_to_create = []
        if deposit_remaining <= 0:
            payments_to_create.append(("rent", row_amount))
        else:
            payments_to_create.append(("deposit", deposit_remaining))
            excess = row_amount - deposit_remaining
            if excess > 0.01:
                payments_to_create.append(("rent", excess))

        row_payment_ids = []
        for ptype, amt in payments_to_create:
            payment = Payment(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                tenant_id=row.tenant_id,
                lease_id=row.lease_id,
                amount=amt,
                payment_method="mpesa",
                payment_type=ptype,
                reference=ref,
                payment_date=row.payment_date,
            )
            db.add(payment)
            db.flush()  # visible to the next row's duplicate check + to settlement
            row_payment_ids.append((payment.id, ptype, amt))

            log_action(
                db=db,
                organization_id=org_id,
                user_id=current_user.id,
                action="payment",
                entity_type="payment",
                entity_id=payment.id,
                description=(
                    f"Batch payment of {amt} ({ptype}) recorded for "
                    f"{tenant.full_name} via mpesa (ref {ref})"
                ),
                new_values={
                    "amount": float(amt),
                    "payment_method": "mpesa",
                    "payment_type": ptype,
                    "reference": ref,
                    "tenant": tenant.full_name,
                    "batch": True,
                    "split_of_row_amount": row_amount if len(payments_to_create) > 1 else None,
                },
            )

            created.append({
                "payment_id": payment.id,
                "reference": ref,
                "tenant_name": tenant.full_name,
                "amount": float(amt),
                "payment_type": ptype,
            })

        leases_to_settle.add(row.lease_id)

        # One WhatsApp receipt per input row. Pick the deposit payment when
        # present (larger / primary), else the single rent payment.
        primary = next((pid for pid, ptype, _ in row_payment_ids if ptype == "deposit"), None)
        if primary is None and row_payment_ids:
            primary = row_payment_ids[0][0]
        if primary:
            receipt_ids.append(primary)

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
