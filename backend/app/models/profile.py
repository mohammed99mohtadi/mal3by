from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            "length(trim(display_name)) BETWEEN 2 AND 100",
            name="ck_user_profiles_display_name_length",
        ),
        CheckConstraint(
            "preferred_language IS NULL OR preferred_language IN ('ar', 'en')",
            name="ck_user_profiles_preferred_language",
        ),
        CheckConstraint("avatar_url IS NULL OR length(avatar_url) <= 500", name="ck_user_profiles_avatar_url_length"),
        CheckConstraint("city IS NULL OR length(city) <= 100", name="ck_user_profiles_city_length"),
        CheckConstraint("area IS NULL OR length(area) <= 100", name="ck_user_profiles_area_length"),
        CheckConstraint("bio IS NULL OR length(bio) <= 1000", name="ck_user_profiles_bio_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    user = relationship("User", back_populates="profile")
