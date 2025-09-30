import datetime as dt

import pytest
from sqlalchemy.orm import Session

from common.schemas import OrderCreate, TaxiCreate, TaxiDeliveredEvent, TaxiPickupEvent, TaxiStatus
from dispatcher_service.app.adapters import crud
from dispatcher_service.app.domain.models import Trip, TripStatus
from dispatcher_service.app.domain.services import assign_order
from dispatcher_service.tests.conftest import make_taxi


def test_create_taxi(db_session):
    # ARRANGE
    taxi_in = TaxiCreate(x=7, y=9, callback_url="http://cb")

    # ACT
    taxi = crud.create_taxi(db_session, taxi_in)

    # ASSERT
    assert taxi.id is not None
    assert taxi.public_id is not None
    assert taxi.status == TaxiStatus.AVAILABLE
    assert taxi.x == 7 and taxi.y == 9
    assert isinstance(taxi.callback_url, str) or taxi.callback_url is not None


def test_count_taxis_by_status(db_session):
    # ACT
    make_taxi(db_session, 1, 1, TaxiStatus.AVAILABLE)
    make_taxi(db_session, 2, 2, TaxiStatus.BUSY)
    make_taxi(db_session, 3, 3, TaxiStatus.OFFLINE)

    # ASSERT
    assert crud.count_taxis(db_session, TaxiStatus.AVAILABLE) == 1
    assert crud.count_taxis(db_session, TaxiStatus.BUSY) == 1
    assert crud.count_taxis(db_session, TaxiStatus.OFFLINE) == 1


def test_mark_taxis_status(db_session):
    # ARRANGE
    taxi = make_taxi(db_session, 5, 5, TaxiStatus.AVAILABLE)

    # ACT & ASSERT
    crud.mark_taxi_busy(db_session, taxi)
    db_session.commit()
    db_session.refresh(taxi)
    assert taxi.status == TaxiStatus.BUSY

    crud.mark_taxi_available(db_session, taxi)
    db_session.commit()
    db_session.refresh(taxi)
    assert taxi.status == TaxiStatus.AVAILABLE

    crud.mark_taxi_offline(db_session, taxi)
    db_session.commit()
    db_session.refresh(taxi)
    assert taxi.status == TaxiStatus.OFFLINE


def test_pick_closest_available_taxi_for_update(db_session):
    # ARRANGE
    _ = make_taxi(db_session, 50, 50, TaxiStatus.AVAILABLE)
    t_close = make_taxi(db_session, 9, 9, TaxiStatus.AVAILABLE)
    _ = make_taxi(db_session, 20, 20, TaxiStatus.AVAILABLE)

    # ACT
    picked = crud.pick_closest_available_taxi_for_update(db_session, 10, 10)

    # ASSERT
    assert picked is not None
    assert picked.id == t_close.id


def test_pick_closest_omits_non_available(db_session):
    # ARRANGE
    make_taxi(db_session, 9, 9, TaxiStatus.BUSY)
    make_taxi(db_session, 8, 8, TaxiStatus.OFFLINE)
    t_ok = make_taxi(db_session, 50, 50, TaxiStatus.AVAILABLE)

    # ACT
    picked = crud.pick_closest_available_taxi_for_update(db_session, 10, 10)

    # ASSERT
    assert picked is not None
    assert picked.id == t_ok.id


def test_create_trip_requested(db_session):
    # ARRANGE
    taxi = make_taxi(db_session, 1, 1, TaxiStatus.AVAILABLE)
    order = OrderCreate(user_id=42, start_x=1, start_y=1, end_x=2, end_y=3)

    # ACT
    trip = crud.create_trip_requested(db_session, order, taxi_id=taxi.id)
    db_session.commit()
    db_session.refresh(trip)

    # ASSERT
    assert trip.id is not None
    assert trip.taxi_id == taxi.id
    assert trip.user_id == 42
    assert trip.status == TripStatus.REQUESTED
    assert trip.start_x == 1 and trip.start_y == 1
    assert trip.end_x == 2 and trip.end_y == 3


@pytest.mark.asyncio
async def test_create_order(db_session, mock_taxi_calls):
    # ARRANGE
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.AVAILABLE, cb="http://cb/assign")
    order = OrderCreate(user_id=1, start_x=10, start_y=10, end_x=12, end_y=15)

    # ACT
    assigned = await assign_order(db_session, order)

    # ASSERT
    assert assigned is not None
    assert assigned.user_id == order.user_id
    assert assigned.taxi_id == taxi.id
    assert assigned.status == TripStatus.REQUESTED
    assert taxi.status == TaxiStatus.BUSY
    assert mock_taxi_calls, "Brak wywołań do taxi"


def test_event_pickup(db_session: Session):
    # ARRANGE
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.AVAILABLE)
    trip = Trip(
        user_id=1,
        taxi=taxi,
        status=TripStatus.REQUESTED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=10,
        start_y=10,
        end_x=20,
        end_y=20,
    )
    db_session.add_all([taxi, trip])
    db_session.commit()

    evt = TaxiPickupEvent(
        trip_id=trip.id, taxi_public_id=taxi.public_id, timestamp=dt.datetime.now(dt.UTC)
    )

    # ACT
    ok = crud.event_pickup(db_session, evt)

    # ASSERT
    db_session.refresh(trip)
    assert ok is True
    assert trip.status == TripStatus.IN_PROGRESS
    assert trip.pickup_time is not None
    assert trip.waiting_time_min >= 0


def test_event_delivered(db_session: Session):
    # ARRANGE
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.AVAILABLE)
    trip = Trip(
        user_id=1,
        taxi=taxi,
        status=TripStatus.IN_PROGRESS,
        request_time=dt.datetime.now(dt.UTC),
        pickup_time=dt.datetime.now(dt.UTC),
        start_x=5,
        start_y=5,
        end_x=15,
        end_y=15,
    )
    db_session.add_all([taxi, trip])
    db_session.commit()

    dropoff_time = dt.datetime.now(dt.UTC)
    evt = TaxiDeliveredEvent(
        trip_id=trip.id,
        taxi_public_id=taxi.public_id,
        dropoff_time=dropoff_time,
        end_x=15,
        end_y=15,
    )

    # ACT
    ok = crud.event_delivered(db_session, evt)

    # ASSERT
    db_session.refresh(trip)
    db_session.refresh(taxi)
    assert ok is True
    assert trip.status == TripStatus.COMPLETED
    assert taxi.status == TaxiStatus.AVAILABLE
    assert (taxi.x, taxi.y) == (15, 15)


@pytest.mark.asyncio
async def test_assign_order_failure_compensates(db_session, monkeypatch):
    # ARRANGE
    taxi = make_taxi(db_session, 5, 5, TaxiStatus.AVAILABLE, cb="http://cb/assign")
    order = OrderCreate(user_id=123, start_x=1, start_y=1, end_x=2, end_y=2)

    from dispatcher_service.app import adapters

    async def fake_post_json(url, payload, **kwargs):
        class DummyResp:
            status_code = 500
            text = "Internal Error"

        return DummyResp()

    monkeypatch.setattr(adapters.http_client, "post_json", fake_post_json)

    # ACT
    assigned = await assign_order(db_session, order)

    # ASSERT
    assert assigned is None
    assert taxi.status == TaxiStatus.AVAILABLE
    trips = crud.get_all_trips(db_session)
    assert len(trips) == 1
    assert trips[0].status == TripStatus.CANCELLED


@pytest.mark.asyncio
async def test_assign_order_no_available_taxi(db_session):
    # ARRANGE
    make_taxi(db_session, 10, 10, TaxiStatus.BUSY)
    order = OrderCreate(user_id=1, start_x=5, start_y=5, end_x=6, end_y=6)

    # ACT
    assigned = await assign_order(db_session, order)

    # ASSERT
    assert assigned is None
    trips = crud.get_all_trips(db_session)
    assert trips == []


def test_event_pickup_invalid_taxi_public_id(db_session: Session):
    # ARRANGE
    wrong_uuid = "fc149bf5-62fe-4f47-a20c-c0face7ab2b9"
    taxi = make_taxi(db_session, 5, 5, TaxiStatus.AVAILABLE)
    trip = Trip(
        user_id=1,
        taxi=taxi,
        status=TripStatus.REQUESTED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=5,
        start_y=5,
        end_x=10,
        end_y=10,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    evt = TaxiPickupEvent(
        trip_id=trip.id, taxi_public_id=wrong_uuid, timestamp=dt.datetime.now(dt.UTC)
    )

    # ACT
    ok = crud.event_pickup(db_session, evt)

    # ASSERT — brak zmian
    assert ok is False
    db_session.refresh(trip)
    assert trip.status == TripStatus.REQUESTED
    assert trip.pickup_time is None


def test_event_pickup_trip_in_wrong_state(db_session: Session):
    # ARRANGE
    taxi = make_taxi(db_session, 5, 5, TaxiStatus.AVAILABLE)
    trip = Trip(
        user_id=1,
        taxi=taxi,
        status=TripStatus.COMPLETED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=1,
        start_y=1,
        end_x=2,
        end_y=2,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    evt = TaxiPickupEvent(
        trip_id=trip.id, taxi_public_id=taxi.public_id, timestamp=dt.datetime.now(dt.UTC)
    )

    # ACT
    ok = crud.event_pickup(db_session, evt)

    # ASSERT
    assert ok is True
    db_session.refresh(trip)
    assert trip.status == TripStatus.COMPLETED
    assert trip.pickup_time is None


def test_event_delivered_trip_not_found(db_session: Session):
    # ARRANGE
    not_existing_trip = 999
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.AVAILABLE)

    evt = TaxiDeliveredEvent(
        trip_id=not_existing_trip,
        taxi_public_id=taxi.public_id,
        dropoff_time=dt.datetime.now(dt.UTC),
        end_x=20,
        end_y=20,
    )

    # ACT
    ok = crud.event_delivered(db_session, evt)

    # ASSERT
    assert ok is False


def test_event_delivered_without_pickup(db_session: Session):
    # ARRANGE — trip REQUESTED, bez pickup
    taxi = make_taxi(db_session, 5, 5, TaxiStatus.AVAILABLE)
    trip = Trip(
        user_id=1,
        taxi=taxi,
        status=TripStatus.REQUESTED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=5,
        start_y=5,
        end_x=15,
        end_y=15,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    evt = TaxiDeliveredEvent(
        trip_id=trip.id,
        taxi_public_id=taxi.public_id,
        dropoff_time=dt.datetime.now(dt.UTC),
        end_x=15,
        end_y=15,
    )

    # ACT
    ok = crud.event_delivered(db_session, evt)

    # ASSERT
    assert ok is True
    db_session.refresh(trip)
    assert trip.status == TripStatus.COMPLETED
    assert (trip.end_x, trip.end_y) == (15, 15)
