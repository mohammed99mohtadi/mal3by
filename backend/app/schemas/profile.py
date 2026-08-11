from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserProfileCreateInternal(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)
    preferred_language: str | None = Field(default=None, pattern="^(ar|en)$")
    city: str | None = Field(default=None, max_length=100)
    area: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Display name must contain at least 2 characters")
        return normalized


class PreferredLanguageUpdate(BaseModel):
    preferred_language: str = Field(pattern="^(ar|en)$")

    model_config = ConfigDict(extra="forbid")


class UserProfileResponse(BaseModel):
    display_name: str
    preferred_language: str | None

    model_config = ConfigDict(from_attributes=True)
