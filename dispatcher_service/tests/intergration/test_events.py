import datetime as dt

from common.schemas import TaxiDeliveredEvent, TaxiPickupEvent
from dispatcher_service.app.domain import models
from dispatcher_service.app.domain.models import TaxiStatus, TripStatus
from dispatcher_service.tests.conftest import make_taxi


def test_events_pickup_and_delivered_202(client, db_session):
    # ARRANGE
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.BUSY)
    trip = models.Trip(
        user_id=1,
        taxi_id=taxi.id,
        status=TripStatus.REQUESTED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=10,
        start_y=10,
        end_x=20,
        end_y=20,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # ACT
    pickup_evt = TaxiPickupEvent(
        trip_id=trip.id,
        taxi_public_id=str(taxi.public_id),
        timestamp=dt.datetime.now(dt.UTC),
    ).model_dump(mode="json")

    r1 = client.post("/events/pickup", json=pickup_evt)
    assert r1.status_code == 202, r1.text
    db_session.refresh(trip)
    assert trip.status == TripStatus.IN_PROGRESS
    assert trip.pickup_time is not None

    delivered_evt = TaxiDeliveredEvent(
        trip_id=trip.id,
        taxi_public_id=str(taxi.public_id),
        dropoff_time=dt.datetime.now(dt.UTC).isoformat(),
        end_x=20,
        end_y=20,
    ).model_dump(mode="json")
    r2 = client.post("/events/delivered", json=delivered_evt)
    
    # ASSERT    
    assert r2.status_code == 202, r2.text
    db_session.refresh(trip)
    db_session.refresh(taxi)
    assert trip.status == TripStatus.COMPLETED
    assert taxi.status == TaxiStatus.AVAILABLE
    assert (taxi.x, taxi.y) == (20, 20)


def test_events_pickup_404_when_wrong_taxi(client, db_session):
    # ARRANGE
    wrong_uuid = "123e4567-e89b-12d3-a456-426614174000"
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.BUSY)
    trip = models.Trip(
        user_id=1,
        taxi_id=taxi.id,
        status=TripStatus.REQUESTED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=10,
        start_y=10,
        end_x=20,
        end_y=20,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    pickup_evt = TaxiPickupEvent(
        trip_id=trip.id,
        taxi_public_id=str(taxi.public_id),
        timestamp=dt.datetime.now(dt.UTC),
    ).model_dump(mode="json")

    # ACT
    _ = client.post("/events/pickup", json=pickup_evt)

    bad_evt = TaxiPickupEvent(
        trip_id=trip.id,
        taxi_public_id=str(wrong_uuid),
        timestamp=dt.datetime.now(dt.UTC),
    ).model_dump(mode="json")

    r = client.post("/events/pickup", json=bad_evt)

    # ASSERT
    assert r.status_code == 404


def test_events_delivered_404_when_trip_not_found(client, db_session):
    # ARRANGE
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.BUSY)
    bad_evt = TaxiDeliveredEvent(
        trip_id=9999,
        taxi_public_id=str(taxi.public_id),
        dropoff_time=dt.datetime.now(dt.UTC),
        end_x=20,
        end_y=20,
    ).model_dump(mode="json")

    # ACT
    r = client.post("/events/delivered", json=bad_evt)

    # ASSERT
    assert r.status_code == 404
