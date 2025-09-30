import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dispatcher_service.app.api.routers import events, orders, taxis, view
from dispatcher_service.app.background.heartbeat_monitor import heartbeat_sweeper

from common.logger import configure_root_logging, get_logger

async def lifespan(app: FastAPI):
    asyncio.create_task(heartbeat_sweeper())
    yield


app = FastAPI(title="Taxi Dispatch Service")

configure_root_logging(service_name="dispatcher")
log = get_logger(__name__)
log.info("Dispatcher app booting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(taxis.router, prefix="/taxis", tags=["Taxis"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(view.router, tags=["View"])


@app.get("/healthz", tags=["Health"])
def health_check():
    return {"status": "ok"}
