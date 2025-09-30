from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime

from common.schemas import AssignPayload, TaxiDeliveredEvent, TaxiPickupEvent
from taxi_service.app.adapters.http_client import post_json
from taxi_service.app.domain.schemas import TaxiState
from taxi_service.app.settings import settings

from common.logger import get_logger
logger = get_logger(__name__)

def _manhattan(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x1 - x2) + abs(y1 - y2)


async def simulate_trip(assign: AssignPayload, taxi: TaxiState) -> None:
    d1 = _manhattan(taxi.x, taxi.y, assign.start_x, assign.start_y)
    d2 = _manhattan(assign.start_x, assign.start_y, assign.end_x, assign.end_y)

    rng = random.Random()
    smin = max(1, settings.SPEED_MIN)
    smax = max(smin, settings.SPEED_MAX)

    pickup_minutes = sum(rng.randint(smin, smax) for _ in range(d1))
    travel_minutes = sum(rng.randint(smin, smax) for _ in range(d2))

    pickup_sleep = pickup_minutes / max(0.0001, settings.TIME_SCALE)
    travel_sleep = travel_minutes / max(0.0001, settings.TIME_SCALE)

    logger.info(f"Simulating trip {assign.trip_id}:")
    logger.info(
        f" - distance to pickup: {d1}, estimated time: {pickup_minutes} min ({pickup_sleep:.1f} s)"
    )
    logger.info(
        f" - distance to dropoff: {d2}, estimated time: {travel_minutes} min ({travel_sleep:.1f} s)"
    )
    logger.info(
        f" - total estimated time: {pickup_minutes + travel_minutes} min ({pickup_sleep + travel_sleep:.1f} s)"
    )
    await asyncio.sleep(pickup_sleep)
    pickup_evt = TaxiPickupEvent(
        trip_id=assign.trip_id,
        taxi_public_id=taxi.public_id,
        timestamp=datetime.now(UTC),
    ).model_dump(mode="json")
    logger.info("Sending pickup event:", pickup_evt)
    await post_json(f"{settings.DISPATCHER_BASE_URL}events/pickup", pickup_evt)
    logger.info("Pickup event sent")

    await asyncio.sleep(travel_sleep)
    delivered_evt = TaxiDeliveredEvent(
        trip_id=assign.trip_id,
        taxi_public_id=taxi.public_id,
        dropoff_time=datetime.now(UTC),
        end_x=assign.end_x,
        end_y=assign.end_y,
    ).model_dump(mode="json")
    logger.info("Sending delivered event:", delivered_evt)
    await post_json(f"{settings.DISPATCHER_BASE_URL}events/delivered", delivered_evt)
    logger.info("Delivered event sent")

    taxi.x = assign.end_x
    taxi.y = assign.end_y
