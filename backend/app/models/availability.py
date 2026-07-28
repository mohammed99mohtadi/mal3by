from datetime import datetime, time, timezone
import enum

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CourtClosureType(str, enum.Enum):
    MAINTENANCE = "maintenance"
    HOLIDAY = "holiday"
    PRIVATE_EVENT = "private_event"
    EMERGENCY = "emergency"
    MANUAL = "manual"


class CourtAvailabilityRule(Base):
    __tablename__ = "court_availability_rules"
    __table_args__ = (
        CheckConstraint("minimum_booking_minutes >= 30", name="check_min_booking_mins_gte_30"),
        CheckConstraint("maximum_booking_minutes >= minimum_booking_minutes", name="check_max_gte_min_booking_mins"),
        CheckConstraint("booking_interval_minutes > 0", name="check_interval_mins_gt_0"),
        CheckConstraint("buffer_minutes >= 0", name="check_buffer_mins_gte_0"),
        CheckConstraint("maximum_advance_booking_days >= 1", name="check_max_advance_days_gte_1"),
        CheckConstraint("minimum_advance_booking_minutes >= 0", name="check_min_advance_mins_gte_0"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    court_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    minimum_booking_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )

    maximum_booking_minutes: Mapped[int] = mapped_column(
        Integer,
        default=360,
        nullable=False,
    )

    booking_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )

    buffer_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    maximum_advance_booking_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )

    minimum_advance_booking_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Kuwait",
        nullable=False,
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
    court = relationship("Court", back_populates="availability_rule")


class CourtWorkingHours(Base):
    __tablename__ = "court_working_hours"
    __table_args__ = (
        UniqueConstraint("court_id", "weekday", name="uq_court_working_hours_weekday"),
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="check_working_hours_weekday_range"),
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

    weekday: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    opens_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    closes_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    court = relationship("Court", back_populates="working_hours")


class CourtClosure(Base):
    __tablename__ = "court_closures"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="check_court_closure_end_after_start"),
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

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    closure_type: Mapped[CourtClosureType] = mapped_column(
        String(50),
        default=CourtClosureType.MANUAL,
        nullable=False,
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
    court = relationship("Court", back_populates="closures")
    created_by = relationship("User")
