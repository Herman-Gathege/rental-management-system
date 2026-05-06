#backend\app\api\routes\payments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import date

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.charge import Charge
from app.models.payment import Payment
from app.schemas.finance import PaymentCreate

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


# ─── Record Payment ───

@router.post("/")
def record_payment(
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id

    # Verify tenant belongs to org
    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == payload.tenant_id, Tenant.organization_id == org_id)
        .first()
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Verify lease belongs to org
    lease = (
        db.query(Lease)
        .filter(Lease.id == payload.lease_id, Lease.organization_id == org_id)
        .first()
    )
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    payment = Payment(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        tenant_id=payload.tenant_id,
        lease_id=payload.lease_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        reference=payload.reference,
        payment_date=payload.payment_date,
    )
    db.add(payment)

    # Auto-settle oldest pending/overdue charges
    remaining = float(payload.amount)
    pending_charges = (
        db.query(Charge)
        .filter(
            Charge.lease_id == payload.lease_id,
            Charge.status.in_(["pending", "overdue"])
        )
        .order_by(Charge.due_date.asc())
        .all()
    )

    for charge in pending_charges:
        if remaining <= 0:
            break
        charge_amount = float(charge.amount)
        if remaining >= charge_amount:
            charge.status = "paid"
            remaining -= charge_amount
        # Partial payments don't mark as paid

    db.commit()
    db.refresh(payment)

    return {
        "id": payment.id,
        "organization_id": payment.organization_id,
        "tenant_id": payment.tenant_id,
        "lease_id": payment.lease_id,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "reference": payment.reference,
        "payment_date": payment.payment_date,
        "created_at": payment.created_at,
        "tenant_name": tenant.full_name,
    }


# ─── List Payments ───

@router.get("/")
def list_payments(
    tenant_id: str = Query(None),
    lease_id: str = Query(None),
    property_id: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(Payment).filter(
        Payment.organization_id == membership.organization_id
    )

    if tenant_id:
        query = query.filter(Payment.tenant_id == tenant_id)

    if lease_id:
        query = query.filter(Payment.lease_id == lease_id)

    if property_id:
        from app.models.unit import Unit
        lease_ids = (
            db.query(Lease.id)
            .join(Unit, Lease.unit_id == Unit.id)
            .filter(Unit.property_id == property_id)
            .subquery()
        )
        query = query.filter(Payment.lease_id.in_(lease_ids))

    payments = query.order_by(Payment.payment_date.desc()).all()

    result = []
    for p in payments:
        tenant = db.query(Tenant).filter(Tenant.id == p.tenant_id).first()
        result.append({
            "id": p.id,
            "organization_id": p.organization_id,
            "tenant_id": p.tenant_id,
            "lease_id": p.lease_id,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "reference": p.reference,
            "payment_date": p.payment_date,
            "created_at": p.created_at,
            "tenant_name": tenant.full_name if tenant else None,
        })

    return result


# ─── Get Single Payment ───

@router.get("/{payment_id}")
def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.organization_id == membership.organization_id
        )
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    tenant = db.query(Tenant).filter(Tenant.id == payment.tenant_id).first()

    return {
        "id": payment.id,
        "organization_id": payment.organization_id,
        "tenant_id": payment.tenant_id,
        "lease_id": payment.lease_id,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "reference": payment.reference,
        "payment_date": payment.payment_date,
        "created_at": payment.created_at,
        "tenant_name": tenant.full_name if tenant else None,
    }
