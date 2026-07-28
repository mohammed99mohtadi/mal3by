from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.pricing import PricingRuleType


class CourtPricingRuleBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(default=None, max_length=255)
    rule_type: PricingRuleType
    weekday: int | None = Field(default=None, ge=0, le=6)
    starts_at: time | None = None
    ends_at: time | None = None
    value: Decimal
    priority: int = Field(default=0, ge=-1000, le=10000)
    is_active: bool = True
    valid_from: date | None = None
    valid_until: date | None = None

    @model_validator(mode="after")
    def validate_pricing_rule_data(self) -> "CourtPricingRuleBase":
        # Time range consistency: either both set or both None
        if (self.starts_at is None) != (self.ends_at is None):
            raise ValueError("starts_at and ends_at must both be provided or both be null")

        # Validity date range
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot be earlier than valid_from")

        # Value bounds by rule type
        if self.rule_type == PricingRuleType.FIXED_HOURLY_PRICE:
            if self.value < Decimal("0"):
                raise ValueError("fixed_hourly_price value must be greater than or equal to 0")
        elif self.rule_type == PricingRuleType.PERCENTAGE_ADJUSTMENT:
            if self.value < Decimal("-90.0") or self.value > Decimal("500.0"):
                raise ValueError("percentage_adjustment value must be between -90% and +500%")
        elif self.rule_type == PricingRuleType.FIXED_HOURLY_ADJUSTMENT:
            if self.value < Decimal("-1000.0") or self.value > Decimal("1000.0"):
                raise ValueError("fixed_hourly_adjustment value must be between -1000 and +1000")

        return self


class CourtPricingRuleCreate(CourtPricingRuleBase):
    pass


class CourtPricingRuleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    rule_type: PricingRuleType | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    starts_at: time | None = None
    ends_at: time | None = None
    value: Decimal | None = None
    priority: int | None = Field(default=None, ge=-1000, le=10000)
    is_active: bool | None = None
    valid_from: date | None = None
    valid_until: date | None = None


class CourtPricingRuleRead(CourtPricingRuleBase):
    id: int
    court_id: int
    created_by_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourtDatePriceOverrideBase(BaseModel):
    name: str = Field(..., max_length=100)
    local_date: date
    starts_at: time | None = None
    ends_at: time | None = None
    override_type: PricingRuleType
    value: Decimal
    priority: int = Field(default=100, ge=-1000, le=10000)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_override_data(self) -> "CourtDatePriceOverrideBase":
        if (self.starts_at is None) != (self.ends_at is None):
            raise ValueError("starts_at and ends_at must both be provided or both be null")

        if self.override_type == PricingRuleType.FIXED_HOURLY_PRICE:
            if self.value < Decimal("0"):
                raise ValueError("fixed_hourly_price value must be greater than or equal to 0")
        elif self.override_type == PricingRuleType.PERCENTAGE_ADJUSTMENT:
            if self.value < Decimal("-90.0") or self.value > Decimal("500.0"):
                raise ValueError("percentage_adjustment value must be between -90% and +500%")
        elif self.override_type == PricingRuleType.FIXED_HOURLY_ADJUSTMENT:
            if self.value < Decimal("-1000.0") or self.value > Decimal("1000.0"):
                raise ValueError("fixed_hourly_adjustment value must be between -1000 and +1000")

        return self


class CourtDatePriceOverrideCreate(CourtDatePriceOverrideBase):
    pass


class CourtDatePriceOverrideUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    local_date: date | None = None
    starts_at: time | None = None
    ends_at: time | None = None
    override_type: PricingRuleType | None = None
    value: Decimal | None = None
    priority: int | None = Field(default=None, ge=-1000, le=10000)
    is_active: bool | None = None


class CourtDatePriceOverrideRead(CourtDatePriceOverrideBase):
    id: int
    court_id: int
    created_by_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppliedPricingRule(BaseModel):
    rule_id: int | None = None
    override_id: int | None = None
    name: str
    rule_type: PricingRuleType
    value: Decimal
    priority: int


class PriceSegment(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    hourly_rate: Decimal
    subtotal: Decimal
    applied_rules: list[AppliedPricingRule] = []


class PriceBreakdown(BaseModel):
    currency: str = "KWD"
    base_price_per_hour: Decimal
    segments: list[PriceSegment]
    subtotal: Decimal
    total: Decimal


class BookingPriceQuoteRequest(BaseModel):
    start_time: datetime
    end_time: datetime

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_time and end_time must be timezone-aware")
        return v

    @model_validator(mode="after")
    def validate_end_after_start(self) -> "BookingPriceQuoteRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingPriceQuoteResponse(BaseModel):
    court_id: int
    start_time: datetime
    end_time: datetime
    court_timezone: str
    currency: str = "KWD"
    base_price_per_hour: Decimal
    segments: list[PriceSegment]
    subtotal: Decimal
    total: Decimal
    available: bool
    disclaimer: str = "Price quote is informational and does not guarantee slot availability."
