from common.schemas import OrderCreate
from dispatcher_service.app.domain.models import TaxiStatus, TripStatus
from dispatcher_service.tests.conftest import make_taxi


def test_orders_success_202(client, db_session, mock_assign_ok):
    # ARRANGE
    _ = make_taxi(db_session, 10, 10, TaxiStatus.AVAILABLE, cb="http://cb/assign")
    payload = OrderCreate(user_id=1, start_x=10, start_y=10, end_x=12, end_y=15)

    # ACT
    resp = client.post("/orders", json=payload.model_dump())

    # ASSERT
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["user_id"] == 1
    assert body["start_x"] == 10 and body["start_y"] == 10
    assert body["end_x"] == 12 and body["end_y"] == 15
    assert body["status"] in (TripStatus.REQUESTED.value, TripStatus.IN_PROGRESS.value)


def test_orders_no_available_taxi_409(client, db_session):
    # ARRANGE
    make_taxi(db_session, 1, 1, TaxiStatus.BUSY)
    make_taxi(db_session, 2, 2, TaxiStatus.OFFLINE)

    # ACT
    payload = {"user_id": 2, "start_x": 10, "start_y": 10, "end_x": 12, "end_y": 15}
    resp = client.post("/orders", json=payload)

    # ASSERT
    assert resp.status_code == 409
    assert "No available taxi" in resp.text
