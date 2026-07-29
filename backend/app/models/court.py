from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Court(Base):
    __tablename__ = "courts"
    __table_args__ = (
        CheckConstraint("price_per_hour > 0", name="check_price_positive"),
        CheckConstraint("capacity > 0", name="check_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sport_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name_en: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    name_ar: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description_ar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    area: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    price_per_hour: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="KWD",
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="courts")
    sport = relationship("Sport", back_populates="courts")
    bookings = relationship("Booking", back_populates="court", cascade="all, delete-orphan")
    availability_rule = relationship("CourtAvailabilityRule", uselist=False, back_populates="court", cascade="all, delete-orphan")
    working_hours = relationship("CourtWorkingHours", back_populates="court", cascade="all, delete-orphan")
    closures = relationship("CourtClosure", back_populates="court", cascade="all, delete-orphan")
    pricing_rules = relationship("CourtPricingRule", back_populates="court", cascade="all, delete-orphan")
    date_price_overrides = relationship("CourtDatePriceOverride", back_populates="court", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="court")
    reviews = relationship("CourtReview", back_populates="court")

