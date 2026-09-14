"""Requirements 4 and 6 - billing charge-type filters and payment date range.

Both filters are applied in the database query (not post-filtered in the
browser), so these tests assert on the returned totals as well as the rows -
a paginated "total" that ignores the active filter would be a bug.
"""
from __future__ import annotations

import uuid
from datetime import date

from app.api.routes import charges as charges_route
from app.api.routes import payments as payments_route
from app.models.charge import Charge
from app.models.payment import Payment


def _charge(org, lease_id, *, charge_type, amount, due, month, status="pending"):
    return Charge(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        lease_id=lease_id,
        amount=amount,
        amount_paid=0,
        charge_type=charge_type,
        due_date=due,
        billing_month=month,
        status=status,
    )


def _payment(org, tenant_id, lease_id, *, amount, payment_date, payment_type="rent"):
    return Payment(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        tenant_id=tenant_id,
        lease_id=lease_id,
        amount=amount,
        payment_method="mpesa",
        payment_type=payment_type,
        payment_date=payment_date,
    )


def _list_charges(call, db, user, **overrides):
    """Call the charges endpoint with every Query default made explicit.

    ``Query(None)`` objects are placeholders that FastAPI resolves at request
    time; calling the function directly means supplying them ourselves.
    """
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


# ─── Charge type filter ──────────────────────────────────────────────────


def test_charges_can_be_filtered_to_rent_only(
    db, call, landlord, org, tenant_record, active_lease
):
    db.add_all(
        [
            _charge(
                org,
                active_lease.id,
                charge_type="rent",
                amount=25000,
                due=date(2026, 9, 1),
                month=date(2026, 9, 1),
            ),
            _charge(
                org,
                active_lease.id,
                charge_type="deposit",
                amount=25000,
                due=date(2026, 1, 1),
                month=date(2026, 1, 1),
            ),
        ]
    )
    db.flush()

    status, body = _list_charges(call, db, landlord, limit=25, charge_type="rent")

    assert status == 200
    assert body["total"] == 1
    assert [row["charge_type"] for row in body["items"]] == ["rent"]


def test_charges_can_be_filtered_to_deposits_only(
    db, call, landlord, org, tenant_record, active_lease
):
    db.add_all(
        [
            _charge(
                org,
                active_lease.id,
                charge_type="rent",
                amount=25000,
                due=date(2026, 9, 1),
                month=date(2026, 9, 1),
            ),
            _charge(
                org,
                active_lease.id,
                charge_type="deposit",
                amount=25000,
                due=date(2026, 1, 1),
                month=date(2026, 1, 1),
            ),
        ]
    )
    db.flush()

    status, body = _list_charges(call, db, landlord, limit=25, charge_type="deposit")

    assert status == 200
    assert body["total"] == 1
    assert [row["charge_type"] for row in body["items"]] == ["deposit"]


def test_unfiltered_charge_list_still_returns_everything(
    db, call, landlord, org, tenant_record, active_lease
):
    db.add_all(
        [
            _charge(
                org,
                active_lease.id,
                charge_type="rent",
                amount=25000,
                due=date(2026, 9, 1),
                month=date(2026, 9, 1),
            ),
            _charge(
                org,
                active_lease.id,
                charge_type="deposit",
                amount=25000,
                due=date(2026, 1, 1),
                month=date(2026, 1, 1),
            ),
        ]
    )
    db.flush()

    status, body = _list_charges(call, db, landlord, limit=25)

    assert status == 200
    assert body["total"] == 2


def test_invalid_charge_type_is_rejected(db, call, landlord):
    status, body = _list_charges(
        call, db, landlord, limit=25, charge_type="utilities"
    )
    assert status == 400
    assert "rent" in body["detail"]


# ─── Payment history date filter ─────────────────────────────────────────


def test_payment_history_date_range_filters_results_and_total(
    db, call, landlord, org, tenant_record, active_lease
):
    db.add_all(
        [
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=25000,
                payment_date=date(2026, 8, 5),
            ),
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=25000,
                payment_date=date(2026, 9, 5),
            ),
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=5000,
                payment_date=date(2026, 9, 20),
            ),
        ]
    )
    db.flush()

    status, body = _list_payments(
        call, db, landlord,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        limit=25,
    )

    assert status == 200
    assert body["total"] == 2
    assert all(
        row["payment_date"] >= date(2026, 9, 1) for row in body["items"]
    )


def test_payment_range_spanning_a_year_boundary(
    db, call, landlord, org, tenant_record, active_lease
):
    """Date filters must behave across month/year boundaries."""
    db.add_all(
        [
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=1000,
                payment_date=date(2025, 12, 31),
            ),
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=2000,
                payment_date=date(2026, 1, 1),
            ),
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=3000,
                payment_date=date(2026, 2, 1),
            ),
        ]
    )
    db.flush()

    status, body = _list_payments(
        call, db, landlord,
        start_date=date(2025, 12, 31),
        end_date=date(2026, 1, 1),
        limit=25,
    )

    assert status == 200
    assert body["total"] == 2


def test_reversed_payment_date_range_is_rejected(db, call, landlord):
    status, body = _list_payments(
        call, db, landlord,
        start_date=date(2026, 9, 30),
        end_date=date(2026, 9, 1),
        limit=25,
    )
    assert status == 400
    assert "start_date" in body["detail"]


def test_payment_date_filter_respects_tenant_filter(
    db, call, landlord, org, tenant_record, active_lease
):
    other_tenant_id = str(uuid.uuid4())
    from app.models.tenant import Tenant

    db.add(
        Tenant(
            id=other_tenant_id,
            organization_id=org.id,
            full_name="Other Tenant",
            phone="+254711111111",
        )
    )
    db.add_all(
        [
            _payment(
                org,
                tenant_record.id,
                active_lease.id,
                amount=1000,
                payment_date=date(2026, 9, 5),
            ),
            _payment(
                org,
                other_tenant_id,
                active_lease.id,
                amount=2000,
                payment_date=date(2026, 9, 6),
            ),
        ]
    )
    db.flush()

    status, body = _list_payments(
        call, db, landlord,
        tenant_id=tenant_record.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        limit=25,
    )

    assert status == 200
    assert body["total"] == 1
    assert body["items"][0]["tenant_id"] == tenant_record.id


def test_payment_history_with_no_matches_returns_empty_envelope(
    db, call, landlord
):
    status, body = _list_payments(
        call, db, landlord,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        limit=25,
    )
    assert status == 200
    assert body == {"items": [], "total": 0, "limit": 25, "offset": 0}
