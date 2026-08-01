from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.booking import BookingStatus
from app.schemas.court import CourtResponse


class BookingCreate(BaseModel):
    court_id: int
    start_time: datetime
    end_time: datetime

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_time must be timezone-aware")
        now = datetime.now(timezone.utc)
        if v < now:
            raise ValueError("start_time cannot be in the past")
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("end_time must be timezone-aware")
        return v

    def validate_duration_and_times(self) -> None:
        """Helper validation for duration and sequence."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        duration = self.end_time - self.start_time
        if duration < timedelta(minutes=30):
            raise ValueError("Booking duration must be at least 30 minutes")
        if duration > timedelta(hours=6):
            raise ValueError("Booking duration must not exceed 6 hours")


class BookingHoldCreate(BookingCreate):
    hold_minutes: int | None = Field(default=10, ge=1, le=60)


class BookingCancel(BaseModel):
    cancellation_reason: str | None = Field(default=None, max_length=255)


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    cancellation_reason: str | None = Field(default=None, max_length=255)


class BookingHoldStatusResponse(BaseModel):
    booking_id: int
    status: BookingStatus
    hold_expires_at: datetime | None = None
    is_expired: bool
    seconds_remaining: int


class BookingRead(BaseModel):
    id: int
    user_id: int
    court_id: int
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    base_price_per_hour: Decimal | None = None
    currency: str = "KWD"
    pricing_breakdown: dict | None = None
    pricing_calculated_at: datetime | None = None
    status: BookingStatus

    hold_expires_at: datetime | None = None
    confirmed_at: datetime | None = None
    expired_at: datetime | None = None
    completed_at: datetime | None = None
    refunded_at: datetime | None = None
    status_updated_at: datetime | None = None

    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    court: CourtResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingListItem(BookingRead):
    pass
