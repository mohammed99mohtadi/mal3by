from datetime import date, datetime, time, timezone
from decimal import Decimal
import enum

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PricingRuleType(str, enum.Enum):
    FIXED_HOURLY_PRICE = "fixed_hourly_price"
    PERCENTAGE_ADJUSTMENT = "percentage_adjustment"
    FIXED_HOURLY_ADJUSTMENT = "fixed_hourly_adjustment"


class CourtPricingRule(Base):
    __tablename__ = "court_pricing_rules"
    __table_args__ = (
        CheckConstraint("(weekday IS NULL) OR (weekday >= 0 AND weekday <= 6)", name="check_pricing_rule_weekday_valid"),
        CheckConstraint("valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from", name="check_pricing_rule_valid_date_range"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    court_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    rule_type: Mapped[PricingRuleType] = mapped_column(
        String(30),
        nullable=False,
    )

    weekday: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    starts_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    ends_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    value: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    valid_from: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    valid_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    created_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    court = relationship("Court", back_populates="pricing_rules")
    created_by = relationship("User", back_populates="created_pricing_rules")


class CourtDatePriceOverride(Base):
    __tablename__ = "court_date_price_overrides"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    court_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    local_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    starts_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    ends_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    override_type: Mapped[PricingRuleType] = mapped_column(
        String(30),
        nullable=False,
    )

    value: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    court = relationship("Court", back_populates="date_price_overrides")
    created_by = relationship("User", back_populates="created_date_overrides")
