"""Requirement 3 - automated invoice generation and pending-payment reminders.

The two properties that matter most here are idempotency (a retried job must
not duplicate invoices or notifications) and correctness of the reminder
audience (tenants who have already paid must be skipped).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.automation_run import (
    JOB_INVOICE_GENERATION,
    JOB_PAYMENT_REMINDER,
    STATUS_SUCCESS,
    AutomationRun,
)
from app.models.charge import Charge
from app.models.lease import Lease
from app.models.message import Message
from app.models.payment import Payment
from app.services import automation_service
from app.services.organization_settings_service import get_settings


@pytest.fixture(autouse=True)
def stub_notifications(monkeypatch):
    """Capture tenant notifications instead of sending them.

    The messaging helpers open their own database session (the real one), which
    a test transaction cannot see. Stubbing the helper keeps these tests focused
    on what they are actually asserting - which charges were created and which
    tenants were selected - while still verifying that the automation asked for
    the right notifications.
    """
    calls: list[list[str]] = []

    def _record(charge_ids):
        calls.append(list(charge_ids or []))

    monkeypatch.setattr(
        "app.services.messaging.notify_rent_due_for_charges", _record
    )
    return calls


def _lease(org, tenant_id, *, rent=25000, day=1, status="active", unit_id=None):
    return Lease(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        unit_id=unit_id or str(uuid.uuid4()),
        tenant_id=tenant_id,
        start_date=date(2026, 1, 1),
        billing_day=day,
        rent_amount=rent,
        status=status,
    )


# ─── Date helpers ────────────────────────────────────────────────────────


def test_days_in_month_handles_leap_and_short_months():
    assert automation_service.days_in_month(date(2026, 2, 1)) == 28
    assert automation_service.days_in_month(date(2024, 2, 1)) == 29
    assert automation_service.days_in_month(date(2026, 9, 1)) == 30
    assert automation_service.days_in_month(date(2026, 1, 1)) == 31


def test_org_today_uses_the_configured_timezone():
    # 2026-09-30 22:30 UTC is already 2026-10-01 in Nairobi (UTC+3).
    moment = datetime(2026, 9, 30, 22, 30, tzinfo=timezone.utc)
    assert automation_service.org_today("Africa/Nairobi", moment) == date(2026, 10, 1)
    assert automation_service.org_today("UTC", moment) == date(2026, 9, 30)


def test_org_today_falls_back_when_the_timezone_is_unknown():
    moment = datetime(2026, 9, 30, 22, 30, tzinfo=timezone.utc)
    assert automation_service.org_today("Not/AZone", moment) == date(2026, 10, 1)


# ─── Invoice generation ──────────────────────────────────────────────────


def test_generation_creates_one_charge_per_active_lease(db, org, tenant_record):
    db.add_all(
        [
            _lease(org, tenant_record.id),
            _lease(org, tenant_record.id),
            _lease(org, tenant_record.id, status="ended"),
        ]
    )
    db.flush()

    result = automation_service.generate_monthly_invoices(
        db, org.id, billing_date=date(2026, 9, 3)
    )

    assert result["created"] == 2
    assert result["billing_month"] == date(2026, 9, 1)
    charges = db.query(Charge).filter(Charge.organization_id == org.id).all()
    assert len(charges) == 2
    assert {c.charge_type for c in charges} == {"rent"}


def test_generation_is_idempotent_when_retried(db, org, tenant_record):
    db.add(_lease(org, tenant_record.id))
    db.flush()

    first = automation_service.generate_monthly_invoices(
        db, org.id, billing_date=date(2026, 9, 1)
    )
    second = automation_service.generate_monthly_invoices(
        db, org.id, billing_date=date(2026, 9, 15)
    )

    assert first["created"] == 1
    assert second["created"] == 0
    assert second["skipped"] == 1
    assert db.query(Charge).filter(Charge.organization_id == org.id).count() == 1


def test_deposit_charge_does_not_mask_a_missing_rent_charge(db, org, tenant_record):
    """Deposit and rent share a billing month; only the rent row should count
    as "already billed"."""
    lease = _lease(org, tenant_record.id)
    db.add(lease)
    db.flush()
    db.add(
        Charge(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            lease_id=lease.id,
            amount=25000,
            amount_paid=0,
            charge_type="deposit",
            due_date=date(2026, 9, 1),
            billing_month=date(2026, 9, 1),
            status="pending",
        )
    )
    db.flush()

    result = automation_service.generate_monthly_invoices(
        db, org.id, billing_date=date(2026, 9, 5)
    )

    assert result["created"] == 1
    types = {
        c.charge_type
        for c in db.query(Charge).filter(Charge.lease_id == lease.id).all()
    }
    assert types == {"deposit", "rent"}


def test_billing_day_is_clamped_for_short_months(db, org, tenant_record):
    db.add(_lease(org, tenant_record.id, day=31))
    db.flush()

    automation_service.generate_monthly_invoices(
        db, org.id, billing_date=date(2026, 2, 1)
    )

    charge = db.query(Charge).filter(Charge.organization_id == org.id).one()
    assert charge.due_date == date(2026, 2, 28)


def test_run_generation_writes_an_audit_row_and_skips_a_second_run(
    db, org, tenant_record, stub_notifications
):
    db.add(_lease(org, tenant_record.id))
    db.flush()
    run_date = date(2026, 9, 1)

    first = automation_service.run_invoice_generation(db, org.id, run_date=run_date)
    db.flush()
    second = automation_service.run_invoice_generation(db, org.id, run_date=run_date)

    assert first is not None
    assert first.status == STATUS_SUCCESS
    assert first.created_count == 1
    assert "1 charge" in first.message
    # Requirement 3.3: the automated run notifies the tenants it just billed,
    # through the existing rent-due notification.
    assert stub_notifications == [
        [c.id for c in db.query(Charge).filter(Charge.organization_id == org.id)]
    ]
    assert second is None
    runs = (
        db.query(AutomationRun)
        .filter(
            AutomationRun.organization_id == org.id,
            AutomationRun.job == JOB_INVOICE_GENERATION,
        )
        .all()
    )
    assert len(runs) == 1


def test_disabled_invoice_automation_does_nothing(db, org, tenant_record):
    settings_row = get_settings(db, org.id)
    settings_row.invoice_automation_enabled = False
    db.flush()

    result = automation_service.run_invoice_generation(
        db, org.id, run_date=date(2026, 9, 1)
    )

    assert result is None
    assert db.query(Charge).filter(Charge.organization_id == org.id).count() == 0


# ─── Pending-payment reminders ───────────────────────────────────────────


def test_pending_payments_exclude_tenants_who_have_paid(db, org, tenant_record):
    paid_lease = _lease(org, tenant_record.id)
    owing_lease = _lease(org, tenant_record.id)
    db.add_all([paid_lease, owing_lease])
    db.flush()

    db.add_all(
        [
            Charge(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                lease_id=paid_lease.id,
                amount=25000,
                amount_paid=25000,
                charge_type="rent",
                due_date=date(2026, 9, 1),
                billing_month=date(2026, 9, 1),
                status="paid",
            ),
            Charge(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                lease_id=owing_lease.id,
                amount=25000,
                amount_paid=0,
                charge_type="rent",
                due_date=date(2026, 9, 1),
                billing_month=date(2026, 9, 1),
                status="pending",
            ),
        ]
    )
    db.flush()

    pending = automation_service.find_pending_payments(
        db, org.id, as_of=date(2026, 9, 10)
    )

    assert [row["lease_id"] for row in pending] == [owing_lease.id]
    assert pending[0]["amount"] == 25000
    assert pending[0]["days_overdue"] == 9
    assert pending[0]["period_key"] == "2026-09"


def test_pending_payments_ignore_other_billing_periods(db, org, tenant_record):
    lease = _lease(org, tenant_record.id)
    db.add(lease)
    db.flush()
    db.add(
        Charge(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            lease_id=lease.id,
            amount=25000,
            amount_paid=0,
            charge_type="rent",
            due_date=date(2026, 8, 1),
            billing_month=date(2026, 8, 1),
            status="overdue",
        )
    )
    db.flush()

    pending = automation_service.find_pending_payments(
        db, org.id, as_of=date(2026, 9, 10)
    )

    assert pending == []


def test_pending_payments_skip_deposit_only_balances(db, org, tenant_record):
    lease = _lease(org, tenant_record.id)
    db.add(lease)
    db.flush()
    db.add(
        Charge(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            lease_id=lease.id,
            amount=25000,
            amount_paid=0,
            charge_type="deposit",
            due_date=date(2026, 9, 1),
            billing_month=date(2026, 9, 1),
            status="pending",
        )
    )
    db.flush()

    assert automation_service.find_pending_payments(db, org.id, date(2026, 9, 10)) == []


def test_reminder_run_records_a_run_row(db, org, tenant_record, monkeypatch):
    lease = _lease(org, tenant_record.id)
    db.add(lease)
    db.flush()
    db.add(
        Charge(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            lease_id=lease.id,
            amount=25000,
            amount_paid=25000,
            charge_type="rent",
            due_date=date(2026, 9, 1),
            billing_month=date(2026, 9, 1),
            status="paid",
        )
    )
    db.flush()

    run = automation_service.run_payment_reminders(
        db, org.id, run_date=date(2026, 9, 10)
    )
    db.flush()

    assert run is not None
    assert run.job == JOB_PAYMENT_REMINDER
    assert run.processed == 0
    assert "0 tenant(s) with a balance" in run.message


def test_reminder_run_is_skipped_when_already_run(db, org):
    run_date = date(2026, 9, 10)
    first = automation_service.run_payment_reminders(db, org.id, run_date=run_date)
    db.flush()
    second = automation_service.run_payment_reminders(db, org.id, run_date=run_date)

    assert first is not None
    assert second is None


# ─── Daily sweep ─────────────────────────────────────────────────────────


def test_daily_sweep_respects_the_configured_day(db, org, tenant_record):
    settings_row = get_settings(db, org.id)
    settings_row.invoice_generation_day = 1
    settings_row.reminder_day = 10
    db.add(_lease(org, tenant_record.id))
    db.flush()
    db.commit()

    # The 1st: invoices run, reminders are not due.
    summary = automation_service.run_daily(db, run_date=date(2026, 9, 1))
    statuses = {row["job"]: row["status"] for row in summary}
    assert statuses[JOB_INVOICE_GENERATION] == STATUS_SUCCESS
    assert statuses[JOB_PAYMENT_REMINDER] == "not_due"


def test_daily_sweep_runs_with_custom_configured_days(db, org, tenant_record):
    settings_row = get_settings(db, org.id)
    settings_row.invoice_generation_day = 3
    settings_row.reminder_day = 15
    db.add(_lease(org, tenant_record.id))
    db.flush()
    db.commit()

    summary = automation_service.run_daily(db, run_date=date(2026, 9, 3))
    statuses = {row["job"]: row["status"] for row in summary}
    assert statuses[JOB_INVOICE_GENERATION] == STATUS_SUCCESS
    assert statuses[JOB_PAYMENT_REMINDER] == "not_due"

    db.expire_all()
    run = (
        db.query(AutomationRun)
        .filter(AutomationRun.organization_id == org.id)
        .one()
    )
    assert run.run_date == date(2026, 9, 3)


def test_daily_sweep_is_safe_to_run_twice(db, org, tenant_record):
    db.add(_lease(org, tenant_record.id))
    db.flush()
    db.commit()

    automation_service.run_daily(db, run_date=date(2026, 9, 1))
    second = automation_service.run_daily(db, run_date=date(2026, 9, 1))

    # Re-running the same day is a no-op: the invoice job reports "skipped",
    # the reminder job is simply not due.
    assert all(row["status"] in ("skipped", "not_due") for row in second)
    assert db.query(Charge).filter(Charge.organization_id == org.id).count() == 1


def test_payment_records_do_not_change_invoice_generation(db, org, tenant_record):
    """A payment for a previous period must not suppress this period's invoice."""
    lease = _lease(org, tenant_record.id)
    db.add(lease)
    db.flush()
    db.add(
        Payment(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            tenant_id=tenant_record.id,
            lease_id=lease.id,
            amount=25000,
            payment_method="mpesa",
            payment_type="rent",
            payment_date=date(2026, 8, 2),
        )
    )
    db.flush()

    result = automation_service.generate_monthly_invoices(
        db, org.id, billing_date=date(2026, 9, 1)
    )

    assert result["created"] == 1
