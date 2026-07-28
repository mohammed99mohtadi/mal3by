from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi import status

from app.models.booking import BookingStatus
from app.models.user import User, UserRole


def get_aligned_now() -> datetime:
    return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)


def register_and_get_token(client, db_session, email: str, role: UserRole = UserRole.PLAYER) -> tuple[int, str]:
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": f"{role.value.capitalize()} User",
            "password": "Password123",
        },
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


def create_test_court(client, admin_token: str, price_per_hour=10.0, is_active=True) -> int:
    headers = {"Authorization": f"Bearer {admin_token}"}
    sport_resp = client.post(
        "/api/v1/sports",
        json={"name_en": "Padel", "name_ar": "بادل", "slug": f"padel-{datetime.now().timestamp()}"},
        headers=headers,
    )
    sport_id = sport_resp.json()["id"]

    court_resp = client.post(
        "/api/v1/courts",
        json={
            "sport_id": sport_id,
            "name_en": "Court 1",
            "name_ar": "ملعب 1",
            "area": "Salmiya",
            "address": "Street 1",
            "price_per_hour": price_per_hour,
            "capacity": 4,
            "is_active": is_active,
        },
        headers=headers,
    )
    return court_resp.json()["id"]


# 1. Unauthenticated user cannot create booking
def test_unauthenticated_user_cannot_create_booking(client):
    now = get_aligned_now()
    payload = {
        "court_id": 1,
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# 2. Authenticated user can create a valid booking
def test_authenticated_user_creates_valid_booking(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b2@example.com", UserRole.ADMIN)
    user_id, user_token = register_and_get_token(client, db_session, "user_b2@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token, price_per_hour=15.0)

    now = get_aligned_now()
    start_time = now + timedelta(days=2)
    end_time = start_time + timedelta(hours=2)

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["court_id"] == court_id
    assert data["user_id"] == user_id
    assert data["status"] in ["pending", "pending_payment"]

    assert float(data["total_price"]) == 30.0  # 2 hours * 15.0/hr = 30.0


# 3 & 4. Client cannot choose user_id or total_price
def test_client_cannot_override_user_id_or_total_price(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b3@example.com", UserRole.ADMIN)
    user_id, user_token = register_and_get_token(client, db_session, "user_b3@example.com", UserRole.PLAYER)
    other_user_id, _ = register_and_get_token(client, db_session, "other_b3@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token, price_per_hour=20.0)

    now = get_aligned_now()
    start_time = now + timedelta(days=3)
    end_time = start_time + timedelta(hours=1)

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "user_id": other_user_id,  # Should be ignored/overridden by authenticated user
        "total_price": 0.01,        # Should be ignored/calculated on server
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["user_id"] == user_id
    assert float(data["total_price"]) == 20.0  # 1 hour * 20.0 = 20.0


# 5. Court not found returns 404
def test_court_not_found_returns_404(client, db_session):
    _, user_token = register_and_get_token(client, db_session, "user_b5@example.com", UserRole.PLAYER)
    now = get_aligned_now()
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": 99999,
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


# 6. Inactive/unavailable court cannot be booked
def test_inactive_court_cannot_be_booked(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b6@example.com", UserRole.ADMIN)
    _, user_token = register_and_get_token(client, db_session, "user_b6@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token, is_active=False)

    now = get_aligned_now()
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "inactive" in resp.json()["detail"].lower()


# 7. Booking in the past is rejected
def test_booking_in_past_is_rejected(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b7@example.com", UserRole.ADMIN)
    _, user_token = register_and_get_token(client, db_session, "user_b7@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 8. End time before start time is rejected
def test_end_time_before_start_time_rejected(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b8@example.com", UserRole.ADMIN)
    _, user_token = register_and_get_token(client, db_session, "user_b8@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": (now + timedelta(days=1, hours=2)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 9. Duration shorter than 30 minutes is rejected
def test_duration_shorter_than_30_minutes_rejected(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b9@example.com", UserRole.ADMIN)
    _, user_token = register_and_get_token(client, db_session, "user_b9@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, minutes=15)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 10. Duration longer than 6 hours is rejected
def test_duration_longer_than_6_hours_rejected(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b10@example.com", UserRole.ADMIN)
    _, user_token = register_and_get_token(client, db_session, "user_b10@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=7)).isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]



# 11. Total price calculated correctly
def test_total_price_calculation_fractional_hours(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b11@example.com", UserRole.ADMIN)
    _, user_token = register_and_get_token(client, db_session, "user_b11@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token, price_per_hour=12.0)

    now = get_aligned_now()
    start_time = now + timedelta(days=4)
    end_time = start_time + timedelta(hours=1, minutes=30)  # 1.5 hours * 12.0 = 18.0

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "court_id": court_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    assert float(resp.json()["total_price"]) == 18.0




# 12. Overlapping pending booking is rejected with 409
def test_overlapping_pending_booking_rejected_with_409(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b12@example.com", UserRole.ADMIN)
    _, u1_token = register_and_get_token(client, db_session, "user1_b12@example.com", UserRole.PLAYER)
    _, u2_token = register_and_get_token(client, db_session, "user2_b12@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    start1 = now + timedelta(days=5, hours=10)
    end1 = start1 + timedelta(hours=2)  # 10:00 to 12:00

    # User 1 books
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED

    # User 2 attempts overlapping slot (11:00 to 13:00)
    start2 = start1 + timedelta(hours=1)
    end2 = start2 + timedelta(hours=2)
    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start2.isoformat(), "end_time": end2.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_409_CONFLICT


# 13. Overlapping confirmed booking is rejected with 409
def test_overlapping_confirmed_booking_rejected_with_409(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b13@example.com", UserRole.ADMIN)
    _, u1_token = register_and_get_token(client, db_session, "user1_b13@example.com", UserRole.PLAYER)
    _, u2_token = register_and_get_token(client, db_session, "user2_b13@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    start1 = now + timedelta(days=6, hours=14)
    end1 = start1 + timedelta(hours=1)

    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED
    b_id = r1.json()["id"]

    # Admin confirms booking 1
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.patch(f"/api/v1/bookings/{b_id}/status", json={"status": "confirmed"}, headers=h_admin)

    # User 2 attempts overlapping booking -> 409
    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_409_CONFLICT


# 14. Cancelled booking does not block the time slot
def test_cancelled_booking_does_not_block_slot(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b14@example.com", UserRole.ADMIN)
    _, u1_token = register_and_get_token(client, db_session, "user1_b14@example.com", UserRole.PLAYER)
    _, u2_token = register_and_get_token(client, db_session, "user2_b14@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    start1 = now + timedelta(days=7, hours=16)
    end1 = start1 + timedelta(hours=1)

    # User 1 books and then cancels
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED
    b_id = r1.json()["id"]
    client.post(f"/api/v1/bookings/{b_id}/cancel", headers=h1)

    # User 2 books exact same slot -> SUCCESS
    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_201_CREATED


# 15. Adjacent bookings are allowed (first ends exactly when second starts)
def test_adjacent_bookings_allowed(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b15@example.com", UserRole.ADMIN)
    _, u1_token = register_and_get_token(client, db_session, "user1_b15@example.com", UserRole.PLAYER)
    _, u2_token = register_and_get_token(client, db_session, "user2_b15@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    start1 = now + timedelta(days=8, hours=10)
    end1 = start1 + timedelta(hours=1)

    start2 = end1
    end2 = start2 + timedelta(hours=1)

    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start1.isoformat(), "end_time": end1.isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED

    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start2.isoformat(), "end_time": end2.isoformat()}, headers=h2)
    assert r2.status_code == status.HTTP_201_CREATED


# 16. User can list their own bookings
def test_user_can_list_own_bookings(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b16@example.com", UserRole.ADMIN)
    _, u_token = register_and_get_token(client, db_session, "user_b16@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    h = {"Authorization": f"Bearer {u_token}"}
    client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": (now + timedelta(days=9)).isoformat(), "end_time": (now + timedelta(days=9, hours=1)).isoformat()}, headers=h)

    resp = client.get("/api/v1/bookings/me", headers=h)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 1


# 17. User cannot view another user's booking
def test_user_cannot_view_another_users_booking(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b17@example.com", UserRole.ADMIN)
    _, u1_token = register_and_get_token(client, db_session, "user1_b17@example.com", UserRole.PLAYER)
    _, u2_token = register_and_get_token(client, db_session, "user2_b17@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": (now + timedelta(days=10)).isoformat(), "end_time": (now + timedelta(days=10, hours=1)).isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED
    b_id = r1.json()["id"]

    h2 = {"Authorization": f"Bearer {u2_token}"}
    r2 = client.get(f"/api/v1/bookings/{b_id}", headers=h2)
    assert r2.status_code == status.HTTP_403_FORBIDDEN


# 18 & 19 & 20. Cancellation permissions and repeat cancellation rules
def test_cancellation_rules_and_permissions(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b18@example.com", UserRole.ADMIN)
    _, u1_token = register_and_get_token(client, db_session, "user1_b18@example.com", UserRole.PLAYER)
    _, u2_token = register_and_get_token(client, db_session, "user2_b18@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    h1 = {"Authorization": f"Bearer {u1_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": (now + timedelta(days=11)).isoformat(), "end_time": (now + timedelta(days=11, hours=1)).isoformat()}, headers=h1)
    assert r1.status_code == status.HTTP_201_CREATED
    b_id = r1.json()["id"]

    # 19. User 2 cannot cancel User 1's booking -> 403
    h2 = {"Authorization": f"Bearer {u2_token}"}
    r_other_cancel = client.post(f"/api/v1/bookings/{b_id}/cancel", headers=h2)
    assert r_other_cancel.status_code == status.HTTP_403_FORBIDDEN

    # 18. User 1 cancels own booking -> 200 OK
    r_own_cancel = client.post(f"/api/v1/bookings/{b_id}/cancel", json={"cancellation_reason": "Changed plans"}, headers=h1)
    assert r_own_cancel.status_code == status.HTTP_200_OK
    assert r_own_cancel.json()["status"] == "cancelled"

    # 20. Repeat cancellation -> 400 Bad Request
    r_repeat_cancel = client.post(f"/api/v1/bookings/{b_id}/cancel", headers=h1)
    assert r_repeat_cancel.status_code == status.HTTP_400_BAD_REQUEST


# 21 & 22 & 23. Status transition rules and permissions
def test_status_update_permissions_and_transitions(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b21@example.com", UserRole.ADMIN)
    _, u_token = register_and_get_token(client, db_session, "user_b21@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    h = {"Authorization": f"Bearer {u_token}"}
    r1 = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": (now + timedelta(days=12)).isoformat(), "end_time": (now + timedelta(days=12, hours=1)).isoformat()}, headers=h)
    assert r1.status_code == status.HTTP_201_CREATED
    b_id = r1.json()["id"]

    # 21. Normal user cannot update status -> 403
    r_user_patch = client.patch(f"/api/v1/bookings/{b_id}/status", json={"status": "confirmed"}, headers=h)
    assert r_user_patch.status_code == status.HTTP_403_FORBIDDEN

    # 22. Admin can update status to confirmed -> 200
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r_admin_patch = client.patch(f"/api/v1/bookings/{b_id}/status", json={"status": "confirmed"}, headers=h_admin)
    assert r_admin_patch.status_code == status.HTTP_200_OK
    assert r_admin_patch.json()["status"] == "confirmed"

    # 23. Invalid status transition (confirmed -> pending) -> 400
    r_invalid_trans = client.patch(f"/api/v1/bookings/{b_id}/status", json={"status": "pending"}, headers=h_admin)
    assert r_invalid_trans.status_code == status.HTTP_400_BAD_REQUEST


# 24 & 25. Availability endpoint tests
def test_availability_endpoint(client, db_session):
    _, admin_token = register_and_get_token(client, db_session, "admin_b24@example.com", UserRole.ADMIN)
    _, u_token = register_and_get_token(client, db_session, "user_b24@example.com", UserRole.PLAYER)
    court_id = create_test_court(client, admin_token)

    now = get_aligned_now()
    start_time = now + timedelta(days=13, hours=10)
    end_time = start_time + timedelta(hours=2)

    start_str = start_time.isoformat().replace("+00:00", "Z")
    end_str = end_time.isoformat().replace("+00:00", "Z")

    # 24. Free slot returns true
    r_avail1 = client.get(f"/api/v1/bookings/availability/{court_id}?start_time={start_str}&end_time={end_str}")
    assert r_avail1.status_code == status.HTTP_200_OK
    assert r_avail1.json()["available"] is True

    # User books the slot
    h = {"Authorization": f"Bearer {u_token}"}
    r_b = client.post("/api/v1/bookings", json={"court_id": court_id, "start_time": start_time.isoformat(), "end_time": end_time.isoformat()}, headers=h)
    assert r_b.status_code == status.HTTP_201_CREATED

    # 25. Occupied slot returns false
    r_avail2 = client.get(f"/api/v1/bookings/availability/{court_id}?start_time={start_str}&end_time={end_str}")
    assert r_avail2.status_code == status.HTTP_200_OK
    assert r_avail2.json()["available"] is False
