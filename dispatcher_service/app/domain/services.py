from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from common.schemas import AssignPayload, OrderCreate
from dispatcher_service.app.adapters import crud
from dispatcher_service.app.adapters.http_client import post_json
from dispatcher_service.app.domain import models
from dispatcher_service.app.settings import settings


def _create_trip_and_reserve_taxi(
    db: Session, order: OrderCreate
) -> tuple[models.Trip, models.Taxi] | None:
    try:
        taxi = crud.pick_closest_available_taxi_for_update(db, order.start_x, order.start_y)
        if taxi is None:
            return None
        crud.mark_taxi_busy(db, taxi)
        trip = crud.create_trip_requested(db, order, taxi_id=taxi.id)
        db.commit()
        db.refresh(trip)
        db.refresh(taxi)
        return trip, taxi
    except SQLAlchemyError:
        db.rollback()
        raise


async def _notify_taxi_assignment(taxi: models.Taxi, trip: models.Trip, order: OrderCreate) -> bool:
    payload = AssignPayload(
        trip_id=trip.id,
        start_x=order.start_x,
        start_y=order.start_y,
        end_x=order.end_x,
        end_y=order.end_y,
    ).model_dump()

    for _ in range(max(1, settings.ASSIGN_RETRIES)):
        try:
            resp = await post_json(taxi.callback_url, payload)  # type: ignore[arg-type]
            if 200 <= resp.status_code < 300:
                return True
        except Exception:
            pass
    return False


def _compensate_failed_assignment(db: Session, trip: models.Trip, taxi: models.Taxi) -> None:
    try:
        trip.status = models.TripStatus.CANCELLED
        crud.mark_taxi_available(db, taxi)
        db.add(trip)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        # best-effort


async def assign_order(db: Session, order: OrderCreate) -> models.Trip | None:
    reserved = _create_trip_and_reserve_taxi(db, order)
    if not reserved:
        return None

    trip, taxi = reserved
    success = await _notify_taxi_assignment(taxi, trip, order)
    if success:
        return trip

    _compensate_failed_assignment(db, trip, taxi)
    return None
