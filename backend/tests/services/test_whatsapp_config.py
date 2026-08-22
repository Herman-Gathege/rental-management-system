"""Tests for WhatsApp configuration (WhatsAppSettings).

Covers:
  - sandbox configuration loads correctly
  - production configuration loads correctly
  - invalid WhatsApp environment fails clearly
  - sandbox default org fallback is documented
  - validation flags missing required fields per environment
"""
import os
import pytest

from app.core.config import WhatsAppSettings


# ─── Sandbox configuration ─────────────────────────────────────────────────────

class TestSandboxConfig:
    def test_sandbox_environment_loads(self):
        os.environ["WHATSAPP_ENV"] = "sandbox"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAABsb_test_token"
        os.environ["WHATSAPP_APP_SECRET"] = "abc123secret"
        os.environ["WHATSAPP_DEFAULT_ORG_ID"] = "org-uuid-123"

        config = WhatsAppSettings()
        assert config.is_sandbox
        assert not config.is_production
        assert config.environment == "sandbox"
        assert config.phone_number_id == "123456789"
        assert config.access_token == "EAABsb_test_token"
        assert config.app_secret == "abc123secret"
        assert config.default_org_id == "org-uuid-123"

    def test_sandbox_validates_passes(self):
        os.environ["WHATSAPP_ENV"] = "sandbox"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAABsb_test_token"
        os.environ["WHATSAPP_APP_SECRET"] = "abc123secret"
        os.environ["WHATSAPP_DEFAULT_ORG_ID"] = "org-uuid-123"

        config = WhatsAppSettings()
        errors = config.validate()
        assert errors == [], f"Expected no validation errors, got: {errors}"

    def test_sandbox_missing_default_org_id_fails_validation(self):
        os.environ["WHATSAPP_ENV"] = "sandbox"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAABsb_test_token"
        os.environ["WHATSAPP_APP_SECRET"] = "abc123secret"
        os.environ.pop("WHATSAPP_DEFAULT_ORG_ID", None)

        config = WhatsAppSettings()
        errors = config.validate()
        assert any("WHATSAPP_DEFAULT_ORG_ID" in e for e in errors)

    def test_sandbox_default_org_id_is_fallback_only(self):
        """The default_org_id is explicitly documented as sandbox fallback only."""
        os.environ["WHATSAPP_ENV"] = "sandbox"
        os.environ["WHATSAPP_DEFAULT_ORG_ID"] = "sandbox-test-org-uuid"
        config = WhatsAppSettings()
        assert config.is_sandbox
        assert config.default_org_id == "sandbox-test-org-uuid"


# ─── Production configuration ──────────────────────────────────────────────────

class TestProductionConfig:
    def test_production_environment_loads(self):
        os.environ["WHATSAPP_ENV"] = "production"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "987654321"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAABprod_test_token"
        os.environ["WHATSAPP_APP_SECRET"] = "def456secret"
        os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = "1234567890"
        os.environ.pop("WHATSAPP_DEFAULT_ORG_ID", None)

        config = WhatsAppSettings()
        assert config.is_production
        assert not config.is_sandbox
        assert config.environment == "production"
        assert config.business_account_id == "1234567890"

    def test_production_validates_passes(self):
        os.environ["WHATSAPP_ENV"] = "production"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "987654321"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAABprod_test_token"
        os.environ["WHATSAPP_APP_SECRET"] = "def456secret"
        os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = "1234567890"
        os.environ.pop("WHATSAPP_DEFAULT_ORG_ID", None)

        config = WhatsAppSettings()
        errors = config.validate()
        assert errors == [], f"Expected no validation errors, got: {errors}"

    def test_production_does_not_require_default_org_id(self):
        """Production should NOT use WHATSAPP_DEFAULT_ORG_ID — org is resolved via DB."""
        os.environ["WHATSAPP_ENV"] = "production"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "987654321"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAABprod_test_token"
        os.environ["WHATSAPP_APP_SECRET"] = "def456secret"
        os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = "1234567890"
        os.environ["WHATSAPP_DEFAULT_ORG_ID"] = "should-be-ignored"

        config = WhatsAppSettings()
        errors = config.validate()
        assert errors == []


# ─── Invalid environment ───────────────────────────────────────────────────────

class TestInvalidEnvironment:
    def test_invalid_environment_fails_clearly(self):
        for bad_value in ("live", "test", "dev", "prod", "staging", "", "  "):
            os.environ["WHATSAPP_ENV"] = bad_value
            config = WhatsAppSettings()
            errors = config.validate()
            assert any("sandbox" in e.lower() and "production" in e.lower() for e in errors), (
                f"Expected invalid env error for '{bad_value}', got: {errors}"
            )

    def test_invalid_environment_does_not_check_credentials(self):
        """When the environment value is invalid, validation should bail
        immediately — before checking individual credentials — so the error
        message is clear and actionable."""
        os.environ["WHATSAPP_ENV"] = "live"
        os.environ.pop("WHATSAPP_PHONE_NUMBER_ID", None)
        os.environ.pop("WHATSAPP_ACCESS_TOKEN", None)

        config = WhatsAppSettings()
        errors = config.validate()
        # Should have exactly the invalid-env error, nothing else
        assert len(errors) == 1
        assert "sandbox" in errors[0] and "production" in errors[0]


# ─── Default for local development ─────────────────────────────────────────────

class TestDefaultEnvironment:
    def test_default_environment_is_sandbox(self):
        # Clear WHATSAPP_ENV so we test the default
        os.environ.pop("WHATSAPP_ENV", None)
        config = WhatsAppSettings()
        assert config.is_sandbox
        assert config.environment == "sandbox"
