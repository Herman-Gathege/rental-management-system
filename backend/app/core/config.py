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


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

    whatsapp: WhatsAppSettings = WhatsAppSettings()


settings = Settings()
