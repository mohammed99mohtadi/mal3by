from datetime import datetime, timedelta, timezone
from decimal import Decimal
import time
import pytest
from fastapi import status

from app.models.booking import BookingStatus
from app.models.user import UserRole
from app.models.court import Court
from app.models.sport import Sport


def register_user(client, db_session, email: str, role: UserRole = UserRole.PLAYER) -> tuple[int, str]:
    payload = {
        "email": email,
        "full_name": "Test User",
        "password": "Password123",
    }
    reg_resp = client.post("/api/v1/auth/register", json=payload)
    user_id = reg_resp.json()["id"]

    if role != UserRole.PLAYER:
        from app.models.user import User
        user = db_session.query(User).filter(User.id == user_id).first()
        user.role = role
        user.is_admin = (role == UserRole.ADMIN)
        db_session.commit()

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    token = login_resp.json()["access_token"]
    return user_id, token


def create_court(client, db_session, token: str, price_per_hour: float = 10.0) -> int:
    headers = {"Authorization": f"Bearer {token}"}

    sport = db_session.query(Sport).first()
    if not sport:
        sport = Sport(name_en="Padel", name_ar="بادل", slug="padel")
        db_session.add(sport)
        db_session.commit()
        db_session.refresh(sport)

    court_payload = {
        "sport_id": sport.id,
        "name_en": "Lifecycle Court",
        "name_ar": "ملعب الحجز",
        "area": "Salmiya",
        "address": "Block 5",
        "price_per_hour": price_per_hour,
        "capacity": 4,
    }
    resp = client.post("/api/v1/courts", json=court_payload, headers=headers)
    return resp.json()["id"]


def get_aligned_future_datetime(days_offset: int = 5, hour: int = 10, minute: int = 0) -> datetime:
    now_utc = datetime.now(timezone.utc)
    base = now_utc + timedelta(days=days_offset)
    tz_offset = timedelta(hours=3)
    local_base = (base + tz_offset).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return (local_base - tz_offset).astimezone(timezone.utc)


# 1. Creating a valid temporary hold
def test_create_valid_temporary_hold(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l1@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l1@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    h_user = {"Authorization": f"Bearer {user_token}"}
    payload = {"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat(), "hold_minutes": 10}
    r = client.post("/api/v1/bookings/hold", json=payload, headers=h_user)
    assert r.status_code == status.HTTP_201_CREATED
    data = r.json()
    assert data["status"] == BookingStatus.PENDING_PAYMENT
    assert data["hold_expires_at"] is not None


# 2. Active hold blocks another booking
def test_active_hold_blocks_another_booking(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l2@example.com", UserRole.ADMIN)
    _, u1_token = register_user(client, db_session, "u1_l2@example.com", UserRole.PLAYER)
    _, u2_token = register_user(client, db_session, "u2_l2@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    # User 1 holds slot
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED

    # User 2 tries to book overlapping slot -> 409
    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_409_CONFLICT


# 3. Expired hold does not block availability
def test_expired_hold_unblocks_availability(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l3@example.com", UserRole.ADMIN)
    _, u1_token = register_user(client, db_session, "u1_l3@example.com", UserRole.PLAYER)
    _, u2_token = register_user(client, db_session, "u2_l3@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    # User 1 creates hold
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()}, headers=h1)
    b_id = r1.json()["id"]

    # Manually expire hold in DB
    from app.models.booking import Booking
    b = db_session.query(Booking).filter(Booking.id == b_id).first()
    b.hold_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    # User 2 books slot -> 201 Created
    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_201_CREATED


# 4. User cannot cancel another user's hold
def test_user_cannot_cancel_other_user_hold(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l4@example.com", UserRole.ADMIN)
    _, u1_token = register_user(client, db_session, "u1_l4@example.com", UserRole.PLAYER)
    _, u2_token = register_user(client, db_session, "u2_l4@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h1)
    b_id = r1.json()["id"]

    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post(f"/api/v1/bookings/{b_id}/cancel-hold", headers=h2)
    assert r2.status_code == status.HTTP_403_FORBIDDEN


# 5. Hold expiry timestamp is correct
def test_hold_expiry_timestamp_correct(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l5@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l5@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    now_utc = datetime.now(timezone.utc)
    r = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat(), "hold_minutes": 15}, headers=h_user)

    exp_raw = r.json()["hold_expires_at"]
    exp_dt = datetime.fromisoformat(exp_raw.replace("Z", "+00:00"))
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
    diff_secs = (exp_dt - now_utc).total_seconds()

    assert 850 <= diff_secs <= 950  # ~15 minutes (900 seconds)


# 6. Pricing snapshot stored on hold creation
def test_pricing_snapshot_stored_on_hold(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l6@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l6@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token, price_per_hour=12.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)

    data = r.json()
    assert float(data["total_price"]) == 12.0
    assert float(data["base_price_per_hour"]) == 12.0
    assert data["pricing_breakdown"] is not None


# 7. pending_payment to confirmed succeeds
def test_pending_payment_to_confirmed_succeeds(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l7@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l7@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    # User confirms payment
    r_conf = client.post(f"/api/v1/bookings/{b_id}/confirm-payment", headers=h_user)
    assert r_conf.status_code == status.HTTP_200_OK
    assert r_conf.json()["status"] == BookingStatus.CONFIRMED
    assert r_conf.json()["confirmed_at"] is not None


# 8. pending_payment to cancelled succeeds
def test_pending_payment_to_cancelled_succeeds(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l8@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l8@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    r_cancel = client.post(f"/api/v1/bookings/{b_id}/cancel-hold", headers=h_user)
    assert r_cancel.status_code == status.HTTP_200_OK
    assert r_cancel.json()["status"] == BookingStatus.CANCELLED


# 9. pending_payment to expired succeeds
def test_pending_payment_to_expired(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l9@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l9@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    # Trigger cleanup endpoint after expiration
    from app.models.booking import Booking
    b = db_session.query(Booking).filter(Booking.id == b_id).first()
    b.hold_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.commit()

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    r_clean = client.post(
        "/api/v1/bookings/cleanup-expired-holds",
        headers=admin_headers,
    )
    assert r_clean.status_code == status.HTTP_200_OK
    assert r_clean.json()["expired_count"] >= 1

    r_get = client.get(f"/api/v1/bookings/{b_id}", headers=h_user)
    assert r_get.json()["status"] == BookingStatus.EXPIRED


def test_cleanup_expired_holds_requires_admin(client, db_session):
    _, user_token = register_user(
        client,
        db_session,
        "cleanup_player@example.com",
        UserRole.PLAYER,
    )

    response = client.post(
        "/api/v1/bookings/cleanup-expired-holds",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_cleanup_expired_holds_requires_authentication(client):
    response = client.post("/api/v1/bookings/cleanup-expired-holds")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# 10. expired to confirmed fails
def test_expired_to_confirmed_fails(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l10@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l10@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    # Set expired
    from app.models.booking import Booking
    b = db_session.query(Booking).filter(Booking.id == b_id).first()
    b.status = BookingStatus.EXPIRED
    db_session.commit()

    r_conf = client.post(f"/api/v1/bookings/{b_id}/confirm-payment", headers=h_user)
    assert r_conf.status_code == status.HTTP_400_BAD_REQUEST


# 11. cancelled to confirmed fails
def test_cancelled_to_confirmed_fails(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l11@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l11@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    client.post(f"/api/v1/bookings/{b_id}/cancel-hold", headers=h_user)

    r_conf = client.post(f"/api/v1/bookings/{b_id}/confirm-payment", headers=h_user)
    assert r_conf.status_code == status.HTTP_400_BAD_REQUEST


# 12. Client cannot set arbitrary booking status
def test_player_cannot_set_arbitrary_status(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l12@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l12@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    # Player tries to PATCH status -> 403 Forbidden
    r_patch = client.patch(f"/api/v1/bookings/{b_id}/status", json={"status": "confirmed"}, headers=h_user)
    assert r_patch.status_code == status.HTTP_403_FORBIDDEN


# 13. Existing confirmed booking behaviour remains unchanged
def test_confirmed_booking_blocks_availability(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l13@example.com", UserRole.ADMIN)
    _, u1_token = register_user(client, db_session, "u1_l13@example.com", UserRole.PLAYER)
    _, u2_token = register_user(client, db_session, "u2_l13@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()}, headers=h1)
    b_id = r1.json()["id"]
    client.post(f"/api/v1/bookings/{b_id}/confirm-payment", headers=h1)

    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_409_CONFLICT


# 14 & 15. Available slots account for active holds and ignore expired holds
def test_available_slots_accounts_for_active_and_expired_holds(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_l14@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_l14@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    tz_offset = timedelta(hours=3)
    target_dt = get_aligned_future_datetime(days_offset=6, hour=10, minute=0)
    target_date = (target_dt + tz_offset).date().isoformat()

    h_user = {"Authorization": f"Bearer {user_token}"}
    r_hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": target_dt.isoformat(), "end_time": (target_dt + timedelta(hours=1)).isoformat()}, headers=h_user)
    b_id = r_hold.json()["id"]

    # Active hold: slot is unavailable (available=False)
    r_slots1 = client.get(f"/api/v1/courts/{court_id}/available-slots?date={target_date}&duration_minutes=60")
    slots1 = r_slots1.json()["slots"]
    match_slot1 = next((s for s in slots1 if s["start_time"] == target_dt.isoformat().replace("+00:00", "Z")), None)
    assert match_slot1 is not None
    assert match_slot1["available"] is False

    # Expire hold: slot becomes available (available=True)
    from app.models.booking import Booking
    b = db_session.query(Booking).filter(Booking.id == b_id).first()
    b.hold_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    r_slots2 = client.get(f"/api/v1/courts/{court_id}/available-slots?date={target_date}&duration_minutes=60")
    slots2 = r_slots2.json()["slots"]
    match_slot2 = next((s for s in slots2 if s["start_time"] == target_dt.isoformat().replace("+00:00", "Z")), None)
    assert match_slot2 is not None
    assert match_slot2["available"] is True


# 16. Migration has one Alembic head
def test_single_alembic_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "c1a8f4d2e9b0"
