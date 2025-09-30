from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from common.schemas import TaxiRead, TripRead
from dispatcher_service.app.api.dependencies import get_db_session
from dispatcher_service.app.domain.models import Taxi, Trip

router = APIRouter()


@router.get("/taxis", response_model=list[TaxiRead])
def list_taxis(db: Session = Depends(get_db_session)) -> list[Taxi]:
    return db.execute(select(Taxi).order_by(Taxi.id.asc())).scalars().all()


@router.get("/trips", response_model=list[TripRead])
def list_trips(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db_session),
) -> list[Trip]:
    stmt = select(Trip).order_by(desc(Trip.id)).limit(limit)
    return db.execute(stmt).scalars().all()
