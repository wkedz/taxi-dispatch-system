import datetime as dt

from sqlalchemy.orm import Session

from common.schemas import TaxiDeliveredEvent, TaxiPickupEvent
from dispatcher_service.app.adapters import crud
from dispatcher_service.app.domain.models import TaxiStatus, Trip, TripStatus
from dispatcher_service.tests.conftest import make_taxi


def test_event_pickup_idempotent(db_session: Session):
    # ARRANGE
    taxi = make_taxi(db_session, x=10, y=10, cb="http://cb")
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
    db_session.refresh(trip)

    # ACT
    evt1 = TaxiPickupEvent(
        trip_id=trip.id, taxi_public_id=taxi.public_id, timestamp=dt.datetime.now(dt.UTC)
    )
    ok1 = crud.event_pickup(db_session, evt1)

    first_wait = trip.waiting_time_min

    evt2 = TaxiPickupEvent(
        trip_id=trip.id, taxi_public_id=taxi.public_id, timestamp=dt.datetime.now(dt.UTC)
    )
    ok2 = crud.event_pickup(db_session, evt2)

    # ASSERT
    assert ok1 is True
    assert trip.status == TripStatus.IN_PROGRESS
    assert trip.pickup_time is not None

    assert ok2 is True
    assert trip.status == TripStatus.IN_PROGRESS
    assert trip.waiting_time_min == first_wait


def test_event_delivered_idempotent(db_session: Session):
    # ARRANGE
    taxi = make_taxi(db_session, x=10, y=10, cb="http://cb")
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
    db_session.refresh(trip)
    db_session.refresh(taxi)

    # ACT
    t1 = dt.datetime.now(dt.UTC)
    evt1 = TaxiDeliveredEvent(
        trip_id=trip.id, taxi_public_id=taxi.public_id, dropoff_time=t1, end_x=15, end_y=15
    )
    ok1 = crud.event_delivered(db_session, evt1)
    db_session.refresh(trip)
    db_session.refresh(taxi)


    t2 = dt.datetime.now(dt.UTC)
    evt2 = TaxiDeliveredEvent(
        trip_id=trip.id, taxi_public_id=taxi.public_id, dropoff_time=t2, end_x=15, end_y=15
    )
    ok2 = crud.event_delivered(db_session, evt2)
    db_session.refresh(trip)
    db_session.refresh(taxi)

    # ASSERT
    assert ok1 is True
    assert trip.status == TripStatus.COMPLETED
    assert taxi.status == TaxiStatus.AVAILABLE
    assert (taxi.x, taxi.y) == (15, 15)

    assert ok2 is True
    assert trip.status == TripStatus.COMPLETED
    assert taxi.status == TaxiStatus.AVAILABLE
    assert (taxi.x, taxi.y) == (15, 15)
