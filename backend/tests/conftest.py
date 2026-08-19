"""Shared pytest fixtures for backend tests."""
from __future__ import annotations

import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set required environment variables before importing app modules.
os.environ.setdefault("PII_ENCRYPTION_KEY", "wEKM2r5xEhY_cLdA6siDCQRSn445fvmbGhxU3xgubE0=")
os.environ.setdefault("PII_BLIND_INDEX_KEY", "e86bfbc05711892c93076272b36a196575132a22e573709f5715ea3fdb9b8663")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")

from app.db.base import Base
from app.models.organization import Organization
from app.models.role import Role
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.payment_review_item import PaymentReviewItem
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.property import Property
from app.models.unit import Unit
from app.core.encryption import encrypt_value


# ── Engine / Session ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ── Base model fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def landlord_user(db: Session):
    user = User(id=str(uuid.uuid4()), email="landlord@test.com", full_name="Landlord", password_hash="test-hash")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def org(db: Session, landlord_user):
    org = Organization(id=str(uuid.uuid4()), name="Test Org", owner_id=landlord_user.id)
    db.add(org)
    db.flush()
    return org


@pytest.fixture
def landlord_role(db: Session):
    role = Role(id=str(uuid.uuid4()), name="landlord")
    db.add(role)
    db.flush()
    return role


@pytest.fixture
def tenant_role(db: Session):
    role = Role(id=str(uuid.uuid4()), name="tenant")
    db.add(role)
    db.flush()
    return role


@pytest.fixture
def finance_role(db: Session):
    role = Role(id=str(uuid.uuid4()), name="finance")
    db.add(role)
    db.flush()
    return role


@pytest.fixture
def landlord_membership(db: Session, org, landlord_user, landlord_role):
    member = OrganizationMember(
        id=str(uuid.uuid4()),
        user_id=landlord_user.id,
        organization_id=org.id,
        role_id=landlord_role.id,
    )
    db.add(member)
    db.flush()
    return member


@pytest.fixture
def tenant_user(db: Session, org, tenant_role):
    user = User(id=str(uuid.uuid4()), email="tenant@test.com", full_name="Tenant User", password_hash="test-hash")
    db.add(user)
    db.flush()
    member = OrganizationMember(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=org.id,
        role_id=tenant_role.id,
    )
    db.add(member)
    db.flush()
    return user


@pytest.fixture
def tenant_record(db: Session, org, tenant_user):
    phone = "+254725123456"
    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        full_name="Test Tenant",
        phone=phone,
        alternative_phone=None,
        email=None,
        id_number=None,
        user_id=tenant_user.id,
    )
    db.add(tenant)
    db.flush()
    return tenant


@pytest.fixture
def active_lease(db: Session, org, tenant_record):
    lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        unit_id=str(uuid.uuid4()),
        tenant_id=tenant_record.id,
        start_date=datetime(2026, 1, 1).date(),
        end_date=None,
        rent_amount=25000,
        status="active",
    )
    db.add(lease)
    db.flush()
    return lease


@pytest.fixture
def property(db: Session, org):
    prop = Property(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        name="Silverleaf Apartments",
        address="123 Riverside Drive",
        city="Nairobi",
        country="Kenya",
    )
    db.add(prop)
    db.flush()
    return prop


@pytest.fixture
def unit(db: Session, org, property):
    unit = Unit(
        id=str(uuid.uuid4()),
        property_id=property.id,
        name="A1",
        description="Corner unit",
        bedrooms=2,
        bathrooms=1,
        size_sqm=65.5,
        rent_amount=35000,
        is_active=True,
    )
    db.add(unit)
    db.flush()
    return unit
