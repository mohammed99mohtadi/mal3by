from datetime import datetime, timedelta, timezone

from fastapi import status

from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.sport import Sport
from app.models.user import User, UserRole


def user(client, db, email, role=UserRole.PLAYER):
    uid = client.post("/api/v1/auth/register", json={"email": email, "full_name": "Review User", "password": "Password123"}).json()["id"]
    if role != UserRole.PLAYER:
        row = db.get(User, uid); row.role = role; row.is_admin = role == UserRole.ADMIN; db.commit()
    return uid, client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"}).json()["access_token"]


def completed_booking(client, db, owner_token, player_id):
    sport = Sport(name_en="Padel", name_ar="Padel", slug="review-padel"); db.add(sport); db.commit()
    court = client.post("/api/v1/courts", json={"sport_id": sport.id, "name_en": "Review Court", "name_ar": "Review Court", "area": "City", "address": "Street", "price_per_hour": 10, "capacity": 4}, headers={"Authorization": f"Bearer {owner_token}"}).json()
    row = Booking(user_id=player_id, court_id=court["id"], start_time=datetime.now(timezone.utc) - timedelta(hours=2), end_time=datetime.now(timezone.utc) - timedelta(hours=1), total_price=10, status=BookingStatus.COMPLETED)
    db.add(row); db.commit()
    return court["id"], row.id


def test_completed_booking_creates_verified_review_and_summary(client, db_session):
    _, admin = user(client, db_session, "review_admin@example.com", UserRole.ADMIN); player_id, player = user(client, db_session, "reviewer@example.com")
    court_id, booking_id = completed_booking(client, db_session, admin, player_id)
    response = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 5, "comment": "  Great court  ", "status": "hidden"}, headers={"Authorization": f"Bearer {player}"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["is_verified_booking"] is True and response.json()["comment"] == "Great court"
    summary = client.get(f"/api/v1/courts/{court_id}/rating-summary").json()
    assert summary["average_rating"] == "5.00" and summary["rating_distribution"]["five"] == 1
    assert client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 4}, headers={"Authorization": f"Bearer {player}"}).status_code == status.HTTP_409_CONFLICT


def test_review_requires_own_completed_booking(client, db_session):
    _, admin = user(client, db_session, "review_admin2@example.com", UserRole.ADMIN); player_id, player = user(client, db_session, "reviewer2@example.com"); _, other = user(client, db_session, "otherreviewer@example.com")
    _, booking_id = completed_booking(client, db_session, admin, player_id)
    assert client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 3}, headers={"Authorization": f"Bearer {other}"}).status_code == status.HTTP_403_FORBIDDEN
    assert client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 6}, headers={"Authorization": f"Bearer {player}"}).status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_owner_response_and_admin_moderation_hide_public_review(client, db_session):
    admin_id, admin = user(client, db_session, "review_admin3@example.com", UserRole.ADMIN); player_id, player = user(client, db_session, "reviewer3@example.com")
    court_id, booking_id = completed_booking(client, db_session, admin, player_id)
    review = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 2}, headers={"Authorization": f"Bearer {player}"}).json()
    response = client.post(f"/api/v1/reviews/{review['id']}/response", json={"response_text": "We will improve"}, headers={"Authorization": f"Bearer {admin}"})
    assert response.status_code == status.HTTP_200_OK and response.json()["owner_response"]["response_text"] == "We will improve"
    hidden = client.post(f"/api/v1/admin/reviews/{review['id']}/hide", json={"moderation_reason": "spam"}, headers={"Authorization": f"Bearer {admin}"})
    assert hidden.status_code == status.HTTP_200_OK
    assert client.get(f"/api/v1/courts/{court_id}/reviews").json() == []
    assert client.get(f"/api/v1/reviews/{review['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/reviews/{review['id']}", headers={"Authorization": f"Bearer {player}"}).status_code == status.HTTP_200_OK


def test_review_me_route_precedes_dynamic_and_delete_soft_deletes(client, db_session):
    _, admin = user(client, db_session, "review_admin4@example.com", UserRole.ADMIN); player_id, player = user(client, db_session, "reviewer4@example.com")
    court_id, booking_id = completed_booking(client, db_session, admin, player_id)
    review = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 4}, headers={"Authorization": f"Bearer {player}"}).json()
    headers = {"Authorization": f"Bearer {player}"}
    assert client.get("/api/v1/reviews/me", headers=headers).status_code == status.HTTP_200_OK
    assert client.delete(f"/api/v1/reviews/{review['id']}", headers=headers).status_code == status.HTTP_200_OK
    assert client.get(f"/api/v1/courts/{court_id}/reviews").json() == []
    assert client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 5}, headers=headers).status_code == status.HTTP_409_CONFLICT


def test_update_ignores_server_fields_and_public_schema_is_safe(client, db_session):
    _, admin = user(client, db_session, "review_admin5@example.com", UserRole.ADMIN); _, player = user(client, db_session, "reviewer5@example.com"); _, other = user(client, db_session, "reviewer_other5@example.com")
    court_id, booking_id = completed_booking(client, db_session, admin, db_session.query(User).filter_by(email="reviewer5@example.com").one().id)
    headers = {"Authorization": f"Bearer {player}"}
    review = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 2, "comment": "old"}, headers=headers).json()
    patched = client.patch(f"/api/v1/reviews/{review['id']}", json={"rating": 4, "comment": "new", "booking_id": 999, "court_id": 999, "status": "hidden", "is_verified_booking": False}, headers=headers)
    assert patched.status_code == status.HTTP_200_OK
    assert patched.json()["rating"] == 4 and patched.json()["status"] == "published" and patched.json()["booking_id"] == booking_id
    assert client.patch(f"/api/v1/reviews/{review['id']}", json={"rating": 1}, headers={"Authorization": f"Bearer {other}"}).status_code == status.HTTP_403_FORBIDDEN
    public = client.get(f"/api/v1/courts/{court_id}/reviews").json()[0]
    assert {"booking_id", "status", "deleted_at", "moderation_reason", "email", "phone_number"}.isdisjoint(public)
    assert client.get(f"/api/v1/courts/{court_id}/rating-summary").json()["average_rating"] == "4.00"


def test_moderation_transitions_and_summary_exclusion(client, db_session):
    _, admin = user(client, db_session, "review_admin6@example.com", UserRole.ADMIN); player_id, player = user(client, db_session, "reviewer6@example.com")
    court_id, booking_id = completed_booking(client, db_session, admin, player_id)
    review = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 1}, headers={"Authorization": f"Bearer {player}"}).json()
    assert client.post(f"/api/v1/admin/reviews/{review['id']}/hide", headers={"Authorization": f"Bearer {player}"}).status_code == status.HTTP_403_FORBIDDEN
    hidden = client.post(f"/api/v1/admin/reviews/{review['id']}/hide", json={"moderation_reason": "abuse"}, headers={"Authorization": f"Bearer {admin}"})
    assert hidden.status_code == status.HTTP_200_OK and hidden.json()["moderation_reason"] == "abuse"
    assert client.get(f"/api/v1/courts/{court_id}/rating-summary").json()["total_reviews"] == 0
    assert client.post(f"/api/v1/admin/reviews/{review['id']}/publish", headers={"Authorization": f"Bearer {admin}"}).status_code == status.HTTP_200_OK
    assert client.get(f"/api/v1/courts/{court_id}/rating-summary").json()["rating_distribution"]["one"] == 1
    assert client.post(f"/api/v1/admin/reviews/{review['id']}/remove", headers={"Authorization": f"Bearer {admin}"}).status_code == status.HTTP_200_OK
    assert client.post(f"/api/v1/admin/reviews/{review['id']}/publish", headers={"Authorization": f"Bearer {admin}"}).status_code == status.HTTP_409_CONFLICT


def test_review_completion_boundary_allows_exact_end_time(client, db_session, monkeypatch):
    _, admin = user(client, db_session, "review_boundary_admin@example.com", UserRole.ADMIN)
    player_id, player = user(client, db_session, "review_boundary_player@example.com")
    court_id, booking_id = completed_booking(client, db_session, admin, player_id)
    boundary = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)
    booking = db_session.get(Booking, booking_id)
    booking.start_time, booking.end_time = boundary - timedelta(hours=1), boundary
    future_booking = Booking(user_id=player_id, court_id=court_id, start_time=boundary, end_time=boundary + timedelta(hours=1), total_price=10, status=BookingStatus.COMPLETED)
    db_session.add(future_booking); db_session.commit()
    monkeypatch.setattr("app.services.review_service._now", lambda: boundary)
    headers = {"Authorization": f"Bearer {player}"}
    assert client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 5}, headers=headers).status_code == status.HTTP_201_CREATED
    assert client.post("/api/v1/reviews", json={"booking_id": future_booking.id, "rating": 5}, headers=headers).status_code == status.HTTP_409_CONFLICT


def test_cross_owner_cannot_manage_another_court_review_response(client, db_session):
    owner_a_id, owner_a = user(client, db_session, "review_owner_a@example.com", UserRole.OWNER)
    owner_b_id, owner_b = user(client, db_session, "review_owner_b@example.com", UserRole.OWNER)
    player_id, player = user(client, db_session, "review_idor_player@example.com")
    sport = Sport(name_en="Tennis", name_ar="Tennis", slug="review-idor-tennis")
    db_session.add(sport); db_session.flush()
    court_a = Court(owner_id=owner_a_id, sport_id=sport.id, name_en="Court A", name_ar="Court A", area="City", address="A", price_per_hour=10, capacity=4)
    court_b = Court(owner_id=owner_b_id, sport_id=sport.id, name_en="Court B", name_ar="Court B", area="City", address="B", price_per_hour=10, capacity=4)
    db_session.add_all([court_a, court_b]); db_session.flush()
    booking = Booking(user_id=player_id, court_id=court_a.id, start_time=datetime.now(timezone.utc) - timedelta(hours=2), end_time=datetime.now(timezone.utc) - timedelta(hours=1), total_price=10, status=BookingStatus.COMPLETED)
    db_session.add(booking); db_session.commit()
    review = client.post("/api/v1/reviews", json={"booking_id": booking.id, "rating": 4}, headers={"Authorization": f"Bearer {player}"}).json()
    owner_a_headers, owner_b_headers = {"Authorization": f"Bearer {owner_a}"}, {"Authorization": f"Bearer {owner_b}"}
    assert client.post(f"/api/v1/reviews/{review['id']}/response", json={"response_text": "Owner A"}, headers=owner_a_headers).status_code == status.HTTP_200_OK
    assert client.post(f"/api/v1/reviews/{review['id']}/response", json={"response_text": "Owner B"}, headers=owner_b_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.patch(f"/api/v1/reviews/{review['id']}/response", json={"response_text": "Takeover"}, headers=owner_b_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.delete(f"/api/v1/reviews/{review['id']}/response", headers=owner_b_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.patch(f"/api/v1/reviews/{review['id']}/response", json={"response_text": "Updated"}, headers=owner_a_headers).status_code == status.HTTP_200_OK
    assert client.delete(f"/api/v1/reviews/{review['id']}/response", headers=owner_a_headers).status_code == status.HTTP_204_NO_CONTENT
