# backend/app/services/automation_service.py
"""
Billing automation: monthly invoice generation + pending-payment reminders.

This is the implementation behind the scheduled job (see
``app/automation/daily.py``) and the "Run now" actions on the settings page.
The monthly-charge loop used to live inline in
``POST /charges/generate-monthly``; it now lives here so the HTTP route and the
scheduler share exactly one implementation and cannot drift apart.

Idempotency, in layers
----------------------
1. An ``AutomationRun`` row per (org, job, run_date). A job that already ran
   successfully today does nothing on a retry; a job that failed earlier today
   is retried in place.
2. Invoice generation re-checks for an existing charge on the same
   (lease, billing_month, charge_type) before inserting, so even a manual
   re-trigger of the same period creates nothing new.
3. Reminders are keyed in the messages table
   (``payment_reminder:{lease_id}:{period}``), so a tenant receives at most one
   reminder per billing period.

Every run - including runs that found nothing to do - writes an AutomationRun
row with counts and a human-readable summary, which is what makes the
automations troubleshootable after the fact.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.automation_run import (
    JOB_INVOICE_GENERATION,
    JOB_PAYMENT_REMINDER,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STATUS_SUCCESS,
    AutomationRun,
)
from app.models.charge import Charge
from app.models.lease import Lease
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.audit_service import log_action
from app.services.organization_settings_service import (
    get_settings_or_none,
    setting_value,
)

logger = logging.getLogger(__name__)


def org_today(tz_name: Optional[str] = None, now: Optional[datetime] = None) -> date:
    """Today's date in the organisation's timezone.

    Falls back to a fixed UTC+3 offset when the IANA database isn't available
    (the platform's primary timezone), so a missing tzdata package degrades to
    the previous behaviour instead of crashing the job.
    """
    now = now or datetime.now(timezone.utc)
    if tz_name:
        try:
            from zoneinfo import ZoneInfo

            return now.astimezone(ZoneInfo(tz_name)).date()
        except Exception:  # noqa: BLE001 - unknown zone / missing tzdata
            logger.warning("Unknown timezone %r - falling back to UTC+3", tz_name)
    return (now + timedelta(hours=3)).date()


def billing_month_for(d: date) -> date:
    """First day of the month containing ``d`` - the billing period key."""
    return d.replace(day=1)


def days_in_month(d: date) -> int:
    """Number of days in the month containing ``d``."""
    next_month = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
    return (next_month - timedelta(days=1)).day


def _claim_run(
    db: Session,
    organization_id: str,
    job: str,
    run_date: date,
) -> Optional[AutomationRun]:
    """Reserve today's run for this org+job.

    Returns the run row to fill in, or None when the job already completed
    successfully today (nothing to do).
    """
    existing = (
        db.query(AutomationRun)
        .filter(
            AutomationRun.organization_id == organization_id,
            AutomationRun.job == job,
            AutomationRun.run_date == run_date,
        )
        .first()
    )

    if existing:
        if existing.status == STATUS_SUCCESS:
            return None
        # A previous attempt failed (or was interrupted) today - retry in place.
        existing.status = STATUS_SUCCESS
        existing.started_at = datetime.utcnow()
        existing.finished_at = None
        existing.message = None
        db.flush()
        return existing

    run = AutomationRun(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        job=job,
        run_date=run_date,
        status=STATUS_SUCCESS,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()
    return run


def _finish(
    db: Session,
    run: AutomationRun,
    *,
    status: str,
    message: str,
    processed: int = 0,
    created: int = 0,
    skipped: int = 0,
    notified: int = 0,
) -> AutomationRun:
    """Record the outcome of a run."""
    run.status = status
    run.message = message
    run.processed = processed
    run.created_count = created
    run.skipped_count = skipped
    run.notified_count = notified
    run.finished_at = datetime.utcnow()
    return run


def generate_monthly_invoices(
    db: Session,
    organization_id: str,
    billing_date: Optional[date] = None,
    triggered_by_user_id: Optional[str] = None,
) -> dict:
    """Create this period's rent charge for every active lease in the org.

    Idempotent on (lease, billing_month, charge_type="rent"): re-running for a
    month that already has a charge skips that lease. Deposit charges share the
    billing_month but carry charge_type="deposit", so they never mask a missing
    rent charge.

    Returns a summary dict; the caller commits.
    """
    from app.services.billing_service import recompute_lease_settlement

    billing_date = billing_date or date.today()
    billing_month = billing_month_for(billing_date)

    active_leases = (
        db.query(Lease)
        .filter(
            Lease.organization_id == organization_id,
            Lease.status == "active",
        )
        .all()
    )

    new_charge_ids: list[str] = []
    affected_lease_ids: set[str] = set()
    skipped = 0

    for lease in active_leases:
        existing = (
            db.query(Charge)
            .filter(
                Charge.lease_id == lease.id,
                Charge.billing_month == billing_month,
                Charge.charge_type == "rent",
            )
            .first()
        )
        if existing:
            skipped += 1
            continue

        # Billing day is clamped to the length of the target month so a lease
        # billing on the 31st still gets a valid due date in February.
        due_day = min(
            max(int(lease.billing_day or 1), 1),
            days_in_month(billing_month),
        )
        due = billing_month.replace(day=due_day)

        charge = Charge(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            lease_id=lease.id,
            amount=lease.rent_amount,
            charge_type="rent",
            due_date=due,
            billing_month=billing_month,
            status="pending",
        )
        db.add(charge)
        new_charge_ids.append(charge.id)
        affected_lease_ids.add(lease.id)

    if affected_lease_ids:
        db.flush()
        for lease_id in affected_lease_ids:
            recompute_lease_settlement(db, lease_id)

    if new_charge_ids:
        log_action(
            db,
            organization_id,
            triggered_by_user_id,
            "billing",
            "charge",
            "batch",
            f"Generated {len(new_charge_ids)} monthly charges for {billing_month}",
        )

    return {
        "created": len(new_charge_ids),
        "skipped": skipped,
        "billing_month": billing_month,
        "charge_ids": new_charge_ids,
        "lease_ids": sorted(affected_lease_ids),
    }


def run_invoice_generation(
    db: Session,
    organization_id: str,
    run_date: Optional[date] = None,
    triggered_by_user_id: Optional[str] = None,
) -> Optional[AutomationRun]:
    """Scheduled/one-off invoice run for one organisation.

    Returns None when the job already succeeded today, or when the automation
    is disabled for the org. Caller commits.
    """
    settings_row = get_settings_or_none(db, organization_id)
    run_date = run_date or org_today(setting_value(settings_row, "timezone"))

    if not bool(setting_value(settings_row, "invoice_automation_enabled")):
        return None

    run = _claim_run(db, organization_id, JOB_INVOICE_GENERATION, run_date)
    if run is None:
        logger.info(
            "invoice_generation already completed for org %s on %s",
            organization_id, run_date,
        )
        return None

    try:
        result = generate_monthly_invoices(
            db,
            organization_id,
            billing_date=run_date,
            triggered_by_user_id=triggered_by_user_id,
        )
        # Notify the tenants who were just billed, reusing the existing
        # rent-due notification and its template. Commit first: the notifier
        # opens its own session, so the new charge rows have to be visible to
        # it. Each send is keyed on the charge id, so running this job twice
        # can never double-message a tenant.
        db.commit()
        notified = 0
        if result["charge_ids"]:
            from app.services.messaging import notify_rent_due_for_charges

            notify_rent_due_for_charges(result["charge_ids"])
            notified = len(result["charge_ids"])

        # Re-claim the run row on the (re-opened) transaction so the counters
        # and summary below are written against a live session.
        run = (
            db.query(AutomationRun)
            .filter(AutomationRun.id == run.id)
            .one()
        )
        _finish(
            db,
            run,
            status=STATUS_SUCCESS,
            message=(
                f"Generated {result['created']} charge(s) for "
                f"{result['billing_month']}; {result['skipped']} lease(s) "
                f"already billed; {notified} notification(s) queued"
            ),
            processed=result["created"] + result["skipped"],
            created=result["created"],
            skipped=result["skipped"],
            notified=notified,
        )
        logger.info(
            "invoice_generation org=%s date=%s created=%s skipped=%s",
            organization_id, run_date, result["created"], result["skipped"],
        )
        return run
    except Exception as exc:  # noqa: BLE001 - one org must not stop the sweep
        logger.exception(
            "invoice_generation failed for org %s: %s", organization_id, exc,
        )
        db.rollback()
        # Re-claim on a clean transaction so the failure is still recorded.
        run = _claim_run(db, organization_id, JOB_INVOICE_GENERATION, run_date)
        if run is not None:
            _finish(db, run, status=STATUS_FAILED, message=str(exc))
        return run


def find_pending_payments(
    db: Session,
    organization_id: str,
    as_of: date,
) -> list[dict]:
    """Active leases in this org that still owe rent for the current period.

    A lease qualifies when at least one rent charge for the period is not fully
    covered as of ``as_of``. Tenants who have already paid are absent by
    construction - their charges are fully settled, so nothing is selected.
    """
    billing_month = billing_month_for(as_of)

    outstanding = (
        db.query(
            Charge.lease_id.label("lease_id"),
            func.sum(Charge.amount - Charge.amount_paid).label("balance"),
            func.min(Charge.due_date).label("first_due"),
        )
        .join(Lease, Lease.id == Charge.lease_id)
        .filter(
            Charge.organization_id == organization_id,
            Charge.charge_type == "rent",
            Charge.billing_month == billing_month,
            Charge.amount_paid < Charge.amount,
            Lease.status == "active",
        )
        .group_by(Charge.lease_id)
        .all()
    )

    results: list[dict] = []
    for row in outstanding:
        lease = db.query(Lease).filter(Lease.id == row.lease_id).first()
        if not lease:
            continue
        tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
        if not tenant:
            continue
        first_due = row.first_due or billing_month
        results.append(
            {
                "lease_id": lease.id,
                "tenant_id": tenant.id,
                "tenant_name": tenant.full_name,
                "amount": float(row.balance or 0),
                "days_overdue": max((as_of - first_due).days, 0),
                "period_key": billing_month.strftime("%Y-%m"),
            }
        )
    return results


def run_payment_reminders(
    db: Session,
    organization_id: str,
    run_date: Optional[date] = None,
    triggered_by_user_id: Optional[str] = None,
) -> Optional[AutomationRun]:
    """Send pending-payment reminders for one org.

    Returns None when the job already succeeded today, or when the automation
    is disabled for the org. Caller commits.
    """
    from app.services.messaging import notify_pending_payment

    settings_row = get_settings_or_none(db, organization_id)
    run_date = run_date or org_today(setting_value(settings_row, "timezone"))

    if not bool(setting_value(settings_row, "reminder_automation_enabled")):
        return None

    run = _claim_run(db, organization_id, JOB_PAYMENT_REMINDER, run_date)
    if run is None:
        logger.info(
            "payment_reminder already completed for org %s on %s",
            organization_id, run_date,
        )
        return None

    try:
        pending = find_pending_payments(db, organization_id, run_date)
        # Commit the run row before the sends: each notification opens its own
        # session, and we don't want to hold this transaction open across
        # network calls to the messaging providers.
        db.commit()

        notified = 0
        for item in pending:
            if notify_pending_payment(
                tenant_id=item["tenant_id"],
                lease_id=item["lease_id"],
                organization_id=organization_id,
                amount=item["amount"],
                days_overdue=item["days_overdue"],
                period_key=item["period_key"],
            ):
                notified += 1

        _finish(
            db,
            run,
            status=STATUS_SUCCESS,
            message=(
                f"{len(pending)} tenant(s) with a balance for "
                f"{billing_month_for(run_date)}; {notified} reminder(s) delivered"
            ),
            processed=len(pending),
            notified=notified,
        )
        logger.info(
            "payment_reminder org=%s date=%s pending=%s notified=%s",
            organization_id, run_date, len(pending), notified,
        )
        return run
    except Exception as exc:  # noqa: BLE001 - one org must not stop the sweep
        logger.exception(
            "payment_reminder failed for org %s: %s", organization_id, exc,
        )
        db.rollback()
        run = _claim_run(db, organization_id, JOB_PAYMENT_REMINDER, run_date)
        if run is not None:
            _finish(db, run, status=STATUS_FAILED, message=str(exc))
        return run


def run_daily(db: Session, run_date: Optional[date] = None) -> list[dict]:
    """Sweep every organisation and run whatever is due today.

    Both jobs are evaluated on every invocation and each decides for itself
    whether today is its configured day, so a missed cron tick is recoverable
    by simply running the job again the same day.
    """
    organizations = db.query(Organization).all()
    summary: list[dict] = []

    for org in organizations:
        settings_row = get_settings_or_none(db, org.id)
        today = run_date or org_today(setting_value(settings_row, "timezone"))

        jobs = (
            (
                JOB_INVOICE_GENERATION,
                "invoice_generation_day",
                "invoice_automation_enabled",
                run_invoice_generation,
            ),
            (
                JOB_PAYMENT_REMINDER,
                "reminder_day",
                "reminder_automation_enabled",
                run_payment_reminders,
            ),
        )

        for job, day_field, enabled_field, runner in jobs:
            if not bool(setting_value(settings_row, enabled_field)):
                summary.append(
                    {"organization_id": org.id, "job": job, "status": "disabled"}
                )
                continue
            if today.day != int(setting_value(settings_row, day_field)):
                summary.append(
                    {"organization_id": org.id, "job": job, "status": "not_due"}
                )
                continue

            run = runner(db, org.id, run_date=today)
            db.commit()
            summary.append(
                {
                    "organization_id": org.id,
                    "job": job,
                    "status": run.status if run else STATUS_SKIPPED,
                    "message": run.message if run else "already completed today",
                }
            )

    return summary
