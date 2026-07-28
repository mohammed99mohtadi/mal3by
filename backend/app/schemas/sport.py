from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SportBase(BaseModel):
    name_en: str = Field(..., min_length=2, max_length=100)
    name_ar: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    icon: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class SportCreate(SportBase):
    pass


class SportUpdate(BaseModel):
    name_en: str | None = Field(default=None, min_length=2, max_length=100)
    name_ar: str | None = Field(default=None, min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    icon: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class SportResponse(SportBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
