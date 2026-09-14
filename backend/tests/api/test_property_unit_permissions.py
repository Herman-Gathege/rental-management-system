"""Requirement 1 - landlord-only CRUD for properties and units.

The backend is the source of truth: these tests call the API directly (no
frontend involved) and assert that every non-landlord role is refused, that the
landlord can complete the full workflow, and that the safeguards around units
with leases/payment history still hold.
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.api.routes import properties as properties_route
from app.api.routes import units as units_route
from app.models.lease import Lease
from app.models.property_manager import PropertyManager
from app.models.property_finance_manager import PropertyFinanceManager
from app.models.tenant import Tenant
from app.models.unit import Unit


def _new_property_payload(name="Lakeview Court"):
    return {
        "name": name,
        "address": "12 Riverside Drive",
        "city": "Nairobi",
        "country": "Kenya",
    }


def _new_unit_payload(property_id, name="B2"):
    return {
        "property_id": property_id,
        "name": name,
        "description": "Two bedroom",
        "bedrooms": 2,
        "bathrooms": 1,
        "size_sqm": 70,
        "rent_amount": 40000,
    }


# ─── Unit mutations are landlord-only ────────────────────────────────────


@pytest.mark.parametrize(
    "fixture_name",
    ["property_manager", "finance_user", "tenant_user_account"],
)
def test_non_landlord_cannot_create_unit(
    db, call, property, request, fixture_name
):
    actor = request.getfixturevalue(fixture_name)
    status, _ = call(
        units_route.create_unit,
        units_route.UnitCreate(**_new_unit_payload(property.id)),
        current_user=actor,
        db=db,
    )
    assert status == 403
    assert db.query(Unit).filter(Unit.name == "B2").first() is None


def test_landlord_can_create_unit(db, call, landlord, property):
    status, body = call(
        units_route.create_unit,
        units_route.UnitCreate(**_new_unit_payload(property.id)),
        current_user=landlord,
        db=db,
    )
    assert status == 200
    assert body["name"] == "B2"


@pytest.mark.parametrize(
    "fixture_name",
    ["property_manager", "finance_user", "tenant_user_account"],
)
def test_non_landlord_cannot_update_or_delete_unit(
    db, call, unit, request, fixture_name
):
    actor = request.getfixturevalue(fixture_name)
    put_status, _ = call(
        units_route.update_unit,
        unit.id,
        units_route.UnitUpdate(name="Renamed"),
        current_user=actor,
        db=db,
    )
    delete_status, _ = call(
        units_route.delete_unit, unit.id, current_user=actor, db=db
    )
    assert put_status == 403
    assert delete_status == 403
    db.refresh(unit)
    assert unit.name == "A1"


def test_landlord_can_update_unit(db, call, landlord, unit):
    status, _ = call(
        units_route.update_unit,
        unit.id,
        units_route.UnitUpdate(rent_amount=45500),
        current_user=landlord,
        db=db,
    )
    assert status == 200
    db.refresh(unit)
    assert float(unit.rent_amount) == 45500


# ─── Unit deletion safeguards ────────────────────────────────────────────


def test_landlord_cannot_delete_unit_with_active_lease(
    db, call, landlord, unit, tenant_record
):
    db.add(
        Lease(
            id=str(uuid.uuid4()),
            organization_id=tenant_record.organization_id,
            unit_id=unit.id,
            tenant_id=tenant_record.id,
            start_date=date(2026, 1, 1),
            rent_amount=40000,
            status="active",
        )
    )
    db.flush()
    status, body = call(units_route.delete_unit, unit.id, current_user=landlord, db=db)
    assert status == 400
    assert "active lease" in body["detail"]
    assert db.query(Unit).filter(Unit.id == unit.id).first() is not None


def test_landlord_cannot_delete_unit_with_payment_history(
    db, call, landlord, unit, tenant_record
):
    """A past (non-active) lease still blocks deletion - its charges and
    payments must not be cascaded away."""
    db.add(
        Lease(
            id=str(uuid.uuid4()),
            organization_id=tenant_record.organization_id,
            unit_id=unit.id,
            tenant_id=tenant_record.id,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            rent_amount=40000,
            status="ended",
        )
    )
    db.flush()
    status, body = call(units_route.delete_unit, unit.id, current_user=landlord, db=db)
    assert status == 400
    assert "payment history" in body["detail"]


def test_landlord_can_delete_unit_without_history(db, call, landlord, unit):
    status, _ = call(units_route.delete_unit, unit.id, current_user=landlord, db=db)
    assert status == 200
    assert db.query(Unit).filter(Unit.id == unit.id).first() is None


# ─── Property deletion safeguards ────────────────────────────────────────


def test_non_landlord_cannot_delete_property(db, call, property_manager, property):
    status, _ = call(
        properties_route.delete_property,
        property.id,
        current_user=property_manager,
        db=db,
    )
    assert status == 403


def test_landlord_cannot_delete_property_that_has_units(
    db, call, landlord, property, unit
):
    status, body = call(
        properties_route.delete_property,
        property.id,
        current_user=landlord,
        db=db,
    )
    assert status == 400
    assert "unit" in body["detail"]


def test_landlord_can_delete_empty_property(db, call, landlord, org):
    empty = properties_route.Property(
        id=str(uuid.uuid4()),
        name="Empty Plot",
        address="Nowhere",
        city="Nairobi",
        country="Kenya",
        organization_id=org.id,
    )
    db.add(empty)
    db.flush()
    status, _ = call(
        properties_route.delete_property, empty.id, current_user=landlord, db=db
    )
    assert status == 200
    assert (
        db.query(properties_route.Property)
        .filter(properties_route.Property.id == empty.id)
        .first()
        is None
    )


def test_landlord_cannot_delete_property_from_another_organisation(
    db, call, landlord, org
):
    """Cross-organisation access must fail closed, not 500 or leak."""
    other_org_id = str(uuid.uuid4())
    from app.models.organization import Organization

    db.add(
        Organization(id=other_org_id, name="Other Org", owner_id=str(uuid.uuid4()))
    )
    foreign = properties_route.Property(
        id=str(uuid.uuid4()),
        name="Not Yours",
        address="Elsewhere",
        city="Mombasa",
        country="Kenya",
        organization_id=other_org_id,
    )
    db.add(foreign)
    db.flush()
    status, _ = call(
        properties_route.delete_property, foreign.id, current_user=landlord, db=db
    )
    assert status == 404
    assert (
        db.query(properties_route.Property)
        .filter(properties_route.Property.id == foreign.id)
        .first()
        is not None
    )


# ─── Read scoping ────────────────────────────────────────────────────────


def test_property_manager_unit_list_is_scoped_to_assigned_properties(
    db, call, property_manager, property, unit, org
):
    other = Unit(
        id=str(uuid.uuid4()),
        property_id=str(uuid.uuid4()),
        name="Other A1",
        bedrooms=1,
        bathrooms=1,
        rent_amount=20000,
        is_active=True,
    )
    db.add(other)
    db.add(
        PropertyManager(
            id=str(uuid.uuid4()),
            property_id=property.id,
            user_id=property_manager.id,
        )
    )
    db.flush()
    status, body = call(units_route.list_units, None, current_user=property_manager, db=db)
    assert status == 200
    names = {row["name"] for row in body}
    assert names == {"A1"}


def test_finance_user_unit_list_is_scoped_to_assigned_properties(
    db, call, finance_user, property, unit
):
    unassigned_status, unassigned = call(
        units_route.list_units, None, current_user=finance_user, db=db
    )
    assert unassigned_status == 200
    assert unassigned == []

    db.add(
        PropertyFinanceManager(
            id=str(uuid.uuid4()),
            property_id=property.id,
            user_id=finance_user.id,
        )
    )
    db.flush()

    assigned_status, assigned = call(
        units_route.list_units, None, current_user=finance_user, db=db
    )
    assert assigned_status == 200
    assert {row["name"] for row in assigned} == {"A1"}


def test_tenant_sees_only_units_they_lease(
    db, call, tenant_user_account, org, unit
):
    """A tenant may read their own unit (the ticket form needs it) but nothing
    else in the portfolio."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        full_name="Tenant Account",
        phone="+254700000000",
        user_id=tenant_user_account.id,
    )
    db.add(tenant)
    other_unit = Unit(
        id=str(uuid.uuid4()),
        property_id=str(uuid.uuid4()),
        name="Not Mine",
        bedrooms=1,
        bathrooms=1,
        rent_amount=15000,
        is_active=True,
    )
    db.add(other_unit)
    db.flush()
    db.add(
        Lease(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            unit_id=unit.id,
            tenant_id=tenant.id,
            start_date=date(2026, 1, 1),
            rent_amount=40000,
            status="active",
        )
    )
    db.flush()
    list_status, listing = call(
        units_route.list_units, None, current_user=tenant_user_account, db=db
    )
    assert list_status == 200
    assert {row["name"] for row in listing} == {"A1"}

    forbidden_status, _ = call(
        units_route.get_unit, other_unit.id, current_user=tenant_user_account, db=db
    )
    assert forbidden_status == 404
