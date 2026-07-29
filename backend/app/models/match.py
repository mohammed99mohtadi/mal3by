import enum
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MatchVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class MatchJoinPolicy(str, enum.Enum):
    OPEN = "open"
    APPROVAL_REQUIRED = "approval_required"


class MatchStatus(str, enum.Enum):
    OPEN = "open"
    FULL = "full"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ParticipantStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    LEFT = "left"


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_matches_booking_id"),
        CheckConstraint("min_players >= 2", name="ck_matches_min_players"),
        CheckConstraint("max_players >= min_players", name="ck_matches_player_range"),
        CheckConstraint("max_players <= 100", name="ck_matches_max_players"),
        CheckConstraint("end_time > start_time", name="ck_matches_end_after_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id", ondelete="RESTRICT"), nullable=False, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sport_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    visibility: Mapped[MatchVisibility] = mapped_column(String(20), nullable=False, default=MatchVisibility.PUBLIC, index=True)
    join_policy: Mapped[MatchJoinPolicy] = mapped_column(String(30), nullable=False, default=MatchJoinPolicy.OPEN)
    status: Mapped[MatchStatus] = mapped_column(String(20), nullable=False, default=MatchStatus.OPEN, index=True)
    skill_level: Mapped[SkillLevel] = mapped_column(String(20), nullable=False, default=SkillLevel.ALL_LEVELS, index=True)
    min_players: Mapped[int] = mapped_column(Integer, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invite_code: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", back_populates="created_matches", foreign_keys=[creator_id])
    court = relationship("Court", back_populates="matches")
    booking = relationship("Booking", back_populates="match")
    participants = relationship("MatchParticipant", back_populates="match")


class MatchParticipant(Base):
    __tablename__ = "match_participants"
    __table_args__ = (UniqueConstraint("match_id", "user_id", name="uq_match_participants_match_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[ParticipantStatus] = mapped_column(String(20), nullable=False, index=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    match = relationship("Match", back_populates="participants")
    user = relationship("User", back_populates="match_participations")
