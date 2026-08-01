from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.booking import BookingHoldCreate
from app.services import booking_service


class _FakeSession:
    def __init__(self, error: IntegrityError):
        self.error = error
        self.rollback_called = False

    def execute(self, _statement):
        return SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(id=1))

    def add(self, _booking):
        return None

    def commit(self):
        raise self.error

    def rollback(self):
        self.rollback_called = True

    def refresh(self, _booking):
        return None


def _integrity_error(constraint_name: str) -> IntegrityError:
    original = RuntimeError("raw database error")
    original.diag = SimpleNamespace(constraint_name=constraint_name)
    return IntegrityError("INSERT INTO bookings ...", {}, original)


def _hold_input() -> BookingHoldCreate:
    start = datetime.now(timezone.utc) + timedelta(days=2)
    return BookingHoldCreate(court_id=1, start_time=start, end_time=start + timedelta(hours=1))


def _patch_hold_dependencies(monkeypatch):
    monkeypatch.setattr(booking_service, "expire_outdated_holds", lambda _db: 0)
    monkeypatch.setattr(booking_service, "validate_requested_booking_time", lambda **_kwargs: None)
    monkeypatch.setattr(
        booking_service,
        "calculate_booking_price",
        lambda *_args: SimpleNamespace(
            total=Decimal("10.000"),
            base_price_per_hour=Decimal("10.000"),
            currency="KWD",
            model_dump=lambda **_kwargs: {},
        ),
    )


def test_booking_overlap_constraint_maps_to_safe_conflict(monkeypatch):
    _patch_hold_dependencies(monkeypatch)
    db = _FakeSession(_integrity_error(booking_service.BOOKING_ACTIVE_TIME_OVERLAP_CONSTRAINT))

    with pytest.raises(HTTPException) as exc_info:
        booking_service.create_booking_hold(db, 7, _hold_input())

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == booking_service.BOOKING_OVERLAP_DETAIL
    assert "constraint" not in exc_info.value.detail.lower()
    assert "database" not in exc_info.value.detail.lower()
    assert db.rollback_called is True


def test_other_integrity_error_is_not_misclassified_as_overlap(monkeypatch):
    _patch_hold_dependencies(monkeypatch)
    db = _FakeSession(_integrity_error("some_other_constraint"))

    with pytest.raises(HTTPException) as exc_info:
        booking_service.create_booking_hold(db, 7, _hold_input())

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Failed to create booking hold"
    assert db.rollback_called is True
