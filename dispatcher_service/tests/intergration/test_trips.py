import datetime as dt
import re

from dispatcher_service.app.domain import models
from dispatcher_service.app.domain.models import TaxiStatus, TripStatus
from dispatcher_service.tests.conftest import make_taxi


def test_trips_get_sorted_and_limited(client, db_session):
    # ARRANGE
    taxi = make_taxi(db_session, 10, 10, TaxiStatus.BUSY)
    t1 = models.Trip(
        user_id=1,
        taxi_id=taxi.id,
        status=TripStatus.REQUESTED,
        request_time=dt.datetime.now(dt.UTC),
        start_x=1,
        start_y=1,
        end_x=2,
        end_y=2,
    )
    t2 = models.Trip(
        user_id=1,
        taxi_id=taxi.id,
        status=TripStatus.IN_PROGRESS,
        request_time=dt.datetime.now(dt.UTC),
        pickup_time=dt.datetime.now(dt.UTC),
        start_x=3,
        start_y=3,
        end_x=4,
        end_y=4,
    )
    t3 = models.Trip(
        user_id=1,
        taxi_id=taxi.id,
        status=TripStatus.COMPLETED,
        request_time=dt.datetime.now(dt.UTC),
        pickup_time=dt.datetime.now(dt.UTC),
        dropoff_time=dt.datetime.now(dt.UTC),
        start_x=5,
        start_y=5,
        end_x=6,
        end_y=6,
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    # ACT
    r = client.get("/trips", params={"limit": 2})
    assert r.status_code == 200
    data = r.json()

    # ASSERT
    assert len(data) == 2
    assert data[0]["id"] > data[1]["id"]

    # Daty jako ISO
    date_keys = ("request_time", "pickup_time", "dropoff_time")
    iso_like = re.compile(r"^\d{4}-\d{2}-\d{2}T")
    for item in data:
        for k in date_keys:
            v = item.get(k)
            if v is not None:
                assert isinstance(v, str)
                assert iso_like.search(v)
