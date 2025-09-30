# dispatcher_service/tests/integration/test_api.py


from common.schemas import TaxiCreate
from dispatcher_service.app.domain.models import TaxiStatus


def test_taxis_register_and_list_and_count(client, db_session):
    # ARRANGE + ACT
    payload = TaxiCreate(x=7, y=9, callback_url="http://cb/assign").model_dump(mode="json")
    r = client.post("/taxis/register", json=payload)
    assert r.status_code in (200, 201)
    taxi = r.json()
    assert taxi["x"] == 7 and taxi["y"] == 9
    assert taxi["status"] == TaxiStatus.AVAILABLE.value

    # ARRANGE + ACT
    r2 = client.get("/taxis")
    assert r2.status_code == 200
    lst = r2.json()
    assert any(t["id"] == taxi["id"] for t in lst)

    # ARRANGE + ACT
    r3 = client.get("/taxis/count", params={"status": TaxiStatus.AVAILABLE.value})
    assert r3.status_code == 200
    cnt = r3.json()
    assert cnt["status"] == TaxiStatus.AVAILABLE.value
    assert isinstance(cnt["count"], int)
    assert cnt["count"] >= 1
