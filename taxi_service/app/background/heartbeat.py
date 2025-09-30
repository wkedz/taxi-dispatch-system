from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx

from common.schemas import TaxiHeartbeat
from taxi_service.app.settings import settings


async def _send_heartbeat(public_id: str) -> None:
    base = str(settings.DISPATCHER_BASE_URL).rstrip("/")
    payload = TaxiHeartbeat(taxi_public_id=public_id, timestamp=datetime.now(UTC)).model_dump(
        mode="json"
    )
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(f"{base}/taxis/heartbeat", json=payload)


async def _heartbeat_loop(public_id: str) -> None:
    while True:
        try:
            await _send_heartbeat(public_id)
        except Exception:
            pass
        await asyncio.sleep(settings.HEARTBEAT_INTERVAL_SEC)


async def start_heartbeat(public_id: str) -> None:
    asyncio.create_task(_heartbeat_loop(public_id))
