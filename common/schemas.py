from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TaxiStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class TripStatus(str, Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaxiCreate(BaseModel):
    x: int = Field(..., ge=1, le=100)
    y: int = Field(..., ge=1, le=100)
    callback_url: HttpUrl


class TaxiRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: int
    public_id: UUID
    status: TaxiStatus
    x: int
    y: int


class TaxiCount(BaseModel):
    count: int
    status: TaxiStatus


class TaxiHeartbeat(BaseModel):
    taxi_public_id: UUID
    timestamp: datetime


class TaxiDeregister(BaseModel):
    taxi_public_id: UUID


class OrderCreate(BaseModel):
    user_id: int
    start_x: int = Field(..., ge=1, le=100)
    start_y: int = Field(..., ge=1, le=100)
    end_x: int = Field(..., ge=1, le=100)
    end_y: int = Field(..., ge=1, le=100)


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: int
    user_id: int
    taxi_id: int | None = None
    status: TripStatus
    request_time: datetime
    pickup_time: datetime | None = None
    dropoff_time: datetime | None = None
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    waiting_time_min: int | None = None
    travel_time_min: int | None = None
    total_distance: int | None = None
    route_meta: dict | None = None


class AssignPayload(BaseModel):
    trip_id: int
    start_x: int
    start_y: int
    end_x: int
    end_y: int


class TaxiPickupEvent(BaseModel):
    trip_id: int
    taxi_public_id: UUID
    timestamp: datetime


class TaxiDeliveredEvent(BaseModel):
    trip_id: int
    taxi_public_id: UUID
    dropoff_time: datetime
    end_x: int
    end_y: int
