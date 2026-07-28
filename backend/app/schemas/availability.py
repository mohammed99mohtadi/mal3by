from datetime import date, datetime, time, timezone

from decimal import Decimal
import zoneinfo
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.availability import CourtClosureType


class CourtAvailabilityRuleBase(BaseModel):
    minimum_booking_minutes: int = Field(default=30, ge=30)
    maximum_booking_minutes: int = Field(default=360, ge=30)
    booking_interval_minutes: int = Field(default=30, gt=0)
    buffer_minutes: int = Field(default=0, ge=0)
    maximum_advance_booking_days: int = Field(default=30, ge=1)
    minimum_advance_booking_minutes: int = Field(default=0, ge=0)
    timezone: str = Field(default="Asia/Kuwait")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except Exception:
            raise ValueError(f"Invalid IANA timezone: '{v}'")
        return v

    def validate_max_gte_min(self) -> None:
        if self.maximum_booking_minutes < self.minimum_booking_minutes:
            raise ValueError("maximum_booking_minutes must be greater than or equal to minimum_booking_minutes")


class CourtAvailabilityRuleCreate(CourtAvailabilityRuleBase):
    pass


class CourtAvailabilityRuleUpdate(BaseModel):
    minimum_booking_minutes: int | None = Field(default=None, ge=30)
    maximum_booking_minutes: int | None = Field(default=None, ge=30)
    booking_interval_minutes: int | None = Field(default=None, gt=0)
    buffer_minutes: int | None = Field(default=None, ge=0)
    maximum_advance_booking_days: int | None = Field(default=None, ge=1)
    minimum_advance_booking_minutes: int | None = Field(default=None, ge=0)
    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone_opt(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                zoneinfo.ZoneInfo(v)
            except Exception:
                raise ValueError(f"Invalid IANA timezone: '{v}'")
        return v


class CourtAvailabilityRuleRead(CourtAvailabilityRuleBase):
    id: int
    court_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourtWorkingHoursBase(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    opens_at: time | None = None
    closes_at: time | None = None
    is_closed: bool = False

    def validate_working_hours(self) -> None:
        if not self.is_closed and (self.opens_at is None or self.closes_at is None):
            raise ValueError("opens_at and closes_at are required when is_closed is false")


class CourtWorkingHoursCreate(CourtWorkingHoursBase):
    pass


class CourtWorkingHoursUpdate(BaseModel):
    opens_at: time | None = None
    closes_at: time | None = None
    is_closed: bool | None = None


class CourtWorkingHoursRead(CourtWorkingHoursBase):
    id: int
    court_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourtClosureBase(BaseModel):
    start_time: datetime
    end_time: datetime
    reason: str | None = Field(default=None, max_length=255)
    closure_type: CourtClosureType = CourtClosureType.MANUAL

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


    def validate_times(self) -> None:
        if self.end_time <= self.start_time:
            raise ValueError("Closure end_time must be after start_time")


class CourtClosureCreate(CourtClosureBase):
    pass


class CourtClosureUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    reason: str | None = Field(default=None, max_length=255)
    closure_type: CourtClosureType | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware_opt(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("Closure start_time and end_time must be timezone-aware")
        return v


class CourtClosureRead(CourtClosureBase):
    id: int
    court_id: int
    created_by_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailableSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    total_price: Decimal | None = None
    available: bool


class CourtAvailabilityResponse(BaseModel):
    court_id: int
    local_date: date
    timezone: str
    duration_minutes: int
    slots: list[AvailableSlot]
    reason: str | None = None
