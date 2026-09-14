#backend\app\api\routes\charges.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_
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
from app.core.roles import FINANCE
from app.services.audit_service import log_action
from app.services.messaging import notify_rent_due_for_charges
from app.services.billing_service import recompute_lease_settlement
from app.services.automation_service import generate_monthly_invoices
from app.services.finance_scope import assigned_finance_property_ids, lease_ids_for_properties

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

    # Sprint 7 cleanup: charge_type on every row (with 'rent' fallback for any
    # historical rent charges that might have NULL — deposit charges have
    # always been created with an explicit type).
    ctype = charge.charge_type or "rent"

    # Sprint 7 cleanup: lease-level credit surfaces ONLY on rent rows.
    #
    # `account_credit` is a lease-wide sum (total paid - total charged, when
    # positive). Previously we stamped it on every charge of the lease, which
    # made a fully-settled deposit row still show a phantom "-5,000" credit
    # whenever the tenant had over-paid or under-paid rent elsewhere.
    #
    # Now deposit rows always show their own per-charge balance (0 when fully
    # paid, positive when unpaid). Any lease-level surplus is confined to the
    # rent row — that's where deficit / overpayment belongs, and it stops
    # deposit rows from lying about their own state.
    if ctype == "deposit":
        credit = 0.0
    else:
        credit = lease_account_credit(db, charge.lease_id, credit_cache)

    return {
        "id": charge.id, "organization_id": charge.organization_id,
        "lease_id": charge.lease_id, "amount": amount,
        "amount_paid": amount_paid,
        "balance": amount - amount_paid,
        "account_credit": credit,
        "due_date": charge.due_date, "billing_month": charge.billing_month,
        "status": charge.status,
        "charge_type": ctype,
        "created_at": charge.created_at,
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
    # The generation loop now lives in automation_service so this manual
    # trigger and the scheduled job share one implementation (and one set of
    # idempotency guarantees). See app/services/automation_service.py.
    result = generate_monthly_invoices(
        db,
        org_id,
        billing_date=billing_date,
        triggered_by_user_id=current_user.id,
    )
    new_charge_ids = result["charge_ids"]
    created = result["created"]
    skipped = result["skipped"]
    db.commit()

    # Send rent_due_reminder WhatsApp to each tenant whose lease just
    # got a fresh charge. The helper opens its own DB session and
    # commits each send individually so one failure doesn't poison the rest.
    if new_charge_ids:
        background_tasks.add_task(notify_rent_due_for_charges, new_charge_ids)

    return {"message": f"Billing complete: {created} charges created, {skipped} already existed", "created": created, "skipped": skipped}


@router.get("/")
def list_charges(
    status: str = Query(None),
    charge_type: str = Query(None),
    lease_id: str = Query(None),
    property_id: str = Query(None),
    search: str = Query(None, max_length=100),
    limit: int = Query(None, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List charges.

    Pagination (Sprint 6.2 #3): when `limit` is provided, returns a paginated
    envelope { items, total, limit, offset }. When `limit` is omitted, returns
    the bare list (unchanged) so existing callers keep working.

    Type filter (rent / deposit): charges already carry `charge_type` (see
    models/charge.py) — this exposes it as a query filter so the billing page
    can show rent-only or deposit-only views. Historical rows may have a NULL
    charge_type from before the column existed and are treated as rent,
    matching the fallback `enrich_charge` already applies.
    """
    membership = get_user_org(current_user, db)
    org_id = membership.organization_id
    role = membership.role.name if membership.role else None
    today = date.today()
    query = db.query(Charge).filter(Charge.organization_id == org_id)

    if charge_type:
        if charge_type not in ("rent", "deposit"):
            raise HTTPException(
                status_code=400,
                detail="charge_type must be 'rent' or 'deposit'",
            )
        if charge_type == "rent":
            query = query.filter(
                (Charge.charge_type == "rent") | (Charge.charge_type.is_(None))
            )
        else:
            query = query.filter(Charge.charge_type == "deposit")

    if status == "overdue":
        # Option A: "overdue" = anything past its due date that still owes a
        # balance. This catches fully-unpaid AND partially-paid-but-late
        # charges, so late money never hides behind a "partial" status.
        query = query.filter(Charge.due_date < today, Charge.amount_paid < Charge.amount)
    elif status == "pending":
        # "pending" = still unpaid and not yet past its due date. Charges whose
        # due date has passed are reported as "overdue" (see above), so scoping
        # this filter to due_date >= today keeps the two mutually exclusive —
        # otherwise every aged unpaid charge would show up under both filters
        # and be relabelled "overdue" inside the pending list.
        query = query.filter(Charge.status == "pending", Charge.due_date >= today)
    elif status:
        query = query.filter(Charge.status == status)

    if lease_id:
        query = query.filter(Charge.lease_id == lease_id)
    if search and search.strip():
        # Page-local table search: match the tenant name for this charge's
        # lease. Charge rows carry no free-text field of their own.
        term = f"%{search.strip()}%"
        matching_lease_ids = [
            row[0]
            for row in db.query(Lease.id)
            .join(Tenant, Tenant.id == Lease.tenant_id)
            .filter(
                Lease.organization_id == org_id,
                Tenant.full_name.ilike(term),
            )
        ]
        query = query.filter(Charge.lease_id.in_(matching_lease_ids or [""]))
    if property_id:
        lease_ids = db.query(Lease.id).join(Unit, Lease.unit_id == Unit.id).filter(Unit.property_id == property_id).subquery()
        query = query.filter(Charge.lease_id.in_(lease_ids))

    # Finance scoping: a FINANCE user only sees charges for the properties
    # they're assigned to. Empty assignment => nothing (strict).
    if role == FINANCE:
        prop_ids = assigned_finance_property_ids(db, current_user.id, org_id)
        scoped_lease_ids = lease_ids_for_properties(db, prop_ids)
        if not scoped_lease_ids:
            return {"items": [], "total": 0, "limit": limit, "offset": offset} if limit is not None else []
        query = query.filter(Charge.lease_id.in_(scoped_lease_ids))

    query = query.order_by(Charge.due_date.desc())

    def _process(charges):
        # A fully-unpaid charge that has aged past its due date displays as
        # "overdue". Partially-paid charges keep their "partial" status (their
        # balance is shown and flagged in the UI instead).
        mutated = False
        for c in charges:
            if c.status == "pending" and c.due_date < today:
                c.status = "overdue"
                mutated = True
        if mutated:
            db.commit()
        # Compute each lease's credit once, not once per charge row.
        credit_cache: dict = {}
        return [enrich_charge(c, db, credit_cache) for c in charges]

    # Paginated envelope when limit is given.
    if limit is not None:
        total = query.count()
        charges = query.offset(offset).limit(limit).all()
        return {
            "items": _process(charges),
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # Backward-compatible bare list.
    charges = query.all()
    return _process(charges)


@router.get("/{charge_id}")
def get_charge(charge_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_user_org(current_user, db)
    charge = db.query(Charge).filter(Charge.id == charge_id, Charge.organization_id == membership.organization_id).first()
    if not charge:
        raise HTTPException(status_code=404, detail="Charge not found")
    return enrich_charge(charge, db)
