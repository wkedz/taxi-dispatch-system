import asyncio
import random

import httpx

from client_service.app.settings import settings
from common.schemas import OrderCreate
from common.logger import get_logger
logger = get_logger(__name__)

class ClientSimulator:
    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def _generate_orders(self):
        async with httpx.AsyncClient() as client:
            while self._running:
                user_id = random.randint(1, 10000)
                start_x = random.randint(1, settings.GRID_SIZE)
                start_y = random.randint(1, settings.GRID_SIZE)
                end_x = random.randint(1, settings.GRID_SIZE)
                end_y = random.randint(1, settings.GRID_SIZE)

                payload = OrderCreate(
                    user_id=user_id,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                ).model_dump(mode="json")

                logger.info(f"Sending order: {payload}")
                logger.info(f"Dispatcher URL: {settings.DISPATCHER_BASE_URL}/orders")
                try:
                    resp = await client.post(f"{settings.DISPATCHER_BASE_URL}/orders", json=payload)
                    if resp.status_code == 202:
                        logger.info(f"Order created: {payload}")
                    else:
                        logger.error(f"Failed to create order: {resp.status_code} {resp.text}")
                except Exception as e:
                    logger.error(f"Error sending order: {e}")

                await asyncio.sleep(settings.FREQUENCY_SECONDS)

    async def start(self):
        logger.info("Starting Client Simulator")
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._generate_orders())

    async def stop(self):
        logger.info("Stopping Client Simulator")
        if self._running:
            self._running = False
            if self._task:
                await self._task
                self._task = None
