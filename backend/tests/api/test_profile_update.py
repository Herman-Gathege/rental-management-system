"""Requirement 8 - fully editable, safe profile page.

Covers the fields a user may change, the validation that guards them, and -
most importantly - that nothing outside the permitted set can be changed
through this endpoint.
"""
from __future__ import annotations

import uuid

from app.api.routes import auth as auth_route
from app.models.users import User


def _update(call, db, user, **payload):
    return call(
        auth_route.update_me,
        auth_route.ProfileUpdate(**payload),
        current_user=user,
        db=db,
    )


def test_phone_is_normalised_to_e164(db, call, landlord):
    status, body = _update(call, db, landlord, phone="0712 345 678")

    assert status == 200
    assert body["phone"] == "+254712345678"
    db.refresh(landlord)
    assert landlord.phone == "+254712345678"


def test_changing_phone_requires_reverification(db, call, landlord):
    landlord.phone_verified = True
    db.flush()

    status, body = _update(call, db, landlord, phone="0722000111")

    assert status == 200
    assert body["phone_verified"] is False
    db.refresh(landlord)
    assert landlord.phone_verified is False


def test_invalid_phone_is_rejected_and_not_stored(db, call, landlord):
    status, body = _update(call, db, landlord, phone="12345")

    assert status == 400
    assert "phone number" in body["detail"]
    db.refresh(landlord)
    assert landlord.phone is None


def test_phone_already_used_by_another_account_is_rejected(db, call, landlord):
    db.add(
        User(
            id=str(uuid.uuid4()),
            email="other@example.com",
            full_name="Other",
            password_hash="x",
            phone="+254700000001",
        )
    )
    db.flush()

    status, body = _update(call, db, landlord, phone="0700000001")

    assert status == 400
    assert "already in use" in body["detail"]


def test_full_name_can_be_cleared(db, call, landlord):
    status, body = _update(call, db, landlord, full_name="   ")

    assert status == 200
    assert body["full_name"] is None


def test_email_change_requires_the_current_password(db, call, landlord):
    status, body = _update(call, db, landlord, email="new@example.com")

    assert status == 400
    assert "current password" in body["detail"]
    db.refresh(landlord)
    assert landlord.email == "landlord@example.com"


def test_email_change_rejects_a_duplicate_address(db, call, landlord, monkeypatch):
    db.add(
        User(
            id=str(uuid.uuid4()),
            email="taken@example.com",
            full_name="Taken",
            password_hash="x",
        )
    )
    db.flush()
    monkeypatch.setattr(auth_route, "verify_password", lambda *a, **k: True)

    status, body = _update(
        call,
        db,
        landlord,
        email="taken@example.com",
        current_password="whatever",
    )

    assert status == 400
    assert "already registered" in body["detail"]


def test_email_change_succeeds_with_the_current_password(db, call, landlord, monkeypatch):
    monkeypatch.setattr(auth_route, "verify_password", lambda *a, **k: True)

    status, body = _update(
        call,
        db,
        landlord,
        email="New.Address@Example.com",
        current_password="whatever",
    )

    assert status == 200
    assert body["email"] == "new.address@example.com"


def test_protected_fields_cannot_be_changed_through_the_profile_api(db, call, landlord):
    """Extra keys are ignored by the request model - a caller cannot use the
    profile endpoint to grant themselves a role or move organisations."""
    before_email = landlord.email
    before_role = landlord.role_id
    before_active = landlord.is_active

    status, body = _update(
        call,
        db,
        landlord,
        full_name="Renamed",
        role="SYSTEM",
        role_id="some-other-role",
        is_active=False,
        organization_id="another-org",
        password_hash="injected",
    )

    assert status == 200
    db.refresh(landlord)
    assert landlord.full_name == "Renamed"
    assert landlord.email == before_email
    assert landlord.role_id == before_role
    assert landlord.is_active == before_active
    assert landlord.password_hash == "test-hash"
