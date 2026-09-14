"""Shared helpers for endpoint-level tests.

The repository has no httpx dependency, so starlette's TestClient cannot be
used. These helpers call the real FastAPI endpoint functions directly,
passing the ``current_user`` and ``db`` arguments that the ``Depends``
defaults would normally supply. That exercises the same permission checks,
queries and serialisation as an HTTP call, with the only gap being FastAPI's
own request parsing layer.
"""
from __future__ import annotations

import os
import sys
import tempfile
import types
import uuid

import pytest

# Routers that accept uploads (tenants, expenses, leases) create their upload
# directory at import time, defaulting to /app/uploads. Point that at a
# throwaway temp directory so importing them in tests works anywhere.
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="alphaone-test-uploads-"))
from fastapi import HTTPException


# The rate limiter (slowapi) is only needed by app.main and the auth router.
# Some local/CI environments install the app's requirements minus that optional
# dependency; when it is genuinely missing we install a minimal no-op stub so
# the routers under test can still be imported. If slowapi IS installed it is
# always preferred - the stub is a fallback, never a shadow.
try:  # pragma: no cover - depends on the environment
    import slowapi  # noqa: F401
except ImportError:  # pragma: no cover - exercised only without slowapi
    slowapi = types.ModuleType("slowapi")
    slowapi_errors = types.ModuleType("slowapi.errors")
    slowapi_middleware = types.ModuleType("slowapi.middleware")
    slowapi_util = types.ModuleType("slowapi.util")

    class _NoopLimiter:
        def __init__(self, *args, **kwargs):
            pass

        def limit(self, *args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

    class _RateLimitExceeded(Exception):
        detail = "rate limited"

    slowapi.Limiter = _NoopLimiter
    slowapi_errors.RateLimitExceeded = _RateLimitExceeded
    slowapi_middleware.SlowAPIMiddleware = object
    slowapi_util.get_remote_address = lambda request: "127.0.0.1"

    sys.modules.setdefault("slowapi", slowapi)
    sys.modules.setdefault("slowapi.errors", slowapi_errors)
    sys.modules.setdefault("slowapi.middleware", slowapi_middleware)
    sys.modules.setdefault("slowapi.util", slowapi_util)


from app.core.roles import (  # noqa: E402
    FINANCE,
    LANDLORD,
    PROPERTY_MANAGER,
    TENANT,
)
from app.models.organization_member import OrganizationMember  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.users import User  # noqa: E402


def make_role(db, name: str) -> Role:
    """Create a role with its production (upper-case) name."""
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(id=str(uuid.uuid4()), name=name)
    db.add(role)
    db.flush()
    return role


def make_user_with_role(db, org, name: str, email: str, role_name: str):
    """Create a user + organisation membership carrying ``role_name``."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        full_name=name,
        password_hash="test-hash",
    )
    db.add(user)
    db.flush()
    membership = OrganizationMember(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=org.id,
        role_id=make_role(db, role_name).id,
    )
    db.add(membership)
    db.flush()
    return user


@pytest.fixture
def roles(db):
    """Ensure every production role exists."""
    return {name: make_role(db, name) for name in (LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT)}


@pytest.fixture
def landlord(db, org):
    return make_user_with_role(db, org, "Landlord", "landlord@example.com", LANDLORD)


@pytest.fixture
def property_manager(db, org):
    return make_user_with_role(
        db, org, "Manager", "manager@example.com", PROPERTY_MANAGER
    )


@pytest.fixture
def finance_user(db, org):
    return make_user_with_role(db, org, "Finance", "finance@example.com", FINANCE)


@pytest.fixture
def tenant_user_account(db, org):
    return make_user_with_role(db, org, "Tenant", "tenant@example.com", TENANT)


def call(endpoint, *args, **kwargs):
    """Call an endpoint function and normalise the result.

    Returns ``(status_code, body)`` where body is the returned value or the
    ``{"detail": ...}`` payload of an HTTPException - i.e. what a client would
    have seen.
    """
    try:
        return 200, endpoint(*args, **kwargs)
    except HTTPException as exc:
        return exc.status_code, {"detail": exc.detail}


@pytest.fixture(name="call")
def call_fixture():
    """Expose ``call`` as a fixture so tests don't need a cross-package import."""
    return call
