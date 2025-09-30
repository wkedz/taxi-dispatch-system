# dispatcher_service/tests/conftest.py
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from dispatcher_service.app.api.dependencies import get_db_session
from dispatcher_service.app.domain.models import Base, Taxi, TaxiStatus
from dispatcher_service.app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def fast_assign_retries(monkeypatch):
    from dispatcher_service.app.settings import settings

    monkeypatch.setattr(settings, "ASSIGN_RETRIES", 1, raising=False)
    return True


@pytest.fixture
def mock_assign_ok(monkeypatch):
    import dispatcher_service.app.domain.services as services

    class DummyResp:
        def __init__(self, code=200, payload=None):
            self.status_code = code
            self._payload = payload or {"status": True}
            self.text = json.dumps(self._payload)

        def json(self):
            return self._payload

    async def fake_post(url, payload, **kwargs):
        return DummyResp(200, {"status": True})

    monkeypatch.setattr(services, "post_json", fake_post, raising=True)
    return True


@pytest.fixture
def mock_assign_fail(monkeypatch):
    import dispatcher_service.app.domain.services as services

    class DummyResp:
        def __init__(self, code=500, text="fail"):
            self.status_code = code
            self.text = text

        def json(self):
            return {"status": False}

    async def fake_post(url, payload, **kwargs):
        return DummyResp(500, "fail")

    monkeypatch.setattr(services, "post_json", fake_post, raising=True)
    return True


@pytest.fixture
def db_engine():
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    return TestClient(app)


@pytest.fixture
def mock_taxi_calls(monkeypatch):
    calls: list[dict] = []

    class DummyResp:
        def __init__(self, status_code=200, data=None):
            self.status_code = status_code
            self._data = data or {"ok": True}
            self.text = json.dumps(self._data)

        def json(self):
            return self._data

    async def fake_post(url, payload, **kwargs):
        calls.append({"url": url, "json": payload})
        return DummyResp(200, {"status": True})

    import dispatcher_service.app.domain.services as services

    monkeypatch.setattr(services, "post_json", fake_post, raising=True)

    return calls


def make_taxi(session, x=10, y=10, status=TaxiStatus.AVAILABLE, cb="http://cb"):
    t = Taxi(x=x, y=y, status=status, callback_url=cb)
    session.add(t)
    session.commit()
    session.refresh(t)
    return t
