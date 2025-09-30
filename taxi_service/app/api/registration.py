from __future__ import annotations

import random

from fastapi import FastAPI

from common.schemas import TaxiCreate, TaxiDeregister, TaxiRead
from taxi_service.app.adapters.http_client import post_json
from taxi_service.app.domain.schemas import TaxiState
from taxi_service.app.services.callback import get_callback_ip
from taxi_service.app.settings import settings

from common.logger import get_logger
logger = get_logger(__name__)

async def _register() -> TaxiState:
    x = random.randint(1, settings.GRID_SIZE)
    y = random.randint(1, settings.GRID_SIZE)

    if settings.PUBLIC_CALLBACK_URL:
        cb = str(settings.PUBLIC_CALLBACK_URL)
    else:
        ip = get_callback_ip()
        cb = f"http://{ip}:{settings.TAXI_SERVICE_PORT}/assign"

    try:
        payload = TaxiCreate(x=x, y=y, callback_url=cb).model_dump(mode="json")
        logger.info(f"Registering taxi with payload: {payload}")
        data = await post_json(f"{settings.DISPATCHER_BASE_URL}taxis/register", payload)
    except Exception as exc:
        logger.error(f"Error during taxi registration: {exc}")
        return
    data = TaxiRead.model_validate(data)

    logger.info(f"Registered taxi: {data}")
    return TaxiState(public_id=data.public_id, x=data.x, y=data.y)


async def _deregister(public_id: str) -> None:
    try:
        payload = TaxiDeregister(taxi_public_id=public_id).model_dump(mode="json")
        await post_json(f"{settings.DISPATCHER_BASE_URL}taxis/deregister", payload)
        logger.info(f"Deregistered taxi {public_id}")
    except Exception as exc:
        logger.error(f"Error during taxi deregistration: {exc}")
        return


async def startup_register(app: FastAPI) -> None:
    if app.state.taxi is None:
        try:
            app.state.taxi = await _register()
        except Exception as exc:
            logger.exception(f"Error during startup registration: {exc}")


async def shutdown_deregister(app: FastAPI) -> None:
    if app.state.taxi:
        try:
            await _deregister(app.state.taxi.public_id)
        except Exception as exc:
            logger.exception(f"Error during shutdown deregistration: {exc}")
