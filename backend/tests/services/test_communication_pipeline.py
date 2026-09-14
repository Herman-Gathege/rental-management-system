"""Requirement 7 - WhatsApp-first pipeline with optional SMTP email.

Covers the four configured modes (WhatsApp-only, email-only, fallback, dual),
idempotency, delivery logging, and the guarantee that a failing email can
never break the business operation that triggered the notification.
"""
from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.models.message import Message
from app.models.organization_settings import (
    CHANNEL_DUAL,
    CHANNEL_EMAIL_ONLY,
    CHANNEL_FALLBACK,
    CHANNEL_WHATSAPP_ONLY,
    OrganizationSettings,
)
from app.services import organization_settings_service as oss
from app.services.messaging import messaging_service


@pytest.fixture
def configured_channels(monkeypatch):
    """Pretend both WhatsApp and SMTP are correctly configured.

    Mutates the settings singleton (restored automatically by monkeypatch) so
    channel resolution sees a fully provisioned deployment.
    """
    monkeypatch.setattr(settings.whatsapp, "environment", "sandbox", raising=False)
    monkeypatch.setattr(settings.whatsapp, "phone_number_id", "123", raising=False)
    monkeypatch.setattr(settings.whatsapp, "access_token", "token", raising=False)
    monkeypatch.setattr(settings.whatsapp, "app_secret", "secret", raising=False)
    monkeypatch.setattr(settings.whatsapp, "default_org_id", "org", raising=False)
    monkeypatch.setattr(settings.email, "host", "smtp.example.com", raising=False)
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com", raising=False)
    monkeypatch.setattr(settings.email, "enabled", True, raising=False)


@pytest.fixture
def sent(monkeypatch):
    """Capture WhatsApp and email sends instead of performing them."""
    captured = {"whatsapp": [], "email": []}

    class FakeProvider:
        def send_freeform_text(self, to_phone, body):
            captured["whatsapp"].append((to_phone, body))
            return {"provider_message_id": f"wa-{len(captured['whatsapp'])}"}

        def send_template(self, to_phone, template_name, template_params, language_code):
            captured["whatsapp"].append((to_phone, template_name))
            return {"provider_message_id": "wa-tpl"}

    monkeypatch.setattr(messaging_service, "_get_provider", lambda: FakeProvider())
    monkeypatch.setattr(messaging_service, "_use_meta_templates", lambda: False)
    monkeypatch.setattr(
        messaging_service,
        "send_email_message",
        lambda to, subject, html: (
            captured["email"].append((to, subject)) or (True, None)
        ),
    )
    return captured


def _settings_row(db, org, **overrides):
    row = OrganizationSettings(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        **{
            "invoice_generation_day": 1,
            "reminder_day": 10,
            "timezone": "Africa/Nairobi",
            "channel_mode": CHANNEL_WHATSAPP_ONLY,
            "whatsapp_enabled": True,
            "email_enabled": False,
            "email_payment_receipts": True,
            **overrides,
        },
    )
    db.add(row)
    db.flush()
    return row


# ─── Channel resolution ──────────────────────────────────────────────────


def test_default_mode_is_whatsapp_only(db, org, configured_channels):
    """With no settings row at all, behaviour is unchanged: WhatsApp only."""
    channels = oss.resolve_channels(None, has_phone=True, has_email=True)
    assert channels == ["whatsapp"]


@pytest.mark.parametrize(
    "mode,has_phone,has_email,expected",
    [
        (CHANNEL_WHATSAPP_ONLY, True, True, ["whatsapp"]),
        (CHANNEL_WHATSAPP_ONLY, False, True, ["email"]),
        (CHANNEL_WHATSAPP_ONLY, False, False, []),
        (CHANNEL_EMAIL_ONLY, True, True, ["email"]),
        (CHANNEL_EMAIL_ONLY, True, False, []),
        (CHANNEL_FALLBACK, True, True, ["whatsapp", "email"]),
        (CHANNEL_FALLBACK, True, False, ["whatsapp"]),
        (CHANNEL_FALLBACK, False, True, ["email"]),
        (CHANNEL_DUAL, True, True, ["whatsapp", "email"]),
        (CHANNEL_DUAL, True, False, ["whatsapp"]),
    ],
)
def test_channel_resolution_per_mode(
    db, org, configured_channels, mode, has_phone, has_email, expected
):
    # Both channels are switched on here; the mode alone decides the outcome.
    row = _settings_row(db, org, channel_mode=mode, email_enabled=True)
    assert (
        oss.resolve_channels(row, has_phone=has_phone, has_email=has_email)
        == expected
    )


def test_email_channel_is_unavailable_when_smtp_is_not_configured(
    db, org, monkeypatch
):
    monkeypatch.setattr(settings.email, "host", "", raising=False)
    monkeypatch.setattr(settings.email, "from_email", "", raising=False)
    row = _settings_row(db, org, channel_mode=CHANNEL_EMAIL_ONLY, email_enabled=True)

    assert oss.resolve_channels(row, has_phone=True, has_email=True) == []


def test_disabled_channels_are_reported_as_such(db, org, configured_channels):
    row = _settings_row(db, org, whatsapp_enabled=True, email_enabled=False)
    status = oss.channel_status(row)

    assert status["email"]["state"] == "disabled"
    assert status["whatsapp"]["state"] == "enabled"


def test_unconfigured_email_is_reported_as_not_configured(
    db, org, configured_channels, monkeypatch
):
    monkeypatch.setattr(settings.email, "host", "", raising=False)
    monkeypatch.setattr(settings.email, "from_email", "", raising=False)
    row = _settings_row(db, org, email_enabled=True)

    assert oss.channel_status(row)["email"]["state"] == "not_configured"


def test_invalid_email_configuration_is_reported(
    db, org, configured_channels, monkeypatch
):
    monkeypatch.setattr(settings.email, "host", "smtp.example.com", raising=False)
    monkeypatch.setattr(settings.email, "from_email", "not-an-email", raising=False)
    row = _settings_row(db, org, email_enabled=True)

    status = oss.channel_status(row)
    assert status["email"]["state"] == "invalid"
    assert status["email"]["errors"]


# ─── Delivery ────────────────────────────────────────────────────────────


def _send(db, org, **overrides):
    kwargs = {
        "db": db,
        "organization_id": org.id,
        "phone_number": "+254700000000",
        "template_name": "payment_receipt",
        "variables": {"tenant_name": "Jane", "amount": "1,000", "date": "1 Sep 2026"},
    }
    kwargs.update(overrides)
    return messaging_service.send_notification(**kwargs)


def test_whatsapp_is_used_by_default(db, org, configured_channels, sent):
    message = _send(db, org)

    assert message.channel == "whatsapp"
    assert message.status == "sent"
    assert len(sent["whatsapp"]) == 1
    assert sent["email"] == []


def test_email_only_mode_sends_no_whatsapp(db, org, configured_channels, sent):
    _settings_row(db, org, channel_mode=CHANNEL_EMAIL_ONLY, email_enabled=True)

    message = _send(db, org, email_address="tenant@example.com")

    assert message.channel == "email"
    assert message.phone_number is None
    assert message.email_address == "tenant@example.com"
    assert message.status == "sent"
    assert sent["whatsapp"] == []
    assert sent["email"] == [("tenant@example.com", "Payment receipt")]


def test_dual_mode_sends_on_both_channels(db, org, configured_channels, sent):
    _settings_row(db, org, channel_mode=CHANNEL_DUAL, email_enabled=True)

    _send(db, org, email_address="tenant@example.com")

    assert len(sent["whatsapp"]) == 1
    assert len(sent["email"]) == 1
    rows = (
        db.query(Message)
        .filter(Message.organization_id == org.id)
        .all()
    )
    assert {row.channel for row in rows} == {"whatsapp", "email"}


def test_fallback_mode_emails_when_whatsapp_fails(
    db, org, configured_channels, monkeypatch
):
    _settings_row(db, org, channel_mode=CHANNEL_FALLBACK, email_enabled=True)
    emailed: list[str] = []

    class FailingProvider:
        def send_freeform_text(self, to_phone, body):
            from app.services.messaging.base_provider import MessagingProviderError

            raise MessagingProviderError("Meta rejected the message")

        def send_template(self, *args, **kwargs):  # pragma: no cover
            raise AssertionError("templates are disabled in this test")

    monkeypatch.setattr(messaging_service, "_get_provider", lambda: FailingProvider())
    monkeypatch.setattr(messaging_service, "_use_meta_templates", lambda: False)
    monkeypatch.setattr(
        messaging_service,
        "send_email_message",
        lambda to, subject, html: (emailed.append(to) or (True, None)),
    )

    _send(db, org, email_address="tenant@example.com")

    assert emailed == ["tenant@example.com"]
    rows = (
        db.query(Message)
        .filter(Message.organization_id == org.id)
        .order_by(Message.channel)
        .all()
    )
    assert {row.channel: row.status for row in rows} == {
        "email": "sent",
        "whatsapp": "failed",
    }
    assert rows[0].error_message is None or rows[0].channel == "email"


def test_whatsapp_only_mode_falls_back_to_email_when_there_is_no_phone(
    db, org, configured_channels, sent
):
    """WhatsApp stays primary, but a tenant with only an email still hears
    from us rather than being silently skipped."""
    _settings_row(db, org, email_enabled=True)

    message = _send(db, org, phone_number=None, email_address="tenant@example.com")

    assert message.channel == "email"
    assert sent["email"] == [("tenant@example.com", "Payment receipt")]


def test_email_failure_is_recorded_and_does_not_raise(
    db, org, configured_channels, monkeypatch
):
    _settings_row(db, org, channel_mode=CHANNEL_DUAL, email_enabled=True)

    class FakeProvider:
        def send_freeform_text(self, to_phone, body):
            return {"provider_message_id": "wa-1"}

    monkeypatch.setattr(messaging_service, "_get_provider", lambda: FakeProvider())
    monkeypatch.setattr(messaging_service, "_use_meta_templates", lambda: False)
    monkeypatch.setattr(
        messaging_service,
        "send_email_message",
        lambda to, subject, html: (False, "SMTP connection refused"),
    )

    # No exception: a bad SMTP host must never break the payment transaction.
    _send(db, org, email_address="tenant@example.com")

    email_row = (
        db.query(Message)
        .filter(
            Message.organization_id == org.id,
            Message.channel == "email",
        )
        .one()
    )
    assert email_row.status == "failed"
    assert email_row.error_message == "SMTP connection refused"


def test_no_available_channel_is_logged_rather_than_dropped(
    db, org, configured_channels, sent
):
    _settings_row(db, org, email_enabled=False)

    message = _send(db, org, phone_number=None, email_address=None)

    assert message.status == "failed"
    assert "No delivery channel" in message.error_message
    assert sent["whatsapp"] == []


# ─── Idempotency ─────────────────────────────────────────────────────────


def test_idempotency_key_prevents_a_duplicate_send(
    db, org, configured_channels, sent
):
    first = _send(db, org, idempotency_key="payment_receipt:abc")
    second = _send(db, org, idempotency_key="payment_receipt:abc")

    assert first.id == second.id
    assert len(sent["whatsapp"]) == 1


def test_idempotency_keys_are_scoped_per_organisation(
    db, org, configured_channels, sent
):
    from app.models.organization import Organization

    other_org = Organization(
        id=str(uuid.uuid4()), name="Other", owner_id=str(uuid.uuid4())
    )
    db.add(other_org)
    db.flush()

    _send(db, org, idempotency_key="payment_receipt:abc")
    _send(db, other_org, idempotency_key="payment_receipt:abc")

    assert len(sent["whatsapp"]) == 2


def test_different_idempotency_keys_both_send(db, org, configured_channels, sent):
    _send(db, org, idempotency_key="payment_receipt:abc")
    _send(db, org, idempotency_key="payment_receipt:def")

    assert len(sent["whatsapp"]) == 2


# ─── Email rendering ─────────────────────────────────────────────────────


def test_email_body_escapes_recipient_supplied_values():
    html = messaging_service._html_from_body(
        "Receipt", "Hi <script>alert(1)</script>,\n\nThanks"
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
