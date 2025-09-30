from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status

from common.schemas import AssignPayload
from taxi_service.app.api.dependencies import get_taxi
from taxi_service.app.domain.schemas import TaxiState
from taxi_service.app.services.simulation import simulate_trip

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def assign(
    payload: AssignPayload, tasks: BackgroundTasks, taxi: TaxiState = Depends(get_taxi)
) -> dict:
    tasks.add_task(simulate_trip, payload, taxi)
    return {"accepted": True, "trip_id": payload.trip_id}
