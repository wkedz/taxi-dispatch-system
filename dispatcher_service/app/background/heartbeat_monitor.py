from __future__ import annotations

import asyncio

from dispatcher_service.app.adapters.crud import sweep_offline_taxis
from dispatcher_service.app.adapters.database import SessionLocal
from dispatcher_service.app.settings import settings


async def heartbeat_sweeper() -> None:
    interval = max(1, settings.HEARTBEAT_SWEEP_INTERVAL_SEC)
    ttl = max(1, settings.HEARTBEAT_TTL_SEC)
    while True:
        try:
            with SessionLocal() as db:
                sweep_offline_taxis(db, ttl_sec=ttl)
        except Exception:
            pass
        await asyncio.sleep(interval)
