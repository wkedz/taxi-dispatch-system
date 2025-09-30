from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common import schemas
from dispatcher_service.app.adapters import crud
from dispatcher_service.app.api.dependencies import get_db_session

router = APIRouter()


@router.post("/register", response_model=schemas.TaxiRead, status_code=status.HTTP_201_CREATED)
def register_taxi(
    taxi_in: schemas.TaxiCreate,
    db: Session = Depends(get_db_session),
):
    taxi = crud.create_taxi(db=db, taxi_in=taxi_in)
    return schemas.TaxiRead(
        id=taxi.id,
        public_id=str(taxi.public_id),
        status=taxi.status,
        x=taxi.x,
        y=taxi.y,
    )


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
def taxi_heartbeat(evt: schemas.TaxiHeartbeat, db: Session = Depends(get_db_session)) -> None:
    taxi = crud.get_taxi_by_public_id(db, evt.taxi_public_id)
    if not taxi:
        raise HTTPException(status_code=404, detail="Taxi not found")
    crud.update_taxi_heartbeat(db, taxi, evt.timestamp)
    db.commit()


@router.post("/deregister", status_code=status.HTTP_204_NO_CONTENT)
def taxi_deregister(req: schemas.TaxiDeregister, db: Session = Depends(get_db_session)) -> None:
    ok = crud.deregister_taxi_by_public_id(db, req.taxi_public_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Taxi not found")
    db.commit()


@router.get("/count", response_model=schemas.TaxiCount)
def number_of_taxis(
    db: Session = Depends(get_db_session), status: schemas.TaxiStatus = schemas.TaxiStatus.AVAILABLE
) -> schemas.TaxiCount:
    count = crud.count_taxis(db, status=status)
    return schemas.TaxiCount(count=count, status=status)
