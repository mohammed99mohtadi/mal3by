from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fastapi import status

from app.models.availability import CourtClosureType
from app.models.booking import BookingStatus
from app.models.court import Court
from app.models.user import User, UserRole

from app.services.availability_service import get_zone_info


def get_aligned_now() -> datetime:
    return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)


def register_user(client, db_session, email: str, role: UserRole = UserRole.PLAYER) -> tuple[int, str]:
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": f"{role.value.capitalize()} User", "password": "Password123"},
    )
    assert reg_resp.status_code == status.HTTP_201_CREATED
    user_id = reg_resp.json()["id"]

    if role != UserRole.PLAYER:
        user = db_session.query(User).filter(User.id == user_id).first()
        user.role = role
        user.is_admin = (role == UserRole.ADMIN)
        db_session.commit()

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    return user_id, login_resp.json()["access_token"]


def create_court(client, token: str, price_per_hour=10.0) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    s_resp = client.post(
        "/api/v1/sports",
        json={"name_en": "Padel", "name_ar": "بادل", "slug": f"padel-{datetime.now().timestamp()}"},
        headers=headers,
    )
    sport_id = s_resp.json()["id"]

    c_resp = client.post(
        "/api/v1/courts",
        json={
            "sport_id": sport_id,
            "name_en": f"Court {datetime.now().timestamp()}",
            "name_ar": "ملعب",
            "area": "Salmiya",
            "address": "Street 1",
            "price_per_hour": price_per_hour,
            "capacity": 4,
            "is_active": True,
        },
        headers=headers,
    )
    return c_resp.json()["id"]


# 1. Existing court without working hours preserves backward-compatible availability (24/7)
def test_court_without_working_hours_is_open(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a1@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a1@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    now = get_aligned_now()
    start_time = now + timedelta(days=2, hours=3)
    end_time = start_time + timedelta(hours=1)

    h_player = {"Authorization": f"Bearer {player_token}"}
    r = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": start_time.isoformat(), "end_time": end_time.isoformat()},
        headers=h_player,
    )
    assert r.status_code == status.HTTP_201_CREATED


# 2 & 4. Admin and Court owner can configure availability rules
def test_admin_and_owner_can_configure_rules(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a2@example.com", UserRole.ADMIN)
    owner_id, owner_token = register_user(client, db_session, "owner_a2@example.com", UserRole.OWNER)
    h_admin = {"Authorization": f"Bearer {admin_token}"}

    # Admin creates court and sets owner_id
    court_id = create_court(client, admin_token)
    db_session.query(Court).filter(Court.id == court_id).update({"owner_id": owner_id})
    db_session.commit()
    db_session.expire_all()




    # 4. Owner configures rules
    h_owner = {"Authorization": f"Bearer {owner_token}"}
    r_owner = client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"buffer_minutes": 15, "minimum_booking_minutes": 60},
        headers=h_owner,
    )
    assert r_owner.status_code == status.HTTP_200_OK
    assert r_owner.json()["buffer_minutes"] == 15
    assert r_owner.json()["minimum_booking_minutes"] == 60

    # 2. Admin configures rules
    r_admin = client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"buffer_minutes": 30},
        headers=h_admin,
    )
    assert r_admin.status_code == status.HTTP_200_OK
    assert r_admin.json()["buffer_minutes"] == 30


# 3. Normal user cannot configure availability rules (403)
def test_normal_user_cannot_configure_rules(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a3@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a3@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_player = {"Authorization": f"Bearer {player_token}"}
    r = client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"buffer_minutes": 15},
        headers=h_player,
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


# 5. Court owner cannot configure another owner's court (403)
def test_owner_cannot_configure_other_owners_court(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a5@example.com", UserRole.ADMIN)
    owner1_id, _ = register_user(client, db_session, "owner1_a5@example.com", UserRole.OWNER)
    _, owner2_token = register_user(client, db_session, "owner2_a5@example.com", UserRole.OWNER)

    court_id = create_court(client, admin_token)
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.patch(f"/api/v1/courts/{court_id}", json={"owner_id": owner1_id}, headers=h_admin)

    h_owner2 = {"Authorization": f"Bearer {owner2_token}"}
    r = client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"buffer_minutes": 15},
        headers=h_owner2,
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


# 6 & 7. Minimum and Maximum booking duration enforced
def test_min_and_max_booking_duration_enforced(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a6@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a6@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"minimum_booking_minutes": 60, "maximum_booking_minutes": 120},
        headers=h_admin,
    )

    now = get_aligned_now()
    h_player = {"Authorization": f"Bearer {player_token}"}

    # 6. Shorter than min (30 mins < 60 mins min) -> 400
    r_short = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": (now + timedelta(days=2)).isoformat(), "end_time": (now + timedelta(days=2, minutes=30)).isoformat()},
        headers=h_player,
    )
    assert r_short.status_code == status.HTTP_400_BAD_REQUEST

    # 7. Longer than max (180 mins > 120 mins max) -> 400
    r_long = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": (now + timedelta(days=2)).isoformat(), "end_time": (now + timedelta(days=2, hours=3)).isoformat()},
        headers=h_player,
    )
    assert r_long.status_code == status.HTTP_400_BAD_REQUEST


# 8 & 9. Booking interval and start-time alignment enforced
def test_interval_and_start_time_alignment_enforced(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a8@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a8@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"booking_interval_minutes": 30},
        headers=h_admin,
    )

    base_time = get_aligned_now() + timedelta(days=2)
    h_player = {"Authorization": f"Bearer {player_token}"}

    # 9. Misaligned start time (e.g. 10:15) -> 400
    unaligned_start = base_time + timedelta(minutes=15)
    r_start = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": unaligned_start.isoformat(), "end_time": (unaligned_start + timedelta(hours=1)).isoformat()},
        headers=h_player,
    )
    assert r_start.status_code == status.HTTP_400_BAD_REQUEST

    # 8. Misaligned duration (e.g. 45 mins with 30 min interval) -> 400
    r_dur = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": base_time.isoformat(), "end_time": (base_time + timedelta(minutes=45)).isoformat()},
        headers=h_player,
    )
    assert r_dur.status_code == status.HTTP_400_BAD_REQUEST


# 10 & 11. Advance booking rules enforced
def test_advance_booking_rules_enforced(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a10@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a10@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"minimum_advance_booking_minutes": 60, "maximum_advance_booking_days": 7},
        headers=h_admin,
    )

    now = get_aligned_now()
    h_player = {"Authorization": f"Bearer {player_token}"}

    # 11. Less than min advance (15 mins advance < 60 mins min) -> 400 or 422
    r_min_adv = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": (now + timedelta(minutes=15)).isoformat(), "end_time": (now + timedelta(minutes=75)).isoformat()},
        headers=h_player,
    )
    assert r_min_adv.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


    # 10. Exceeds max advance days (10 days > 7 days max) -> 400
    r_max_adv = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": (now + timedelta(days=10)).isoformat(), "end_time": (now + timedelta(days=10, hours=1)).isoformat()},
        headers=h_player,
    )
    assert r_max_adv.status_code == status.HTTP_400_BAD_REQUEST


# 12 & 13 & 14. Working hours and closed weekday checks
def test_working_hours_and_closed_weekday(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a12@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a12@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    # Configure Friday (weekday 4) as closed, Monday (weekday 0) 08:00 to 20:00 local time
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/working-hours/4",
        json={"weekday": 4, "is_closed": True},
        headers=h_admin,
    )
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/working-hours/0",
        json={"weekday": 0, "opens_at": "08:00:00", "closes_at": "20:00:00", "is_closed": False},
        headers=h_admin,
    )

    tz = get_zone_info("Asia/Kuwait")
    h_player = {"Authorization": f"Bearer {player_token}"}

    # Find next Friday in local time
    now_local = datetime.now(tz)
    days_to_fri = (4 - now_local.weekday()) % 7
    if days_to_fri == 0:
        days_to_fri = 7
    fri_local = (now_local + timedelta(days=days_to_fri)).replace(hour=10, minute=0, second=0, microsecond=0)

    # 14. Booking on closed Friday -> 400
    r_fri = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": fri_local.astimezone(timezone.utc).isoformat(), "end_time": (fri_local + timedelta(hours=1)).astimezone(timezone.utc).isoformat()},
        headers=h_player,
    )
    assert r_fri.status_code == status.HTTP_400_BAD_REQUEST

    # Find next Monday in local time
    days_to_mon = (0 - now_local.weekday()) % 7
    if days_to_mon == 0:
        days_to_mon = 7
    mon_local = (now_local + timedelta(days=days_to_mon)).replace(hour=6, minute=0, second=0, microsecond=0) # 06:00 is outside 08:00-20:00

    # 13. Outside Monday open hours -> 400
    r_mon_out = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": mon_local.astimezone(timezone.utc).isoformat(), "end_time": (mon_local + timedelta(hours=1)).astimezone(timezone.utc).isoformat()},
        headers=h_player,
    )
    assert r_mon_out.status_code == status.HTTP_400_BAD_REQUEST

    # 12. Inside Monday open hours (10:00 -> 11:00) -> 201
    mon_in = mon_local.replace(hour=10)
    r_mon_in = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": mon_in.astimezone(timezone.utc).isoformat(), "end_time": (mon_in + timedelta(hours=1)).astimezone(timezone.utc).isoformat()},
        headers=h_player,
    )
    assert r_mon_in.status_code == status.HTTP_201_CREATED


# 15 & 16 & 17. Overnight working hours support
def test_overnight_working_hours(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a15@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a15@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    # Configure Friday (weekday 4): 18:00 to 02:00 (overnight)
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/working-hours/4",
        json={"weekday": 4, "opens_at": "18:00:00", "closes_at": "02:00:00", "is_closed": False},
        headers=h_admin,
    )

    tz = get_zone_info("Asia/Kuwait")
    now_local = datetime.now(tz)
    days_to_fri = (4 - now_local.weekday()) % 7
    if days_to_fri == 0:
        days_to_fri = 7
    fri_local = (now_local + timedelta(days=days_to_fri)).replace(hour=19, minute=0, second=0, microsecond=0)

    h_player = {"Authorization": f"Bearer {player_token}"}

    # 15. Before midnight (Friday 19:00 -> 20:00) -> 201
    r15 = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": fri_local.astimezone(timezone.utc).isoformat(), "end_time": (fri_local + timedelta(hours=1)).astimezone(timezone.utc).isoformat()},
        headers=h_player,
    )
    assert r15.status_code == status.HTTP_201_CREATED

    # 16. After midnight (Saturday 01:00 -> 02:00) -> 201
    sat_after_midnight = (fri_local + timedelta(days=1)).replace(hour=1, minute=0)
    r16 = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": sat_after_midnight.astimezone(timezone.utc).isoformat(), "end_time": (sat_after_midnight + timedelta(hours=1)).astimezone(timezone.utc).isoformat()},
        headers=h_player,
    )
    assert r16.status_code == status.HTTP_201_CREATED

    # 17. Beyond closing time (Saturday 02:00 -> 03:00) -> 400
    sat_beyond = (fri_local + timedelta(days=1)).replace(hour=2, minute=0)
    r17 = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": sat_beyond.astimezone(timezone.utc).isoformat(), "end_time": (sat_beyond + timedelta(hours=1)).astimezone(timezone.utc).isoformat()},
        headers=h_player,
    )
    assert r17.status_code == status.HTTP_400_BAD_REQUEST


# 18 & 19 & 20 & 21. Court Closure management and booking overlap
def test_closures_and_booking_overlaps(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a18@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a18@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    now = get_aligned_now()
    closure_start = now + timedelta(days=5, hours=10)
    closure_end = closure_start + timedelta(hours=4)

    h_player = {"Authorization": f"Bearer {player_token}"}

    # 19. Normal user cannot create closure -> 403
    r_user_cls = client.post(
        f"/api/v1/courts/{court_id}/availability-settings/closures",
        json={"start_time": closure_start.isoformat(), "end_time": closure_end.isoformat(), "reason": "Maintenance"},
        headers=h_player,
    )
    assert r_user_cls.status_code == status.HTTP_403_FORBIDDEN

    # 18. Admin creates closure -> 201
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r_admin_cls = client.post(
        f"/api/v1/courts/{court_id}/availability-settings/closures",
        json={"start_time": closure_start.isoformat(), "end_time": closure_end.isoformat(), "reason": "Maintenance"},
        headers=h_admin,
    )
    assert r_admin_cls.status_code == status.HTTP_201_CREATED

    # 20. Booking overlapping closure -> 400
    r_over = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": (closure_start + timedelta(hours=1)).isoformat(), "end_time": (closure_start + timedelta(hours=2)).isoformat()},
        headers=h_player,
    )
    assert r_over.status_code == status.HTTP_400_BAD_REQUEST

    # 21. Adjacent booking outside closure (starts exactly at closure_end) -> 201
    r_adj = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": closure_end.isoformat(), "end_time": (closure_end + timedelta(hours=1)).isoformat()},
        headers=h_player,
    )
    assert r_adj.status_code == status.HTTP_201_CREATED


# 22 & 23 & 24. Buffer minutes enforcement
def test_buffer_minutes_enforcement(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a22@example.com", UserRole.ADMIN)
    _, u1_token = register_user(client, db_session, "u1_a22@example.com", UserRole.PLAYER)
    _, u2_token = register_user(client, db_session, "u2_a22@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    # Configure 15 minute buffer and 15 minute interval
    client.put(
        f"/api/v1/courts/{court_id}/availability-settings/rules",
        json={"buffer_minutes": 15, "booking_interval_minutes": 15},
        headers=h_admin,
    )


    now = get_aligned_now()
    start1 = now + timedelta(days=6, hours=10)
    end1 = start1 + timedelta(hours=1) # 10:00 to 11:00

    # User 1 books 10:00 -> 11:00
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r_b1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r_b1.status_code == status.HTTP_201_CREATED

    h2 = {"Authorization": f"Bearer {u2_token}"}

    # 23. Buffer after (11:00 to 11:15 is buffered, so 11:00 -> 12:00 overlaps buffer) -> 409
    r_after = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": end1.isoformat(), "end_time": (end1 + timedelta(hours=1)).isoformat()}, headers=h2)
    assert r_after.status_code == status.HTTP_409_CONFLICT

    # 22. Buffer before (09:45 to 10:00 is buffered, so 09:00 -> 10:00 overlaps buffer) -> 409
    r_before = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": (start1 - timedelta(hours=1)).isoformat(), "end_time": start1.isoformat()}, headers=h2)
    assert r_before.status_code == status.HTTP_409_CONFLICT

    # 24. Booking starting exactly after buffer ends (11:15 -> 12:15) -> 201
    exact_start = end1 + timedelta(minutes=15)
    r_exact = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": exact_start.isoformat(), "end_time": (exact_start + timedelta(hours=1)).isoformat()}, headers=h2)
    assert r_exact.status_code == status.HTTP_201_CREATED


# 25 & 26. Cancelled and Rejected bookings do not block slots
def test_cancelled_and_rejected_bookings_unblock_slots(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a25@example.com", UserRole.ADMIN)
    _, u1_token = register_user(client, db_session, "u1_a25@example.com", UserRole.PLAYER)
    _, u2_token = register_user(client, db_session, "u2_a25@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    now = get_aligned_now()
    start1 = now + timedelta(days=7, hours=14)
    end1 = start1 + timedelta(hours=1)

    # 25. User 1 books and cancels
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r_b1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r_b1.status_code == status.HTTP_201_CREATED
    b1_id = r_b1.json()["id"]
    client.post(f"/api/v1/bookings/{b1_id}/cancel", headers=h1)

    h2 = {"Authorization": f"Bearer {u2_token}"}
    r_slot1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h2)
    assert r_slot1.status_code == status.HTTP_201_CREATED
    b2_id = r_slot1.json()["id"]

    # 26. Admin rejects booking 2
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.patch(f"/api/v1/bookings/{b2_id}/status", json={"status": "rejected"}, headers=h_admin)

    # User 1 re-books slot -> 201
    r_slot2 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r_slot2.status_code == status.HTTP_201_CREATED


# 27 & 28 & 29 & 30. Public slots endpoint tests
def test_public_available_slots_endpoint(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a27@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a27@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    now_utc = get_aligned_now()
    target_date = (now_utc + timedelta(days=8)).date()

    # 27. Public slot generation returns valid intervals
    url = f"/api/v1/courts/{court_id}/available-slots?date={target_date.isoformat()}&duration_minutes=60"
    resp = client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["court_id"] == court_id
    assert len(data["slots"]) > 0

    # Book first slot
    slot0 = data["slots"][0]
    h_player = {"Authorization": f"Bearer {player_token}"}
    client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": slot0["start_time"], "end_time": slot0["end_time"]}, headers=h_player)

    # 28. Public slots exclude booked interval (marked available: False)
    resp2 = client.get(url)
    data2 = resp2.json()
    booked_slot = next(s for s in data2["slots"] if s["start_time"] == slot0["start_time"])
    assert booked_slot["available"] is False

    # 29. Add closure and verify excluded
    slot1 = data2["slots"][1]
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/availability-settings/closures",
        json={"start_time": slot1["start_time"], "end_time": slot1["end_time"], "reason": "Repair"},
        headers=h_admin,
    )
    resp3 = client.get(url)
    closed_slot = next(s for s in resp3.json()["slots"] if s["start_time"] == slot1["start_time"])
    assert closed_slot["available"] is False

    # 30. Past slots excluded
    today = now_utc.date() - timedelta(days=1)
    resp_past = client.get(f"/api/v1/courts/{court_id}/available-slots?date={today.isoformat()}&duration_minutes=60")
    assert len(resp_past.json()["slots"]) == 0


# 31 & 32. Timezone-aware validation and naive datetimes rejection
def test_timezone_validation(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a31@example.com", UserRole.ADMIN)
    _, player_token = register_user(client, db_session, "player_a31@example.com", UserRole.PLAYER)
    court_id = create_court(client, admin_token)

    now = datetime.now() # Naive datetime
    h_player = {"Authorization": f"Bearer {player_token}"}

    # 32. Naive datetime rejected
    payload = {
        "court_id": court_id,
        "start_time": now.isoformat(), # Naive ISO string without timezone offset
        "end_time": (now + timedelta(hours=1)).isoformat(),
    }
    r = client.post("/api/v1/bookings", json=payload, headers=h_player)
    assert r.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # 31. Timezone-aware datetime accepted
    now_utc = get_aligned_now()
    payload_tz = {
        "court_id": court_id,
        "start_time": (now_utc + timedelta(days=9)).isoformat(),
        "end_time": (now_utc + timedelta(days=9, hours=1)).isoformat(),
    }
    r_tz = client.post("/api/v1/bookings", json=payload_tz, headers=h_player)
    assert r_tz.status_code == status.HTTP_201_CREATED


# 33 & 34. Closure update and deletion
def test_closure_update_and_deletion(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_a33@example.com", UserRole.ADMIN)
    court_id = create_court(client, admin_token)

    now = get_aligned_now()
    start_t = now + timedelta(days=11, hours=10)
    end_t = start_t + timedelta(hours=2)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r_create = client.post(
        f"/api/v1/courts/{court_id}/availability-settings/closures",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat(), "reason": "Initial Reason"},
        headers=h_admin,
    )
    assert r_create.status_code == status.HTTP_201_CREATED
    cls_id = r_create.json()["id"]

    # 33. Closure update works
    r_update = client.patch(
        f"/api/v1/courts/{court_id}/availability-settings/closures/{cls_id}",
        json={"reason": "Updated Reason"},
        headers=h_admin,
    )
    assert r_update.status_code == status.HTTP_200_OK
    assert r_update.json()["reason"] == "Updated Reason"

    # 34. Closure deletion works -> 204
    r_del = client.delete(
        f"/api/v1/courts/{court_id}/availability-settings/closures/{cls_id}",
        headers=h_admin,
    )
    assert r_del.status_code == status.HTTP_204_NO_CONTENT


# 35. Migration has one Alembic head
def test_alembic_single_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config("alembic.ini")
    script_dir = ScriptDirectory.from_config(alembic_cfg)
    heads = script_dir.get_heads()
    assert len(heads) == 1
