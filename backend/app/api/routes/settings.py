# backend/app/api/routes/settings.py
"""
Organisation settings: billing automation + communication channels.

Landlord-only (the organisation owner is the only role authorised to change
how money is invoiced and how tenants are contacted).

    GET  /settings/automation          -> invoice + reminder configuration
    PUT  /settings/automation          -> update configuration
    POST /settings/automation/run      -> run a job now (catch-up / testing)
    GET  /settings/automation/history  -> recent runs with counts + messages
    GET  /settings/communication       -> channel mode + channel health
    PUT  /settings/communication       -> update channel mode

No endpoint here returns or accepts a credential: secrets live only in the
environment (see app/core/config.py).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import require_landlord
from app.models.automation_run import (
    JOB_INVOICE_GENERATION,
    JOB_PAYMENT_REMINDER,
    AutomationRun,
)
from app.models.organization_settings import (
    CHANNEL_DUAL,
    CHANNEL_EMAIL_ONLY,
    CHANNEL_FALLBACK,
    CHANNEL_WHATSAPP_ONLY,
    VALID_CHANNEL_MODES,
)
from app.services import automation_service
from app.services.audit_service import log_action
from app.services.organization_settings_service import (
    channel_status,
    get_settings,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


class AutomationSettingsUpdate(BaseModel):
    invoice_generation_day: Optional[int] = Field(default=None, ge=1, le=28)
    reminder_day: Optional[int] = Field(default=None, ge=1, le=28)
    invoice_automation_enabled: Optional[bool] = None
    reminder_automation_enabled: Optional[bool] = None
    timezone: Optional[str] = None


class CommunicationSettingsUpdate(BaseModel):
    channel_mode: Optional[str] = None
    whatsapp_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    email_payment_receipts: Optional[bool] = None


def _serialize_settings(row) -> dict:
    return {
        "invoice_generation_day": row.invoice_generation_day,
        "reminder_day": row.reminder_day,
        "invoice_automation_enabled": row.invoice_automation_enabled,
        "reminder_automation_enabled": row.reminder_automation_enabled,
        "timezone": row.timezone,
        "channel_mode": row.channel_mode,
        "whatsapp_enabled": row.whatsapp_enabled,
        "email_enabled": row.email_enabled,
        "email_payment_receipts": row.email_payment_receipts,
        "updated_at": row.updated_at,
    }


def _serialize_run(run: AutomationRun) -> dict:
    return {
        "id": run.id,
        "job": run.job,
        "run_date": run.run_date,
        "status": run.status,
        "processed": run.processed,
        "created_count": run.created_count,
        "skipped_count": run.skipped_count,
        "notified_count": run.notified_count,
        "message": run.message,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


@router.get("/automation")
def get_automation_settings(deps=Depends(require_landlord)):
    """Current automation configuration for this organisation."""
    user, membership, db = deps
    row = get_settings(db, membership.organization_id)
    db.commit()
    return {
        "settings": _serialize_settings(row),
        "defaults": {
            "invoice_generation_day": 1,
            "reminder_day": 10,
        },
        "server_date": automation_service.org_today(row.timezone),
    }


@router.put("/automation")
def update_automation_settings(
    payload: AutomationSettingsUpdate,
    deps=Depends(require_landlord),
):
    """Update automation configuration.

    Days 29-31 are rejected: those days don't exist in every month, so a job
    configured for them would silently skip February, April, June, September
    and November.
    """
    user, membership, db = deps
    row = get_settings(db, membership.organization_id)
    old_values = _serialize_settings(row)

    if payload.invoice_generation_day is not None:
        row.invoice_generation_day = payload.invoice_generation_day
    if payload.reminder_day is not None:
        row.reminder_day = payload.reminder_day
    if payload.invoice_automation_enabled is not None:
        row.invoice_automation_enabled = payload.invoice_automation_enabled
    if payload.reminder_automation_enabled is not None:
        row.reminder_automation_enabled = payload.reminder_automation_enabled
    if payload.timezone is not None:
        tz = payload.timezone.strip()
        try:
            from zoneinfo import ZoneInfo

            ZoneInfo(tz)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Unknown timezone: {tz}")
        row.timezone = tz

    log_action(
        db,
        membership.organization_id,
        user.id,
        "update",
        "organization_settings",
        row.id,
        "Updated billing automation settings",
        old_values=old_values,
        new_values=_serialize_settings(row),
    )
    db.commit()
    db.refresh(row)
    return {"settings": _serialize_settings(row)}


@router.post("/automation/run")
def run_automation_now(
    job: str = Query(..., description="invoice_generation | payment_reminder"),
    run_date: Optional[date] = Query(None),
    deps=Depends(require_landlord),
):
    """Run one automation immediately for this organisation.

    Shares the scheduled job's idempotency, so pressing this twice on the same
    day is a no-op the second time - the button cannot duplicate invoices or
    reminders.
    """
    user, membership, db = deps
    if job not in (JOB_INVOICE_GENERATION, JOB_PAYMENT_REMINDER):
        raise HTTPException(
            status_code=400,
            detail="job must be invoice_generation or payment_reminder",
        )

    runner = (
        automation_service.run_invoice_generation
        if job == JOB_INVOICE_GENERATION
        else automation_service.run_payment_reminders
    )
    run = runner(db, membership.organization_id, run_date=run_date)
    db.commit()

    if run is None:
        return {
            "already_completed": True,
            "job": job,
            "message": "This job has already completed for the selected date.",
        }
    return {"already_completed": False, "run": _serialize_run(run)}


@router.get("/automation/history")
def automation_history(
    limit: int = Query(20, ge=1, le=200),
    deps=Depends(require_landlord),
):
    """Recent automation runs - what ran, what it did, and what went wrong."""
    user, membership, db = deps
    rows = (
        db.query(AutomationRun)
        .filter(AutomationRun.organization_id == membership.organization_id)
        .order_by(AutomationRun.run_date.desc(), AutomationRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_run(r) for r in rows]


@router.get("/communication")
def get_communication_settings(deps=Depends(require_landlord)):
    """Channel configuration plus the live health of each channel."""
    user, membership, db = deps
    row = get_settings(db, membership.organization_id)
    db.commit()
    return {
        "settings": {
            "channel_mode": row.channel_mode,
            "whatsapp_enabled": row.whatsapp_enabled,
            "email_enabled": row.email_enabled,
            "email_payment_receipts": row.email_payment_receipts,
        },
        "channels": channel_status(row),
        "modes": [
            {
                "value": CHANNEL_WHATSAPP_ONLY,
                "label": "WhatsApp only",
                "description": "WhatsApp is the only channel; email is never used.",
            },
            {
                "value": CHANNEL_FALLBACK,
                "label": "WhatsApp first, email fallback",
                "description": "Try WhatsApp, then send by email if it fails.",
            },
            {
                "value": CHANNEL_DUAL,
                "label": "Both channels",
                "description": "Send every notification on WhatsApp and by email.",
            },
            {
                "value": CHANNEL_EMAIL_ONLY,
                "label": "Email only",
                "description": "Send everything by email; WhatsApp is not used.",
            },
        ],
    }


@router.put("/communication")
def update_communication_settings(
    payload: CommunicationSettingsUpdate,
    deps=Depends(require_landlord),
):
    """Update channel configuration. Never touches credentials."""
    user, membership, db = deps
    row = get_settings(db, membership.organization_id)
    old_values = {
        "channel_mode": row.channel_mode,
        "whatsapp_enabled": row.whatsapp_enabled,
        "email_enabled": row.email_enabled,
        "email_payment_receipts": row.email_payment_receipts,
    }

    if payload.channel_mode is not None:
        if payload.channel_mode not in VALID_CHANNEL_MODES:
            raise HTTPException(
                status_code=400,
                detail=(
                    "channel_mode must be one of: "
                    + ", ".join(VALID_CHANNEL_MODES)
                ),
            )
        row.channel_mode = payload.channel_mode

    if payload.whatsapp_enabled is not None:
        row.whatsapp_enabled = payload.whatsapp_enabled
    if payload.email_enabled is not None:
        row.email_enabled = payload.email_enabled
    if payload.email_payment_receipts is not None:
        row.email_payment_receipts = payload.email_payment_receipts

    # Refuse a configuration that cannot deliver anything - better to fail the
    # save than to silently drop every tenant notification.
    if not row.whatsapp_enabled and not row.email_enabled:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one channel must stay enabled, otherwise tenants "
                "would receive no notifications at all."
            ),
        )

    new_values = {
        "channel_mode": row.channel_mode,
        "whatsapp_enabled": row.whatsapp_enabled,
        "email_enabled": row.email_enabled,
        "email_payment_receipts": row.email_payment_receipts,
    }

    log_action(
        db,
        membership.organization_id,
        user.id,
        "update",
        "organization_settings",
        row.id,
        f"Updated communication settings ({row.channel_mode})",
        old_values=old_values,
        new_values=new_values,
    )
    db.commit()
    db.refresh(row)
    return {"settings": new_values, "channels": channel_status(row)}
