import json

import httpx
import pytest
from fastapi.testclient import TestClient

from common.schemas import TaxiRead
from taxi_service.app.main import app


@pytest.fixture(autouse=True)
def fast_simulation(monkeypatch):
   try:
       import taxi_service.app.settings as sett
       if hasattr(sett, "TIME_SCALE"):
           monkeypatch.setattr(sett, "TIME_SCALE", 1e-9, raising=False)
       monkeypatch.setattr(sett, "SPEED_MIN", 1, raising=False)
       monkeypatch.setattr(sett, "SPEED_MAX", 1, raising=False)
   except ModuleNotFoundError:
       pass

@pytest.fixture
def mock_dispatcher_calls(monkeypatch):
    calls: list[dict] = []

    class DummyResp:
        def __init__(self, status_code: int, data: dict):
            self.status_code = status_code
            self._data = data
            self.text = json.dumps(data)

        def json(self):
            return self._data

    async def fake_post(self, url, *args, **kwargs):
        payload = kwargs.get("json")
        calls.append({"url": url, "json": payload})

        if url.endswith("/taxis/register"):
            return DummyResp(
                201,
                TaxiRead(
                    id=1,
                    public_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    status="available",
                    x=1,
                    y=1,
                ).model_dump(mode="json"),
            )

        if url.endswith("/events/pickup") or url.endswith("/events/delivered"):
            return DummyResp(200, {"ok": True})

        if url.endswith("/taxis/deregister"):
            return DummyResp(204, {"ok": True})

        return DummyResp(200, {"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post, raising=True)
    return calls


@pytest.fixture
def client(mock_dispatcher_calls):
    with TestClient(app) as c:
        yield c
