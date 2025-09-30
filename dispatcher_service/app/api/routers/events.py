from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.schemas import TaxiDeliveredEvent, TaxiPickupEvent
from dispatcher_service.app.adapters import crud
from dispatcher_service.app.api.dependencies import get_db_session

from common.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()


@router.post("/pickup", status_code=status.HTTP_202_ACCEPTED)
def event_pickup(evt: TaxiPickupEvent, db: Session = Depends(get_db_session)):
    logger.info(f"Pickup event received: {evt}")
    ok = crud.event_pickup(db, evt)
    logger.info(f"Pickup event processed: {ok}")
    if not ok:
        raise HTTPException(status_code=404, detail="Trip not found or taxi mismatch")
    return {"status": True}


@router.post("/delivered", status_code=status.HTTP_202_ACCEPTED)
def event_delivered(evt: TaxiDeliveredEvent, db: Session = Depends(get_db_session)):
    logger.info(f"Delivered event received: {evt}")
    ok = crud.event_delivered(db, evt)
    logger.info(f"Delivered event processed: {ok}")
    if not ok:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"status": True}
