from fastapi import Request

from taxi_service.app.domain.schemas import TaxiState


def get_taxi(request: Request) -> TaxiState:
    taxi = getattr(request.app.state, "taxi", None)
    if taxi is None:
        raise RuntimeError("Taxi not registered yet")
    return taxi
