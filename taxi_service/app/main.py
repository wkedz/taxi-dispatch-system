from __future__ import annotations

from fastapi import FastAPI

from taxi_service.app.api.registration import shutdown_deregister, startup_register
from taxi_service.app.api.routers import assign
from taxi_service.app.background.heartbeat import start_heartbeat
from taxi_service.app.domain.schemas import TaxiState
from common.logger import configure_root_logging, get_logger

configure_root_logging(service_name="taxi")
log = get_logger(__name__)
log.info("Taxi app booting")


async def lifespan(app: FastAPI):
    app.state.taxi: TaxiState | None = None
    await startup_register(app)
    await start_heartbeat(app.state.taxi.public_id)  # type: ignore[arg-type]
    yield
    await shutdown_deregister(app)


app = FastAPI(title="Taxi Service", lifespan=lifespan)

app.include_router(assign.router, prefix="/assign", tags=["Assign"])


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "taxi_public_id": app.state.taxi.public_id if app.state.taxi else None}  # type: ignore[attr-defined]
