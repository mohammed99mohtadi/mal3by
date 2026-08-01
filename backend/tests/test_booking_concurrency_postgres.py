"""Opt-in PostgreSQL tests for the booking exclusion constraint.

Run only against an explicitly disposable database whose name contains "test":
MAL3BY_RUN_POSTGRES_TESTS=1 and MAL3BY_TEST_POSTGRES_URL=<isolated URL>.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


POSTGRES_URL = os.getenv("MAL3BY_TEST_POSTGRES_URL")
POSTGRES_ENABLED = os.getenv("MAL3BY_RUN_POSTGRES_TESTS") == "1"
CONSTRAINT_NAME = "excl_bookings_active_court_time_overlap"
ACTIVE_STATUSES = ("pending", "pending_payment", "confirmed")

pytestmark = pytest.mark.skipif(
    not POSTGRES_ENABLED or not POSTGRES_URL,
    reason="requires explicitly confirmed isolated PostgreSQL test database",
)


@pytest.fixture(scope="module")
def postgres_engine():
    url = make_url(POSTGRES_URL)
    if url.get_backend_name() != "postgresql" or "test" not in (url.database or "").lower():
        pytest.fail("PostgreSQL tests require a disposable database with 'test' in its name")

    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", POSTGRES_URL.replace("%", "%%"))
    command.upgrade(config, "head")

    engine = create_engine(POSTGRES_URL)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def booking_domain(postgres_engine):
    suffix = uuid4().hex
    now = datetime.now(timezone.utc)
    with postgres_engine.begin() as connection:
        owner_id = connection.execute(
            text(
                "INSERT INTO users (full_name, email, hashed_password, role, is_active, is_admin, created_at) "
                "VALUES ('Owner', :email, 'unused', 'owner', true, false, :now) RETURNING id"
            ),
            {"email": f"owner-{suffix}@example.test", "now": now},
        ).scalar_one()
        user_ids = []
        for number in (1, 2):
            user_ids.append(
                connection.execute(
                    text(
                        "INSERT INTO users (full_name, email, hashed_password, role, is_active, is_admin, created_at) "
                        "VALUES ('Player', :email, 'unused', 'player', true, false, :now) RETURNING id"
                    ),
                    {"email": f"player-{number}-{suffix}@example.test", "now": now},
                ).scalar_one()
            )
        sport_id = connection.execute(
            text(
                "INSERT INTO sports (name_en, name_ar, slug, is_active, created_at) "
                "VALUES ('Test', 'Test', :slug, true, :now) RETURNING id"
            ),
            {"slug": f"test-{suffix}", "now": now},
        ).scalar_one()
        court_ids = []
        for number in (1, 2):
            court_ids.append(
                connection.execute(
                    text(
                        "INSERT INTO courts "
                        "(owner_id, sport_id, name_en, name_ar, area, address, price_per_hour, currency, capacity, is_active, created_at, updated_at) "
                        "VALUES (:owner, :sport, :name, :name, 'Test', 'Test', 10, 'KWD', 4, true, :now, :now) RETURNING id"
                    ),
                    {"owner": owner_id, "sport": sport_id, "name": f"Court {number} {suffix}", "now": now},
                ).scalar_one()
            )

    domain = SimpleDomain(owner_id, user_ids, sport_id, court_ids)
    try:
        yield domain
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(text("DELETE FROM bookings WHERE court_id = ANY(:court_ids)"), {"court_ids": court_ids})
            connection.execute(text("DELETE FROM courts WHERE id = ANY(:court_ids)"), {"court_ids": court_ids})
            connection.execute(text("DELETE FROM sports WHERE id = :sport_id"), {"sport_id": sport_id})
            connection.execute(text("DELETE FROM users WHERE id = ANY(:user_ids)"), {"user_ids": [owner_id, *user_ids]})


class SimpleDomain:
    def __init__(self, owner_id, user_ids, sport_id, court_ids):
        self.owner_id = owner_id
        self.user_ids = user_ids
        self.sport_id = sport_id
        self.court_ids = court_ids


def _insert_booking(connection, user_id, court_id, start, end, booking_status):
    return connection.execute(
        text(
            "INSERT INTO bookings "
            "(user_id, court_id, start_time, end_time, total_price, currency, status, status_updated_at, created_at, updated_at) "
            "VALUES (:user_id, :court_id, :start, :end, 10, 'KWD', :status, now(), now(), now()) RETURNING id"
        ),
        {"user_id": user_id, "court_id": court_id, "start": start, "end": end, "status": booking_status},
    ).scalar_one()


def _future_interval():
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=10)
    return start, start + timedelta(hours=1)


@pytest.mark.parametrize("active_status", ACTIVE_STATUSES)
def test_active_booking_blocks_overlap(postgres_engine, booking_domain, active_status):
    start, end = _future_interval()
    with postgres_engine.begin() as connection:
        _insert_booking(connection, booking_domain.user_ids[0], booking_domain.court_ids[0], start, end, active_status)
    with pytest.raises(IntegrityError) as exc_info:
        with postgres_engine.begin() as connection:
            _insert_booking(
                connection,
                booking_domain.user_ids[1],
                booking_domain.court_ids[0],
                start + timedelta(minutes=15),
                end,
                "pending_payment",
            )
    assert exc_info.value.orig.diag.constraint_name == CONSTRAINT_NAME


@pytest.mark.parametrize("inactive_status", ("cancelled", "expired", "rejected", "refunded", "completed"))
def test_inactive_booking_does_not_block(postgres_engine, booking_domain, inactive_status):
    start, end = _future_interval()
    with postgres_engine.begin() as connection:
        _insert_booking(connection, booking_domain.user_ids[0], booking_domain.court_ids[0], start, end, inactive_status)
        _insert_booking(connection, booking_domain.user_ids[1], booking_domain.court_ids[0], start, end, "pending_payment")


def test_same_interval_on_different_courts_succeeds(postgres_engine, booking_domain):
    start, end = _future_interval()
    with postgres_engine.begin() as connection:
        _insert_booking(connection, booking_domain.user_ids[0], booking_domain.court_ids[0], start, end, "confirmed")
        _insert_booking(connection, booking_domain.user_ids[1], booking_domain.court_ids[1], start, end, "pending_payment")


def test_adjacent_interval_succeeds(postgres_engine, booking_domain):
    start, end = _future_interval()
    with postgres_engine.begin() as connection:
        _insert_booking(connection, booking_domain.user_ids[0], booking_domain.court_ids[0], start, end, "confirmed")
        _insert_booking(
            connection,
            booking_domain.user_ids[1],
            booking_domain.court_ids[0],
            end,
            end + timedelta(hours=1),
            "pending_payment",
        )


def test_concurrent_overlapping_holds_allow_one_commit(postgres_engine, booking_domain):
    start, end = _future_interval()
    barrier = Barrier(2)

    def attempt(user_id):
        connection = postgres_engine.connect()
        transaction = connection.begin()
        try:
            available = connection.execute(
                text(
                    "SELECT NOT EXISTS (SELECT 1 FROM bookings WHERE court_id = :court_id "
                    "AND status IN ('pending', 'pending_payment', 'confirmed') "
                    "AND tstzrange(start_time, end_time, '[)') && tstzrange(:start, :end, '[)'))"
                ),
                {"court_id": booking_domain.court_ids[0], "start": start, "end": end},
            ).scalar_one()
            barrier.wait(timeout=10)
            assert available is True
            _insert_booking(connection, user_id, booking_domain.court_ids[0], start, end, "pending_payment")
            transaction.commit()
            return "committed"
        except IntegrityError as exc:
            transaction.rollback()
            return exc.orig.diag.constraint_name
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, booking_domain.user_ids))

    assert sorted(results) == [CONSTRAINT_NAME, "committed"]
    with postgres_engine.connect() as connection:
        active_count = connection.execute(
            text(
                "SELECT count(*) FROM bookings WHERE court_id = :court_id "
                "AND status IN ('pending', 'pending_payment', 'confirmed')"
            ),
            {"court_id": booking_domain.court_ids[0]},
        ).scalar_one()
    assert active_count == 1
