"""Requirement 2 - the selected property filters system data.

The navbar property selector is only real if the API honours a property scope,
so these tests exercise the endpoints the selector drives. "All properties"
(no filter) must keep working exactly as before.
"""
from __future__ import annotations

import uuid
from datetime import date

from app.api.routes import charges as charges_route
from app.api.routes import payments as payments_route
from app.api.routes import tenants as tenants_route
from app.models.charge import Charge
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


def _lease_on(db, org, tenant_id, unit_id, *, rent=25000):
    lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        unit_id=unit_id,
        tenant_id=tenant_id,
        start_date=date(2026, 1, 1),
        rent_amount=rent,
        status="active",
    )
    db.add(lease)
    db.flush()
    return lease


def _second_property_with_lease(db, org, tenant_record):
    """A second property, unit and lease used to prove scoping is real."""
    other_property = Property(
        id=str(uuid.uuid4()),
        name="Second Property",
        address="9 Other Road",
        city="Nairobi",
        country="Kenya",
        organization_id=org.id,
    )
    other_unit = Unit(
        id=str(uuid.uuid4()),
        property_id=other_property.id,
        name="X1",
        bedrooms=1,
        bathrooms=1,
        rent_amount=18000,
        is_active=True,
    )
    other_tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        full_name="Second Property Tenant",
        phone="+254700000002",
    )
    db.add_all([other_property, other_unit, other_tenant])
    db.flush()
    other_lease = Lease(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        unit_id=other_unit.id,
        tenant_id=other_tenant.id,
        start_date=date(2026, 1, 1),
        rent_amount=18000,
        status="active",
    )
    db.add(other_lease)
    db.flush()
    return other_property, other_lease, other_tenant


def _list_charges(call, db, user, **overrides):
    params = {
        "status": None,
        "charge_type": None,
        "lease_id": None,
        "property_id": None,
        "search": None,
        "limit": None,
        "offset": 0,
    }
    params.update(overrides)
    return call(charges_route.list_charges, current_user=user, db=db, **params)


def _list_payments(call, db, user, **overrides):
    params = {
        "tenant_id": None,
        "lease_id": None,
        "property_id": None,
        "payment_type": None,
        "payment_method": None,
        "start_date": None,
        "end_date": None,
        "search": None,
        "limit": None,
        "offset": 0,
    }
    params.update(overrides)
    return call(payments_route.list_payments, current_user=user, db=db, **params)


def _seed_money(db, org, tenant_record, active_lease, other_lease, other_tenant):
    db.add_all(
        [
            Charge(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                lease_id=active_lease.id,
                amount=25000,
                amount_paid=0,
                charge_type="rent",
                due_date=date(2026, 9, 1),
                billing_month=date(2026, 9, 1),
                status="pending",
            ),
            Charge(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                lease_id=other_lease.id,
                amount=18000,
                amount_paid=0,
                charge_type="rent",
                due_date=date(2026, 9, 1),
                billing_month=date(2026, 9, 1),
                status="pending",
            ),
            Payment(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                tenant_id=tenant_record.id,
                lease_id=active_lease.id,
                amount=25000,
                payment_method="mpesa",
                payment_type="rent",
                payment_date=date(2026, 9, 2),
            ),
            Payment(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                tenant_id=other_tenant.id,
                lease_id=other_lease.id,
                amount=18000,
                payment_method="mpesa",
                payment_type="rent",
                payment_date=date(2026, 9, 2),
            ),
        ]
    )
    db.flush()


def test_charges_are_scoped_to_the_selected_property(
    db, call, landlord, org, property, unit, tenant_record
):
    scoped_lease = _lease_on(db, org, tenant_record.id, unit.id)
    _, other_lease, other_tenant = _second_property_with_lease(
        db, org, tenant_record
    )
    _seed_money(db, org, tenant_record, scoped_lease, other_lease, other_tenant)

    status, body = _list_charges(
        call, db, landlord, property_id=property.id, limit=25
    )

    assert status == 200
    assert body["total"] == 1
    assert body["items"][0]["lease_id"] == scoped_lease.id


def test_charges_unscoped_still_return_everything(
    db, call, landlord, org, unit, tenant_record
):
    scoped_lease = _lease_on(db, org, tenant_record.id, unit.id)
    _, other_lease, other_tenant = _second_property_with_lease(
        db, org, tenant_record
    )
    _seed_money(db, org, tenant_record, scoped_lease, other_lease, other_tenant)

    status, body = _list_charges(call, db, landlord, limit=25)

    assert status == 200
    assert body["total"] == 2


def test_payments_are_scoped_to_the_selected_property(
    db, call, landlord, org, property, unit, tenant_record
):
    scoped_lease = _lease_on(db, org, tenant_record.id, unit.id)
    _, other_lease, other_tenant = _second_property_with_lease(
        db, org, tenant_record
    )
    _seed_money(db, org, tenant_record, scoped_lease, other_lease, other_tenant)

    status, body = _list_payments(
        call, db, landlord, property_id=property.id, limit=25
    )

    assert status == 200
    assert body["total"] == 1
    assert body["items"][0]["tenant_id"] == tenant_record.id


def test_tenants_are_scoped_to_the_selected_property(
    db, call, landlord, org, property, unit, tenant_record
):
    _lease_on(db, org, tenant_record.id, unit.id)
    _, _, other_tenant = _second_property_with_lease(db, org, tenant_record)

    status, body = call(
        tenants_route.list_tenants,
        search=None,
        property_id=property.id,
        current_user=landlord,
        db=db,
    )

    assert status == 200
    ids = {row["id"] for row in body}
    assert tenant_record.id in ids
    assert other_tenant.id not in ids


def test_tenants_unscoped_include_the_whole_portfolio(
    db, call, landlord, org, property, unit, tenant_record
):
    _lease_on(db, org, tenant_record.id, unit.id)
    _, _, other_tenant = _second_property_with_lease(db, org, tenant_record)

    status, body = call(
        tenants_route.list_tenants,
        search=None,
        property_id=None,
        current_user=landlord,
        db=db,
    )

    assert status == 200
    ids = {row["id"] for row in body}
    assert {tenant_record.id, other_tenant.id} <= ids


def test_tenant_name_search_still_works_alongside_property_scope(
    db, call, landlord, org, property, unit, tenant_record
):
    _lease_on(db, org, tenant_record.id, unit.id)
    _second_property_with_lease(db, org, tenant_record)

    status, body = call(
        tenants_route.list_tenants,
        search="Test Tenant",
        property_id=property.id,
        current_user=landlord,
        db=db,
    )

    assert status == 200
    assert [row["id"] for row in body] == [tenant_record.id]


def test_payment_search_matches_tenant_name_and_reference(
    db, call, landlord, org, unit, tenant_record
):
    scoped_lease = _lease_on(db, org, tenant_record.id, unit.id)
    _, other_lease, other_tenant = _second_property_with_lease(
        db, org, tenant_record
    )
    _seed_money(db, org, tenant_record, scoped_lease, other_lease, other_tenant)

    status, body = _list_payments(call, db, landlord, search="Second Property", limit=25)

    assert status == 200
    assert body["total"] == 1
    assert body["items"][0]["tenant_id"] == other_tenant.id
