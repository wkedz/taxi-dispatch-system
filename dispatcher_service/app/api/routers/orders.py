from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from common.schemas import OrderCreate, TripRead
from dispatcher_service.app.adapters import crud
from dispatcher_service.app.api.dependencies import get_db_session
from dispatcher_service.app.domain.services import assign_order

from common.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=TripRead, status_code=status.HTTP_202_ACCEPTED)
async def create_order(order: OrderCreate, db: Session = Depends(get_db_session)):
    trip = await assign_order(db, order)
    if trip is None:
        logger.info("No available taxi found")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No available taxi found")
    return trip


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int = Path(..., ge=1), db: Session = Depends(get_db_session)):
    trip = crud.get_trip(db, trip_id)
    if not trip:
        logger.info(f"Trip id={trip_id} not found")
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
