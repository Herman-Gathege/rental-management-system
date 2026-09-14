# backend/app/core/config.py
"""
Application settings.

All configuration flows through `settings` — a singleton `Settings` instance
created at module import time. The rest of the codebase reads from
`settings.whatsapp.*` rather than calling `os.getenv("WHATSAPP_*")` directly.

.env  →  Settings  →  WhatsApp services
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class WhatsAppSettings:
    """
    Centralized WhatsApp configuration (Meta Cloud API).

    Environment variables
    ---------------------
    WHATSAPP_ENV
        Integration environment.  Must be ``"sandbox"`` or ``"production"``.
        Defaults to ``"sandbox"`` for local development.

        ``sandbox``  — Meta's test/sandbox phone number.  Credentials are
                       non-production and a dedicated test organization is used.
        ``production`` — Live Meta credentials pointing at a real business
                       phone number that is registered in the
                       ``whatsapp_integrations`` table.

    Sandbox credentials
        WHATSAPP_PHONE_NUMBER_ID
        WHATSAPP_BUSINESS_ACCOUNT_ID
        WHATSAPP_ACCESS_TOKEN
        WHATSAPP_APP_SECRET
        WHATSAPP_DEFAULT_ORG_ID   — **SANDBOX FALLBACK ONLY** (see below)

    Shared
        WHATSAPP_WEBHOOK_VERIFY_TOKEN
        WHATSAPP_USE_TEMPLATES    — ``true``/``false`` (default ``false``)
        WHATSAPP_DEFAULT_COUNTRY_CODE  — dial code for phone normalization

    Sandbox-only fallback
    ---------------------
    ``WHATSAPP_DEFAULT_ORG_ID`` exists so that sandbox development can run
    without pre-populating the ``whatsapp_integrations`` table.  It is
    explicitly documented as a **sandbox fallback only** and must NOT be
    treated as tenant ownership or the production organization-routing
    mechanism.  In production the organization is resolved via
    ``phone_number_id → WhatsAppIntegration → organization_id``.
    """

    SANDBOX = "sandbox"
    PRODUCTION = "production"
    _VALID_ENVS = frozenset({SANDBOX, PRODUCTION})

    def __init__(self) -> None:
        self.environment: str = os.getenv("WHATSAPP_ENV", self.SANDBOX).strip().lower()
        self.phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "") or ""
        self.business_account_id: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "") or ""
        self.access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "") or ""
        self.app_secret: str = os.getenv("WHATSAPP_APP_SECRET", "") or ""
        self.webhook_verify_token: str = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "") or ""
        self.use_templates: bool = os.getenv(
            "WHATSAPP_USE_TEMPLATES", "false"
        ).lower() == "true"
        self.default_country_code: str = os.getenv(
            "WHATSAPP_DEFAULT_COUNTRY_CODE", "254"
        )
        # SANDBOX FALLBACK ONLY — never use for tenant ownership or production routing.
        self.default_org_id: Optional[str] = os.getenv("WHATSAPP_DEFAULT_ORG_ID") or ""

    # ── Convenience predicates ──────────────────────────────────────────────

    @property
    def is_sandbox(self) -> bool:
        return self.environment == self.SANDBOX

    @property
    def is_production(self) -> bool:
        return self.environment == self.PRODUCTION

    # ── Validation ──────────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """
        Validate the WhatsApp configuration for the current environment.

        Returns a list of human-readable error strings.  An empty list
        means the configuration is valid.
        """
        errors: list[str] = []

        if self.environment not in self._VALID_ENVS:
            errors.append(
                f"WHATSAPP_ENV must be 'sandbox' or 'production' "
                f"(got '{self.environment}')"
            )
            return errors  # nothing else to check with a bad env

        if not self.phone_number_id:
            errors.append(
                "WHATSAPP_PHONE_NUMBER_ID is required "
                f"for environment '{self.environment}'"
            )
        if not self.access_token:
            errors.append(
                "WHATSAPP_ACCESS_TOKEN is required "
                f"for environment '{self.environment}'"
            )
        if not self.app_secret:
            errors.append(
                "WHATSAPP_APP_SECRET is required "
                f"for environment '{self.environment}'"
            )

        if self.is_sandbox and not self.default_org_id:
            errors.append(
                "WHATSAPP_DEFAULT_ORG_ID is required for sandbox environment "
                "(SANDBOX FALLBACK ONLY — not used for production routing)"
            )

        if self.is_production:
            if not self.business_account_id:
                errors.append(
                    "WHATSAPP_BUSINESS_ACCOUNT_ID is required for production"
                )

        return errors

    def describe(self) -> dict:
        """Return a non-sensitive summary for startup logging."""
        return {
            "environment": self.environment,
            "phone_number_id": (
                self.phone_number_id if self.phone_number_id else "<not set>"
            ),
            "has_access_token": bool(self.access_token),
            "has_app_secret": bool(self.app_secret),
            "has_business_account_id": bool(self.business_account_id),
            "has_default_org_id": bool(self.default_org_id),
            "use_templates": self.use_templates,
        }


class EmailSettings:
    """
    SMTP configuration for the optional email channel.

    Credentials come from the environment only — never from the database, the
    API or the frontend. ``describe()`` is deliberately secret-free so it is
    safe to return to an authenticated admin.

    Behaviour mirrors WhatsAppSettings: the channel is *optional*. With no
    ``SMTP_HOST`` set, ``is_configured`` is False and the communication
    pipeline simply reports the channel as "not configured" instead of failing.

    Environment variables
    ---------------------
    SMTP_HOST            SMTP server hostname (enables the channel when set)
    SMTP_PORT            defaults to 587
    SMTP_USERNAME        SMTP auth user
    SMTP_PASSWORD        SMTP auth password / API key
    SMTP_FROM_EMAIL      From: address (defaults to SMTP_USERNAME)
    SMTP_FROM_NAME       From: display name, defaults to "AlphaOne"
    SMTP_USE_TLS         STARTTLS on the submission port, default "true"
    SMTP_USE_SSL         implicit TLS (port 465), default "false"
    SMTP_TIMEOUT_SECONDS socket timeout, default 10
    EMAIL_ENABLED        global kill switch, default "true" when SMTP is set
    EMAIL_FROM           legacy SendGrid from-address (kept for compatibility)
    SENDGRID_API_KEY     legacy SendGrid key — used only when SMTP is absent
    """

    def __init__(self) -> None:
        self.host: str = (os.getenv("SMTP_HOST") or "").strip()
        self.port: int = int(os.getenv("SMTP_PORT") or 587)
        self.username: str = (os.getenv("SMTP_USERNAME") or "").strip()
        self.password: str = os.getenv("SMTP_PASSWORD") or ""
        self.from_email: str = (
            os.getenv("SMTP_FROM_EMAIL") or os.getenv("EMAIL_FROM") or ""
        ).strip()
        self.from_name: str = (os.getenv("SMTP_FROM_NAME") or "AlphaOne").strip()
        self.use_tls: bool = (
            os.getenv("SMTP_USE_TLS", "true").strip().lower() == "true"
        )
        self.use_ssl: bool = (
            os.getenv("SMTP_USE_SSL", "false").strip().lower() == "true"
        )
        self.timeout: int = int(os.getenv("SMTP_TIMEOUT_SECONDS") or 10)
        # Global kill switch. Defaults to enabled so that configuring SMTP is
        # enough — the per-org switch in organization_settings is what decides
        # whether a given organisation actually sends email.
        self.enabled: bool = (
            os.getenv("EMAIL_ENABLED", "true").strip().lower() == "true"
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.from_email)

    @property
    def is_usable(self) -> bool:
        return self.enabled and self.is_configured

    def validate(self) -> list[str]:
        """Human-readable configuration errors. Empty list means valid."""
        errors: list[str] = []
        if not self.host:
            errors.append("SMTP_HOST is not set")
        if not self.from_email:
            errors.append("SMTP_FROM_EMAIL (or EMAIL_FROM) is not set")
        elif "@" not in self.from_email:
            errors.append("SMTP_FROM_EMAIL is not a valid email address")
        if not (1 <= self.port <= 65535):
            errors.append(f"SMTP_PORT is out of range: {self.port}")
        if self.use_ssl and self.use_tls:
            errors.append("SMTP_USE_SSL and SMTP_USE_TLS cannot both be true")
        if self.username and not self.password:
            errors.append("SMTP_USERNAME is set but SMTP_PASSWORD is empty")
        return errors

    def describe(self) -> dict:
        """Secret-free summary, safe for API responses and startup logs."""
        return {
            "enabled": self.enabled,
            "configured": self.is_configured,
            "host": self.host or None,
            "port": self.port,
            "from_email": self.from_email or None,
            "from_name": self.from_name,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "has_credentials": bool(self.username and self.password),
        }


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

    whatsapp: WhatsAppSettings = WhatsAppSettings()
    email: EmailSettings = EmailSettings()


settings = Settings()
