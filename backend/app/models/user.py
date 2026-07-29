from datetime import datetime, timezone
import enum

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    PLAYER = "player"
    OWNER = "owner"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )

    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.PLAYER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    courts = relationship("Court", back_populates="owner", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    created_pricing_rules = relationship("CourtPricingRule", back_populates="created_by")
    created_date_overrides = relationship("CourtDatePriceOverride", back_populates="created_by")
    created_matches = relationship("Match", back_populates="creator", foreign_keys="Match.creator_id")
    match_participations = relationship("MatchParticipant", back_populates="user")
    court_reviews = relationship("CourtReview", back_populates="reviewer", foreign_keys="CourtReview.reviewer_id")
