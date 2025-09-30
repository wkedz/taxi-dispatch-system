from __future__ import annotations

import asyncio

import httpx

from dispatcher_service.app.settings import settings
from common.logger import get_logger
logger = get_logger(__name__)

async def post_json(url: str, payload: dict) -> httpx.Response:
    timeout = httpx.Timeout(settings.ASSIGN_TIMEOUT_SEC)
    retry = settings.ASSIGN_RETRIES
    for attempt in range(retry):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"POST {url} with payload: {payload}")
                resp = await client.post(url, json=payload)
                if resp.status_code in (200, 201, 202):
                    return resp
        except Exception as exc:  # noqa: BLE001
            logger.error(f"POST {url} failed (attempt {attempt + 1}/{retry}): {exc}")
            if attempt + 1 == retry:
                logger.error(f"Giving up on POST {url}")
                raise
            await asyncio.sleep(1 + attempt * 2)  # backoff
