"""Tests for the WhatsApp organization resolver.

Covers:
  - WhatsAppIntegration resolves correct organization
  - sandbox default organization fallback works
  - unknown production phone_number_id does not route to wrong org
  - sandbox falls back when no integration row exists
  - production rejects unknown phone_number_id
  - is_active flag respected
  - empty phone_number_id returns None
"""
import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.users import User
from app.models.whatsapp_integration import WhatsAppIntegration
from app.services.messaging.organization_resolver import resolve_organization


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def org(db: Session, landlord_user):
    org = Organization(id=str(uuid.uuid4()), name="Test Org", owner_id=landlord_user.id)
    db.add(org)
    db.flush()
    return org


# ─── DB-driven resolution ──────────────────────────────────────────────────────

class TestIntegrationResolution:
    def test_integration_resolves_correct_org(self, db: Session, org):
        """WhatsAppIntegration maps phone_number_id → organization_id."""
        integration = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="7234567890",
            environment=settings.whatsapp.environment,
            is_active=True,
        )
        db.add(integration)
        db.flush()

        result = resolve_organization(db, "7234567890")
        assert result == org.id

    def test_is_active_false_not_resolved(self, db: Session, org):
        """An inactive integration row should not resolve."""
        integration = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="9999999999",
            environment=settings.whatsapp.environment,
            is_active=False,
        )
        db.add(integration)
        db.flush()

        result = resolve_organization(db, "9999999999")
        # If sandbox, should fall back to default_org_id; if prod, should return None
        if settings.whatsapp.environment == "sandbox" and settings.whatsapp.default_org_id:
            assert result == settings.whatsapp.default_org_id
        else:
            assert result is None

    def test_different_phone_number_different_org(self, db: Session, org, landlord_user):
        """Two different phone numbers resolve to different orgs."""
        other_org = Organization(id=str(uuid.uuid4()), name="Other Org", owner_id=landlord_user.id)
        db.add(other_org)
        db.flush()

        integration1 = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="1111111111",
            environment=settings.whatsapp.environment,
            is_active=True,
        )
        integration2 = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=other_org.id,
            meta_phone_number_id="2222222222",
            environment=settings.whatsapp.environment,
            is_active=True,
        )
        db.add_all([integration1, integration2])
        db.flush()

        assert resolve_organization(db, "1111111111") == org.id
        assert resolve_organization(db, "2222222222") == other_org.id


# ─── Sandbox fallback ──────────────────────────────────────────────────────────

class TestSandboxFallback:
    def test_sandbox_fallback_to_default_org(self, db: Session, monkeypatch):
        """When no integration row exists, sandbox falls back to WHATSAPP_DEFAULT_ORG_ID."""
        monkeypatch.setattr(settings.whatsapp, "environment", "sandbox")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "sandbox-fallback-uuid")

        result = resolve_organization(db, "unknown-phone-number-id")
        assert result == "sandbox-fallback-uuid"

    def test_sandbox_fallback_logged_as_sandbox(self, db: Session, monkeypatch, caplog):
        """The fallback should be clearly labeled as a sandbox-only mechanism."""
        monkeypatch.setattr(settings.whatsapp, "environment", "sandbox")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "sandbox-uuid")

        import logging
        with caplog.at_level(logging.INFO):
            result = resolve_organization(db, "unknown-phone-number-id")

        assert result == "sandbox-uuid"
        assert any("SANDBOX FALLBACK" in record.message for record in caplog.records)

    def test_sandbox_no_fallback_no_integration_returns_none(self, db: Session, monkeypatch):
        """If sandbox has no integration row AND no default_org_id, return None."""
        monkeypatch.setattr(settings.whatsapp, "environment", "sandbox")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "")

        result = resolve_organization(db, "unknown-phone-number-id")
        assert result is None


# ─── Production rejection ──────────────────────────────────────────────────────

class TestProductionRejection:
    def test_production_unknown_number_returns_none(self, db: Session, monkeypatch, caplog):
        """Production must NOT silently route unknown numbers to an arbitrary org."""
        monkeypatch.setattr(settings.whatsapp, "environment", "production")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "prod-org-uuid")

        import logging
        with caplog.at_level(logging.ERROR):
            result = resolve_organization(db, "unknown-phone-number-id")

        assert result is None
        assert any("unknown" in record.message.lower() for record in caplog.records)

    def test_production_known_number_resolves_via_integration(self, db: Session, org, monkeypatch):
        """Production resolves org ONLY via WhatsAppIntegration, never via default_org_id."""
        integration = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="7234567890",
            environment="production",
            is_active=True,
        )
        db.add(integration)
        db.flush()

        monkeypatch.setattr(settings.whatsapp, "environment", "production")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "wrong-org-uuid")

        result = resolve_organization(db, "7234567890")
        assert result == org.id

    def test_production_does_not_use_default_org_id(self, db: Session, monkeypatch):
        """Production must not route to WHATSAPP_DEFAULT_ORG_ID even if set."""
        monkeypatch.setattr(settings.whatsapp, "environment", "production")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "should-not-be-used")

        result = resolve_organization(db, "unregistered-phone-number-id")
        assert result is None


# ─── Edge cases ─────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_phone_number_id_returns_none(self, db: Session, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            result = resolve_organization(db, None)
        assert result is None
        assert any("no phone_number_id" in record.message for record in caplog.records)

    def test_empty_string_phone_number_id_returns_none(self, db: Session):
        result = resolve_organization(db, "")
        assert result is None

    def test_environment_isolation(self, db: Session, org, monkeypatch):
        """Sandbox and production integrations are isolated — same phone_number_id
        in both environments resolves to potentially different orgs."""
        integration_sandbox = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="12345",
            environment="sandbox",
            is_active=True,
        )
        integration_prod = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="12345",
            environment="production",
            is_active=True,
        )
        db.add_all([integration_sandbox, integration_prod])
        db.flush()

        monkeypatch.setattr(settings.whatsapp, "environment", "sandbox")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "fallback-uuid")
        result_sandbox = resolve_organization(db, "12345")
        assert result_sandbox == org.id

        monkeypatch.setattr(settings.whatsapp, "environment", "production")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "should-not-be-used")
        result_prod = resolve_organization(db, "12345")
        assert result_prod == org.id

    def test_tenant_isolation_via_org_scoping(self, db: Session, org, landlord_user, monkeypatch):
        """Two orgs with different phone numbers should resolve independently.
        A WhatsAppIntegration for org A's phone number must not resolve to org B."""
        org_b = Organization(id=str(uuid.uuid4()), name="Org B", owner_id=landlord_user.id)
        db.add(org_b)
        db.flush()

        integration_a = WhatsAppIntegration(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            meta_phone_number_id="AAA_PHONE",
            environment="sandbox",
            is_active=True,
        )
        integration_b = WhatsAppIntegration(
            id=str(uuid.uuid.uuid4()) if False else str(uuid.uuid4()),
            organization_id=org_b.id,
            meta_phone_number_id="BBB_PHONE",
            environment="sandbox",
            is_active=True,
        )
        db.add_all([integration_a, integration_b])
        db.flush()

        monkeypatch.setattr(settings.whatsapp, "environment", "sandbox")
        monkeypatch.setattr(settings.whatsapp, "default_org_id", "fallback-uuid")

        assert resolve_organization(db, "AAA_PHONE") == org.id
        assert resolve_organization(db, "BBB_PHONE") == org_b.id
