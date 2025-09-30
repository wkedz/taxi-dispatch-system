import time

from common.schemas import AssignPayload


def _has_call(calls, suffix: str) -> bool:
    return any(call["url"].endswith(suffix) for call in calls)


def test_registers_taxi_on_startup(client, mock_dispatcher_calls):
    # ACT & ASSERT
    assert _has_call(
        mock_dispatcher_calls, "/taxis/register"
    ), f"No taxi registration call. Collected calls: {mock_dispatcher_calls}"


def test_deregister_on_shutdown(mock_dispatcher_calls):
    # ARRANGE
    from fastapi.testclient import TestClient

    from taxi_service.app.main import app

    # ACT
    with TestClient(app) as _:
        pass

    # ASSERT
    assert _has_call(
        mock_dispatcher_calls, "/taxis/deregister"
    ), f"No deregister call, calls={mock_dispatcher_calls}"


def test_assign_triggers_events(client, mock_dispatcher_calls, fast_simulation):
    # ARRANGE
    payload = AssignPayload(trip_id=123, start_x=10, start_y=10, end_x=11, end_y=12)

    # ACT
    resp = client.post("/assign", json=payload.model_dump(mode="json"))

    # ASSERT
    assert resp.status_code == 202, "Assign should return 202 Accepted"

    for _ in range(40):
        if _has_call(mock_dispatcher_calls, "/events/pickup") and _has_call(
            mock_dispatcher_calls, "/events/delivered"
        ):
            break
        time.sleep(1)

    assert _has_call(mock_dispatcher_calls, "/events/pickup"), f"No pickup: {mock_dispatcher_calls}"
    assert _has_call(
        mock_dispatcher_calls, "/events/delivered"
    ), f"No delivered: {mock_dispatcher_calls}"
