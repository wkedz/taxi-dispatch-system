from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from common import schemas
from common.schemas import TaxiDeliveredEvent, TaxiPickupEvent
from dispatcher_service.app.domain import models
from dispatcher_service.app.domain.models import Taxi, TaxiStatus, Trip, TripStatus
from dispatcher_service.app.domain.utils import as_utc


def create_taxi(db: Session, taxi_in: schemas.TaxiCreate) -> models.Taxi:
    taxi = models.Taxi(
        x=taxi_in.x,
        y=taxi_in.y,
        callback_url=str(taxi_in.callback_url),
        status=models.TaxiStatus.AVAILABLE,
    )
    try:
        db.add(taxi)
        db.commit()
        db.refresh(taxi)
        return taxi
    except SQLAlchemyError:
        db.rollback()
        raise


def update_taxi_heartbeat(db: Session, taxi: models.Taxi, ts: datetime) -> None:
    ts_utc = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
    taxi.last_seen_at = ts_utc.astimezone(UTC)
    if taxi.status == models.TaxiStatus.OFFLINE:
        taxi.status = models.TaxiStatus.AVAILABLE
    db.add(taxi)


def deregister_taxi_by_public_id(db: Session, public_id: str) -> bool:
    taxi = get_taxi_by_public_id(db, public_id)
    if not taxi:
        return False
    mark_taxi_offline(db, taxi)
    db.add(taxi)
    return True


def sweep_offline_taxis(db: Session, ttl_sec: int) -> int:
    cutoff = datetime.now(UTC) - timedelta(seconds=ttl_sec)
    stmt = (
        update(models.Taxi)
        .where(
            models.Taxi.status.in_([models.TaxiStatus.AVAILABLE, models.TaxiStatus.BUSY]),
            (models.Taxi.last_seen_at.is_(None)) | (models.Taxi.last_seen_at < cutoff),
        )
        .values(status=models.TaxiStatus.OFFLINE)
    )
    res = db.execute(stmt)
    db.commit()
    return res.rowcount or 0


def pick_closest_available_taxi_for_update(db: Session, x: int, y: int) -> models.Taxi | None:
    distance = func.abs(models.Taxi.x - x) + func.abs(models.Taxi.y - y)
    stmt: Select = (
        select(models.Taxi)
        .where(models.Taxi.status == models.TaxiStatus.AVAILABLE)
        .order_by(distance, models.Taxi.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    return db.execute(stmt).scalars().first()


def mark_taxi_busy(db: Session, taxi: models.Taxi) -> None:
    taxi.status = models.TaxiStatus.BUSY
    db.add(taxi)


def mark_taxi_available(db: Session, taxi: models.Taxi) -> None:
    taxi.status = models.TaxiStatus.AVAILABLE
    db.add(taxi)


def mark_taxi_offline(db: Session, taxi: models.Taxi) -> None:
    taxi.status = models.TaxiStatus.OFFLINE
    db.add(taxi)


def count_taxis(db: Session, status: schemas.TaxiStatus = schemas.TaxiStatus.AVAILABLE) -> int:
    stmt: Select = select(func.count(models.Taxi.id))
    if status is not None:
        stmt = stmt.where(models.Taxi.status == status)
    count = db.execute(stmt).scalar_one()
    return count


def create_trip_requested(
    db: Session,
    order: schemas.OrderCreate,
    taxi_id: int | None,
) -> models.Trip:
    trip = models.Trip(
        user_id=order.user_id,
        taxi_id=taxi_id,
        start_x=order.start_x,
        start_y=order.start_y,
        end_x=order.end_x,
        end_y=order.end_y,
        status=models.TripStatus.REQUESTED,
    )
    db.add(trip)
    return trip


def event_pickup(db: Session, evt: TaxiPickupEvent) -> bool:
    trip = db.get(Trip, evt.trip_id)
    taxi = db.scalar(select(Taxi).where(Taxi.public_id == evt.taxi_public_id))

    if not trip or not taxi or trip.taxi_id != taxi.id:
        return False

    if trip.status not in (TripStatus.REQUESTED, TripStatus.IN_PROGRESS):
        return True

    trip.pickup_time = as_utc(evt.timestamp)
    trip.status = TripStatus.IN_PROGRESS
    trip.waiting_time_min = int(
        (trip.pickup_time - as_utc(trip.request_time)).total_seconds() // 60
    )

    db.add(trip)
    db.commit()
    return True


def event_delivered(db: Session, evt: TaxiDeliveredEvent) -> bool:
    trip = db.get(Trip, evt.trip_id)
    if not trip:
        return False

    trip.status = TripStatus.COMPLETED
    trip.dropoff_time = evt.dropoff_time

    taxi = db.get(Taxi, trip.taxi_id)
    if taxi:
        taxi.status = TaxiStatus.AVAILABLE
        taxi.x = evt.end_x
        taxi.y = evt.end_y
        db.add(taxi)

    db.add(trip)
    db.commit()
    return True


def get_trip(db: Session, trip_id: int) -> models.Trip | None:
    return db.get(Trip, trip_id)


def get_all_trips(db: Session) -> list[models.Trip]:
    stmt = select(models.Trip)
    return db.execute(stmt).scalars().all()


def get_taxi_by_public_id(db: Session, public_id: str) -> models.Taxi | None:
    return db.scalar(select(models.Taxi).where(models.Taxi.public_id == public_id))
