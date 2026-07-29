import enum
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReviewStatus(str, enum.Enum):
    PUBLISHED = "published"
    HIDDEN = "hidden"
    REMOVED = "removed"


class CourtReview(Base):
    __tablename__ = "court_reviews"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_court_reviews_booking_id"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_court_reviews_rating"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id", ondelete="RESTRICT"), nullable=False, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(String(20), nullable=False, default=ReviewStatus.PUBLISHED, index=True)
    is_verified_booking: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    moderation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    court = relationship("Court", back_populates="reviews")
    booking = relationship("Booking", back_populates="review")
    reviewer = relationship("User", back_populates="court_reviews", foreign_keys=[reviewer_id])
    moderated_by = relationship("User", foreign_keys=[moderated_by_id])
    response = relationship("CourtReviewResponse", back_populates="review", uselist=False)


class CourtReviewResponse(Base):
    __tablename__ = "court_review_responses"
    __table_args__ = (UniqueConstraint("review_id", name="uq_court_review_responses_review_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("court_reviews.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review = relationship("CourtReview", back_populates="response")
    owner = relationship("User", foreign_keys=[owner_id])
