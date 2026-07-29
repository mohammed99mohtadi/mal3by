from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.review import ReviewStatus


class CourtReviewCreate(BaseModel):
    booking_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class CourtReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class CourtReviewResponseCreate(BaseModel):
    response_text: str = Field(min_length=1, max_length=2000)

    @field_validator("response_text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("response_text cannot be blank")
        return value


class CourtReviewResponseUpdate(CourtReviewResponseCreate):
    pass


class ModerationRequest(BaseModel):
    moderation_reason: str | None = Field(default=None, max_length=500)


class ReviewerSummary(BaseModel):
    id: int
    full_name: str


class CourtReviewResponsePublic(BaseModel):
    id: int
    response_text: str
    created_at: datetime
    updated_at: datetime


class CourtReviewPublicResponse(BaseModel):
    id: int
    rating: int
    comment: str | None
    is_verified_booking: bool
    created_at: datetime
    updated_at: datetime
    reviewer: ReviewerSummary
    owner_response: CourtReviewResponsePublic | None = None


class CourtReviewManagementResponse(CourtReviewPublicResponse):
    status: ReviewStatus
    deleted_at: datetime | None
    moderation_reason: str | None = None
    booking_id: int
    court_id: int


class RatingDistributionResponse(BaseModel):
    one: int
    two: int
    three: int
    four: int
    five: int


class RatingSummaryResponse(BaseModel):
    average_rating: Decimal
    total_reviews: int
    verified_reviews: int
    rating_distribution: RatingDistributionResponse
