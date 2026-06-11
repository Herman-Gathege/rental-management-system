#backend\app\api\routes\charges.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
import uuid
from datetime import date

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.lease import Lease
from app.models.unit import Unit
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.charge import Charge
from app.models.payment import Payment
from app.services.audit_service import log_action
from app.services.messaging import notify_rent_due_for_charges
from app.services.billing_service import recompute_lease_settlement

router = APIRouter(prefix="/charges", tags=["Charges"])


def get_user_org(user, db):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


def lease_account_credit(db, lease_id, cache=None):
    """Lease-level credit (overpayment): total payments minus total charges for
    the lease, when positive. This is the money that isn't attached to any
    single charge -- a charge settles at most to balance 0, so overpayment lives
    on the lease. Returns 0.0 when the lease is square or owing.

    `cache` (a dict keyed by lease_id) lets list_charges compute this once per
    lease instead of once per charge row.
    """
    if cache is not None and lease_id in cache:
        return cache[lease_id]

    paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.lease_id == lease_id)
        .scalar()
    ) or 0
    charged = (
        db.query(func.coalesce(func.sum(Charge.amount), 0))
        .filter(Charge.lease_id == lease_id)
        .scalar()
    ) or 0

    credit = float(paid) - float(charged)
    credit = credit if credit > 0 else 0.0

    if cache is not None:
        cache[lease_id] = credit
    return credit


def enrich_charge(charge, db, credit_cache=None):
    lease = db.query(Lease).filter(Lease.id == charge.lease_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first() if lease else None
    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first() if lease else None
    prop = db.query(Property).filter(Property.id == unit.property_id).first() if unit else None

    amount = float(charge.amount)
    amount_paid = float(charge.amount_paid or 0)

    return {
        "id": charge.id, "organization_id": charge.organization_id,
        "lease_id": charge.lease_id, "amount": amount,
        "amount_paid": amount_paid,
        "balance": amount - amount_paid,
        # Lease-level overpayment (0 unless the tenant has paid beyond their
        # total charges). The rent dashboard shows this in green.
        "account_credit": lease_account_credit(db, charge.lease_id, credit_cache),
        "due_date": charge.due_date, "billing_month": charge.billing_month,
        "status": charge.status, "created_at": charge.created_at,
        "tenant_name": tenant.full_name if tenant else None,
        "unit_name": unit.name if unit else None,
        "property_name": prop.name if prop else None,
    }


@router.post("/generate-monthly")
def generate_monthly_charges(
    background_tasks: BackgroundTasks,
    billing_date: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id
    if not billing_date:
        billing_date = date.today()
    billing_month = billing_date.replace(day=1)
    active_leases = db.query(Lease).filter(Lease.organization_id == org_id, Lease.status == "active").all()

    # Collect the IDs of newly-created charges so we can fire one
    # rent_due_reminder per tenant in a single background task batch.
    new_charge_ids: list[str] = []
    affected_lease_ids: set[str] = set()
    skipped = 0

    for lease in active_leases:
        existing = db.query(Charge).filter(Charge.lease_id == lease.id, Charge.billing_month == billing_month).first()
        if existing:
            skipped += 1
            continue
        try:
            due = billing_date.replace(day=lease.billing_day)
        except ValueError:
            due = billing_date.replace(day=28)
        charge = Charge(id=str(uuid.uuid4()), organization_id=org_id, lease_id=lease.id, amount=lease.rent_amount, due_date=due, billing_month=billing_month, status="pending")
        db.add(charge)
        new_charge_ids.append(charge.id)
        affected_lease_ids.add(lease.id)

    created = len(new_charge_ids)

    # Re-settle each lease that got a new charge so any existing credit is
    # applied immediately and the new charge's amount_paid/status are correct.
    if affected_lease_ids:
        db.flush()
        for lid in affected_lease_ids:
            recompute_lease_settlement(db, lid)

    if created > 0:
        log_action(db, org_id, current_user.id, "billing", "charge", "batch", f"Generated {created} monthly charges for {billing_month}")
    db.commit()

    # Send rent_due_reminder WhatsApp to each tenant whose lease just
    # got a fresh charge. The helper opens its own DB session and
    # commits each send individually so one failure doesn't poison the rest.
    if new_charge_ids:
        background_tasks.add_task(notify_rent_due_for_charges, new_charge_ids)

    return {"message": f"Billing complete: {created} charges created, {skipped} already existed", "created": created, "skipped": skipped}


@router.get("/")
def list_charges(status: str = Query(None), lease_id: str = Query(None), property_id: str = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    today = date.today()
    query = db.query(Charge).filter(Charge.organization_id == membership.organization_id)

    if status == "overdue":
        # Option A: "overdue" = anything past its due date that still owes a
        # balance. This catches fully-unpaid AND partially-paid-but-late
        # charges, so late money never hides behind a "partial" status.
        query = query.filter(Charge.due_date < today, Charge.amount_paid < Charge.amount)
    elif status:
        query = query.filter(Charge.status == status)

    if lease_id:
        query = query.filter(Charge.lease_id == lease_id)
    if property_id:
        lease_ids = db.query(Lease.id).join(Unit, Lease.unit_id == Unit.id).filter(Unit.property_id == property_id).subquery()
        query = query.filter(Charge.lease_id.in_(lease_ids))

    charges = query.order_by(Charge.due_date.desc()).all()

    # A fully-unpaid charge that has aged past its due date displays as
    # "overdue". Partially-paid charges keep their "partial" status (their
    # balance is shown and flagged in the UI instead).
    for c in charges:
        if c.status == "pending" and c.due_date < today:
            c.status = "overdue"
    db.commit()

    # Compute each lease's credit once, not once per charge row.
    credit_cache: dict = {}
    return [enrich_charge(c, db, credit_cache) for c in charges]


@router.get("/{charge_id}")
def get_charge(charge_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    charge = db.query(Charge).filter(Charge.id == charge_id, Charge.organization_id == membership.organization_id).first()
    if not charge:
        raise HTTPException(status_code=404, detail="Charge not found")
    return enrich_charge(charge, db)