# backend/app/services/email_service.py
"""
Email delivery.

Two transports, chosen automatically:

  1. SMTP (preferred) - configured entirely from the environment via
     ``settings.email``. No credentials are ever read from the database or
     accepted from the API.
  2. SendGrid (legacy) - the original integration, kept working so existing
     deployments that only have ``SENDGRID_API_KEY`` are unaffected.

``send_email`` keeps its original signature and boolean return value, so the
two existing call sites (password reset, account-locked fallback) behave
exactly as before. New code should prefer ``send_email_message``, which
returns the error text so the caller can record it against the outbound
message row instead of only printing it.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_message(to_email: str, subject: str, html: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(
        (settings.email.from_name or "AlphaOne", settings.email.from_email)
    )
    msg["To"] = to_email
    msg.set_content("This message requires an HTML-capable email client.")
    msg.add_alternative(html, subtype="html")
    return msg


def send_smtp_email(to_email: str, subject: str, html: str) -> None:
    """Send via SMTP. Raises on any failure so the caller can log it."""
    cfg = settings.email
    if not cfg.is_configured:
        raise RuntimeError("SMTP is not configured (SMTP_HOST / SMTP_FROM_EMAIL)")
    if not cfg.enabled:
        raise RuntimeError("Email channel is disabled (EMAIL_ENABLED=false)")

    msg = _build_message(to_email, subject, html)

    if cfg.use_ssl:
        server = smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=cfg.timeout)
    else:
        server = smtplib.SMTP(cfg.host, cfg.port, timeout=cfg.timeout)

    try:
        if cfg.use_tls and not cfg.use_ssl:
            server.ehlo()
            server.starttls()
            server.ehlo()
        if cfg.username and cfg.password:
            server.login(cfg.username, cfg.password)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001 - closing must never mask the real error
            pass


def _send_sendgrid(to_email: str, subject: str, html: str) -> None:
    """Legacy SendGrid path. Raises on failure."""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Email is not configured (set SMTP_HOST or SENDGRID_API_KEY)"
        )

    message = Mail(
        from_email=os.getenv("EMAIL_FROM"),
        to_emails=to_email,
        subject=subject,
        html_content=html,
    )
    SendGridAPIClient(api_key).send(message)


def send_email_message(
    to_email: str,
    subject: str,
    html: str,
) -> tuple[bool, Optional[str]]:
    """Deliver one email. Returns ``(ok, error_text)`` and never raises.

    Preferred over ``send_email`` for anything that records delivery status,
    because the error text is what lands in ``messages.error_message``.
    """
    if not to_email:
        return False, "No recipient email address"
    try:
        if settings.email.is_configured:
            send_smtp_email(to_email, subject, html)
        else:
            _send_sendgrid(to_email, subject, html)
        return True, None
    except Exception as exc:  # noqa: BLE001 - delivery failures are data, not crashes
        logger.warning("Email send failed for %s: %s", to_email, exc)
        return False, str(exc)


def send_email(to_email: str, subject: str, content: str) -> bool:
    """Backwards-compatible wrapper. Returns True/False, never raises."""
    ok, error = send_email_message(to_email, subject, content)
    if not ok:
        # Preserve the original log line for existing operational tooling.
        print("Email error:", error)
    return ok
