import enum
import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import JSON, UUID, CheckConstraint, DateTime, ForeignKey
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaxiStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class TripStatus(str, enum.Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Taxi(Base):
    __tablename__ = "taxis"
    __table_args__ = (
        CheckConstraint("x BETWEEN 1 AND 100", name="ck_taxis_x_range"),
        CheckConstraint("y BETWEEN 1 AND 100", name="ck_taxis_y_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)  # internal PK
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    status: Mapped[TaxiStatus] = mapped_column(
        SQLAlchemyEnum(TaxiStatus), default=TaxiStatus.AVAILABLE, nullable=False
    )
    x: Mapped[int] = mapped_column(nullable=False)
    y: Mapped[int] = mapped_column(nullable=False)
    callback_url: Mapped[str] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    trips: Mapped[list["Trip"]] = relationship(back_populates="taxi")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(nullable=False)
    taxi_id: Mapped[int | None] = mapped_column(ForeignKey("taxis.id"), nullable=True)
    start_x: Mapped[int] = mapped_column(nullable=False)
    start_y: Mapped[int] = mapped_column(nullable=False)
    end_x: Mapped[int] = mapped_column(nullable=False)
    end_y: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[TripStatus] = mapped_column(
        SQLAlchemyEnum(TripStatus), default=TripStatus.REQUESTED, nullable=False
    )
    request_time: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    pickup_time: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    dropoff_time: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    waiting_time_min: Mapped[int | None] = mapped_column(nullable=True, default=None)
    travel_time_min: Mapped[int | None] = mapped_column(nullable=True, default=None)
    total_distance: Mapped[int | None] = mapped_column(nullable=True, default=None)
    route_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    taxi: Mapped[Optional["Taxi"]] = relationship(back_populates="trips")
