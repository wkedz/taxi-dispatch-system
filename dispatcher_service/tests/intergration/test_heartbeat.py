import datetime as dt

from common.schemas import TaxiHeartbeat
from dispatcher_service.app.domain import models
from dispatcher_service.tests.conftest import make_taxi


def test_heartbeat_updates_last_seen(client, db_session):
    # ARRANGE
    taxi = make_taxi(db_session, 5, 5, models.TaxiStatus.AVAILABLE)
    old_seen = taxi.last_seen_at

    evt = TaxiHeartbeat(
        taxi_public_id=str(taxi.public_id),
        timestamp=dt.datetime.now(dt.UTC),
    ).model_dump(mode="json")

    # ACT
    r = client.post("/taxis/heartbeat", json=evt)

    # ASSERT
    assert r.status_code == 204, r.text
    assert taxi.last_seen_at is not None
    assert taxi.last_seen_at != old_seen


def test_heartbeat_returns_404_for_missing_taxi(client):
    # ARRANGE
    evt = TaxiHeartbeat(
        taxi_public_id="00000000-0000-0000-0000-000000000000",
        timestamp=dt.datetime.now(dt.UTC),
    ).model_dump(mode="json")

    # ACT
    r = client.post("/taxis/heartbeat", json=evt)

    # ASSERT
    assert r.status_code == 404
    assert "Taxi not found" in r.text
