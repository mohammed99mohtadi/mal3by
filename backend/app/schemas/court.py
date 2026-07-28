from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.sport import SportResponse


class CourtBase(BaseModel):
    sport_id: int
    name_en: str = Field(..., min_length=2, max_length=150)
    name_ar: str = Field(..., min_length=2, max_length=150)
    description_en: str | None = None
    description_ar: str | None = None
    area: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=2, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    price_per_hour: Decimal = Field(..., gt=0)
    currency: str = Field(default="KWD", min_length=1, max_length=10)
    capacity: int = Field(..., gt=0)
    image_url: str | None = None
    is_active: bool = True

    @field_validator("price_per_hour")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price per hour must be greater than 0")
        return v

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Capacity must be greater than 0")
        return v


class CourtCreate(CourtBase):
    pass


class CourtUpdate(BaseModel):
    sport_id: int | None = None
    name_en: str | None = Field(default=None, min_length=2, max_length=150)
    name_ar: str | None = Field(default=None, min_length=2, max_length=150)
    description_en: str | None = None
    description_ar: str | None = None
    area: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, min_length=2, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    price_per_hour: Decimal | None = None
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    capacity: int | None = None
    image_url: str | None = None
    is_active: bool | None = None

    @field_validator("price_per_hour")
    @classmethod
    def validate_price_opt(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Price per hour must be greater than 0")
        return v

    @field_validator("capacity")
    @classmethod
    def validate_capacity_opt(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("Capacity must be greater than 0")
        return v


class CourtResponse(CourtBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    sport: SportResponse | None = None

    model_config = ConfigDict(from_attributes=True)
