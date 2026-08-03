from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models.profile import UserProfile
from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.match import Match
from app.models.sport import Sport
from app.models.user import User, UserRole
from app.schemas.profile import UserProfileCreateInternal
from app.schemas.user import UserCreate
from app.services import auth_service


def _user(email: str = "profile@example.com") -> User:
    return User(
        full_name="Profile User",
        email=email,
        hashed_password="not-used-by-profile-tests",
        role=UserRole.PLAYER,
        is_active=True,
        is_admin=False,
    )


def test_profile_metadata_and_optional_fields(db_session):
    assert "user_profiles" in Base.metadata.tables
    columns = {column["name"]: column for column in inspect(db_session.bind).get_columns("user_profiles")}
    assert set(columns) == {
        "id", "user_id", "display_name", "avatar_url", "preferred_language",
        "city", "area", "bio", "created_at", "updated_at",
    }
    user = _user()
    user.profile = UserProfile(display_name="Profile User")
    db_session.add(user)
    db_session.commit()
    assert user.profile.avatar_url is None
    assert user.profile.preferred_language is None
    assert user.profile.city is None
    assert user.profile.area is None
    assert user.profile.bio is None


def test_profile_is_one_to_one_and_relationship_is_bidirectional(db_session):
    user = _user()
    profile = UserProfile(display_name="Display Name")
    user.profile = profile
    db_session.add(user)
    db_session.commit()
    assert profile.user is user
    assert user.profile is profile

    db_session.add(UserProfile(user_id=user.id, display_name="Duplicate"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("display_name", ["", " ", "x"])
def test_database_rejects_invalid_display_name(db_session, display_name):
    user = _user(f"{len(display_name)}-{display_name == ' '}@example.com")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserProfile(user_id=user.id, display_name=display_name))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_internal_schema_trims_name_and_rejects_ownership_input():
    profile = UserProfileCreateInternal(display_name="  Player Name  ")
    assert profile.display_name == "Player Name"
    with pytest.raises(ValidationError):
        UserProfileCreateInternal(display_name="Player Name", user_id=99)


def test_registration_creates_exactly_one_profile(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new-profile@example.com", "full_name": "  New Player  ", "password": "Password123"},
    )
    assert response.status_code == 201
    user = db_session.scalar(select(User).where(User.email == "new-profile@example.com"))
    profiles = list(db_session.scalars(select(UserProfile).where(UserProfile.user_id == user.id)))
    assert user.role == UserRole.PLAYER
    assert user.is_admin is False
    assert user.full_name == "New Player"
    assert len(profiles) == 1
    assert profiles[0].display_name == "New Player"


def test_duplicate_registration_does_not_create_another_profile(client, db_session):
    payload = {"email": "duplicate-profile@example.com", "full_name": "First Player", "password": "Password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    duplicate = client.post("/api/v1/auth/register", json={**payload, "full_name": "Second Player"})
    assert duplicate.status_code == 400
    assert len(list(db_session.scalars(select(User).where(User.email == payload["email"])))) == 1
    assert len(list(db_session.scalars(select(UserProfile)))) == 1


def test_profile_creation_failure_rolls_back_user(db_session, monkeypatch):
    class BrokenProfile:
        def __init__(self, **_kwargs):
            raise RuntimeError("profile insert preparation failed")

    monkeypatch.setattr(auth_service, "UserProfile", BrokenProfile)
    with pytest.raises(RuntimeError, match="profile insert preparation failed"):
        auth_service.register_new_user(
            db_session,
            UserCreate(email="rollback@example.com", full_name="Rollback User", password="Password123"),
        )
    assert db_session.scalar(select(User).where(User.email == "rollback@example.com")) is None
    assert db_session.scalar(select(UserProfile)) is None


def test_deleting_profile_does_not_delete_user(db_session):
    user = _user("keep-user@example.com")
    user.profile = UserProfile(display_name="Keep User")
    db_session.add(user)
    db_session.commit()
    user_id = user.id
    db_session.delete(user.profile)
    db_session.commit()
    assert db_session.get(User, user_id) is not None
    assert db_session.scalar(select(UserProfile).where(UserProfile.user_id == user_id)) is None


def test_deleting_user_deletes_only_its_dependent_profile(db_session):
    first = _user("delete-user@example.com")
    first.profile = UserProfile(display_name="Delete User")
    second = _user("other-user@example.com")
    second.profile = UserProfile(display_name="Other User")
    db_session.add_all([first, second])
    db_session.commit()
    first_profile_id, second_id = first.profile.id, second.id
    db_session.delete(first)
    db_session.commit()
    assert db_session.get(UserProfile, first_profile_id) is None
    assert db_session.get(User, second_id).profile.display_name == "Other User"


def test_deleting_profile_has_no_booking_or_match_side_effects(db_session):
    user = _user("history-user@example.com")
    user.profile = UserProfile(display_name="History User")
    sport = Sport(name_en="Football", name_ar="Football", slug="profile-history", is_active=True)
    db_session.add_all([user, sport])
    db_session.flush()
    court = Court(
        owner_id=user.id, sport_id=sport.id, name_en="History Court", name_ar="History Court",
        area="Kuwait", address="Test address", price_per_hour=Decimal("10.000"), capacity=10, is_active=True,
    )
    db_session.add(court)
    db_session.flush()
    starts = datetime.now(timezone.utc) + timedelta(days=2)
    booking = Booking(
        user_id=user.id, court_id=court.id, start_time=starts, end_time=starts + timedelta(hours=1),
        total_price=Decimal("10.000"), currency="KWD", status=BookingStatus.CONFIRMED,
    )
    db_session.add(booking)
    db_session.flush()
    match = Match(
        creator_id=user.id, court_id=court.id, booking_id=booking.id, title="History Match",
        sport_type="football", min_players=2, max_players=10,
        start_time=starts, end_time=starts + timedelta(hours=1),
    )
    db_session.add(match)
    db_session.commit()
    booking_id, match_id = booking.id, match.id
    db_session.delete(user.profile)
    db_session.commit()
    assert db_session.get(Booking, booking_id) is not None
    assert db_session.get(Match, match_id) is not None


def test_registration_ignores_client_role_and_profile_ownership(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "safe-profile@example.com", "full_name": "Safe Player", "password": "Password123",
            "role": "admin", "is_admin": True, "user_id": 999, "profile": {"user_id": 999},
        },
    )
    assert response.status_code == 201
    user = db_session.scalar(select(User).where(User.email == "safe-profile@example.com"))
    assert user.role == UserRole.PLAYER
    assert user.is_admin is False
    assert user.profile.user_id == user.id


def test_migration_declares_backfill_constraints_and_reversible_structure():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "e4f5a6b7c8d9_create_user_profiles.py"
    source = migration.read_text(encoding="utf-8")
    assert 'down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"' in source
    assert 'op.create_table(\n        "user_profiles"' in source
    assert "CASE" in source
    assert "WHEN length(trim(users.full_name)) >= 2 THEN trim(users.full_name)" in source
    assert "ELSE 'Player ' || users.id" in source
    assert "WHERE NOT EXISTS" in source
    assert 'op.create_index("ix_user_profiles_user_id"' in source
    assert 'unique=True' in source
    assert 'ondelete="CASCADE"' in source
    assert 'op.drop_table("user_profiles")' in source
    assert 'op.alter_column("users"' not in source
