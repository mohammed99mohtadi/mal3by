from datetime import datetime, timedelta, timezone

from fastapi import status

from app.models.booking import Booking
from app.models.court import Court
from app.models.match import Match, MatchParticipant, MatchStatus, ParticipantStatus
from app.models.sport import Sport
from app.models.user import User, UserRole


def register_user(client, db_session, email, role=UserRole.PLAYER):
    response = client.post("/api/v1/auth/register", json={"email": email, "full_name": "Match User", "password": "Password123"})
    user_id = response.json()["id"]
    if role != UserRole.PLAYER:
        user = db_session.get(User, user_id)
        user.role = role
        user.is_admin = role == UserRole.ADMIN
        db_session.commit()
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"}).json()["access_token"]
    return user_id, token


def create_court(client, db_session, admin_token):
    sport = db_session.query(Sport).first()
    if not sport:
        sport = Sport(name_en="Padel", name_ar="Padel", slug="padel")
        db_session.add(sport)
        db_session.commit()
    response = client.post("/api/v1/courts", json={
        "sport_id": sport.id, "name_en": "Match Court", "name_ar": "Match Court", "area": "Salmiya",
        "address": "Block 5", "price_per_hour": 10, "capacity": 8,
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]


def confirmed_booking(client, court_id, token, offset=5):
    start = (datetime.now(timezone.utc) + timedelta(days=offset)).replace(hour=10, minute=0, second=0, microsecond=0)
    headers = {"Authorization": f"Bearer {token}"}
    hold = client.post("/api/v1/bookings/hold", json={"court_id": court_id, "start_time": start.isoformat(), "end_time": (start + timedelta(hours=1)).isoformat()}, headers=headers)
    assert hold.status_code == status.HTTP_201_CREATED
    booking_id = hold.json()["id"]
    confirmed = client.post(f"/api/v1/bookings/{booking_id}/confirm-payment", headers=headers)
    assert confirmed.status_code == status.HTTP_200_OK
    return booking_id


def create_match(client, booking_id, token, **overrides):
    payload = {"booking_id": booking_id, "title": "Friday Padel", "min_players": 2, "max_players": 4}
    payload.update(overrides)
    response = client.post("/api/v1/matches", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response


def setup_match(client, db_session, visibility="public", join_policy="open", max_players=4, suffix=""):
    _, admin_token = register_user(client, db_session, f"match_admin{suffix}@example.com", UserRole.ADMIN)
    creator_id, creator_token = register_user(client, db_session, f"match_creator{suffix}@example.com")
    court_id = create_court(client, db_session, admin_token)
    booking_id = confirmed_booking(client, court_id, creator_token)
    response = create_match(client, booking_id, creator_token, visibility=visibility, join_policy=join_policy, max_players=max_players)
    return creator_id, creator_token, court_id, booking_id, response.json()


def test_create_match_from_confirmed_own_booking_adds_creator(client, db_session):
    creator_id, _, court_id, booking_id, match = setup_match(client, db_session)
    assert match["booking_id"] == booking_id
    assert match["court"]["id"] == court_id
    assert match["approved_participant_count"] == 1
    participant = db_session.query(MatchParticipant).filter_by(match_id=match["id"], user_id=creator_id).one()
    assert participant.status == ParticipantStatus.APPROVED


def test_match_creation_rejects_other_booking_and_duplicate(client, db_session):
    _, admin_token = register_user(client, db_session, "other_admin@example.com", UserRole.ADMIN)
    _, creator_token = register_user(client, db_session, "booking_owner@example.com")
    _, other_token = register_user(client, db_session, "other_player@example.com")
    booking_id = confirmed_booking(client, create_court(client, db_session, admin_token), creator_token)
    denied = client.post("/api/v1/matches", json={"booking_id": booking_id, "title": "Not mine", "min_players": 2, "max_players": 4}, headers={"Authorization": f"Bearer {other_token}"})
    assert denied.status_code == status.HTTP_403_FORBIDDEN
    create_match(client, booking_id, creator_token)
    duplicate = client.post("/api/v1/matches", json={"booking_id": booking_id, "title": "Duplicate", "min_players": 2, "max_players": 4}, headers={"Authorization": f"Bearer {creator_token}"})
    assert duplicate.status_code == status.HTTP_409_CONFLICT


def test_private_match_hides_details_and_uses_invite_code(client, db_session):
    _, creator_token, _, _, match = setup_match(client, db_session, visibility="private")
    _, player_token = register_user(client, db_session, "private_viewer@example.com")
    assert match["invite_code"]
    public_list = client.get("/api/v1/matches", headers={"Authorization": f"Bearer {player_token}"})
    assert match["id"] not in [item["id"] for item in public_list.json()]
    hidden = client.get(f"/api/v1/matches/{match['id']}", headers={"Authorization": f"Bearer {player_token}"})
    assert hidden.status_code == status.HTTP_404_NOT_FOUND
    joined = client.post("/api/v1/matches/join-by-code", json={"invite_code": match["invite_code"]}, headers={"Authorization": f"Bearer {player_token}"})
    assert joined.status_code == status.HTTP_200_OK
    detail = client.get(f"/api/v1/matches/{match['id']}", headers={"Authorization": f"Bearer {player_token}"})
    assert detail.status_code == status.HTTP_200_OK
    creator_detail = client.get(f"/api/v1/matches/{match['id']}", headers={"Authorization": f"Bearer {creator_token}"})
    assert "invite_code" not in creator_detail.json()


def test_open_join_capacity_duplicate_and_leave_reopens_match(client, db_session):
    _, creator_token, _, _, match = setup_match(client, db_session, max_players=2)
    _, player_token = register_user(client, db_session, "joiner@example.com")
    _, third_token = register_user(client, db_session, "third@example.com")
    headers = {"Authorization": f"Bearer {player_token}"}
    joined = client.post(f"/api/v1/matches/{match['id']}/join", headers=headers)
    assert joined.status_code == status.HTTP_200_OK
    assert joined.json()["status"] == MatchStatus.FULL
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers=headers).status_code == status.HTTP_409_CONFLICT
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers={"Authorization": f"Bearer {third_token}"}).status_code == status.HTTP_409_CONFLICT
    left = client.post(f"/api/v1/matches/{match['id']}/leave", headers=headers)
    assert left.status_code == status.HTTP_200_OK
    assert left.json()["status"] == MatchStatus.OPEN
    assert client.post(f"/api/v1/matches/{match['id']}/leave", headers=headers).status_code == status.HTTP_409_CONFLICT


def test_approval_policy_and_creator_participant_management(client, db_session):
    _, creator_token, _, _, match = setup_match(client, db_session, join_policy="approval_required")
    _, player_token = register_user(client, db_session, "pending_player@example.com")
    _, stranger_token = register_user(client, db_session, "match_stranger@example.com")
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers={"Authorization": f"Bearer {player_token}"}).json()["current_user_participant_status"] == ParticipantStatus.PENDING
    participants = client.get(f"/api/v1/matches/{match['id']}/participants", headers={"Authorization": f"Bearer {creator_token}"}).json()
    pending = next(item for item in participants if item["status"] == ParticipantStatus.PENDING)
    assert client.post(f"/api/v1/matches/{match['id']}/participants/{pending['id']}/approve", headers={"Authorization": f"Bearer {stranger_token}"}).status_code == status.HTTP_403_FORBIDDEN
    approved = client.post(f"/api/v1/matches/{match['id']}/participants/{pending['id']}/approve", headers={"Authorization": f"Bearer {creator_token}"})
    assert approved.status_code == status.HTTP_200_OK
    assert approved.json()["approved_participant_count"] == 2


def test_updates_cancel_and_complete_enforce_permissions_and_time(client, db_session):
    _, creator_token, _, _, match = setup_match(client, db_session)
    _, stranger_token = register_user(client, db_session, "update_stranger@example.com")
    denied = client.patch(f"/api/v1/matches/{match['id']}", json={"title": "Nope"}, headers={"Authorization": f"Bearer {stranger_token}"})
    assert denied.status_code == status.HTTP_403_FORBIDDEN
    updated = client.patch(f"/api/v1/matches/{match['id']}", json={"title": "Updated", "status": "cancelled", "booking_id": 999}, headers={"Authorization": f"Bearer {creator_token}"})
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json()["title"] == "Updated"
    assert updated.json()["status"] == MatchStatus.OPEN
    assert client.post(f"/api/v1/matches/{match['id']}/regenerate-invite-code", headers={"Authorization": f"Bearer {creator_token}"}).status_code == status.HTTP_409_CONFLICT
    assert client.post(f"/api/v1/matches/{match['id']}/complete", headers={"Authorization": f"Bearer {creator_token}"}).status_code == status.HTTP_409_CONFLICT
    match_row = db_session.get(Match, match["id"])
    match_row.start_time = datetime.now(timezone.utc) - timedelta(hours=2)
    match_row.end_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()
    completed = client.post(f"/api/v1/matches/{match['id']}/complete", headers={"Authorization": f"Bearer {creator_token}"})
    assert completed.status_code == status.HTTP_200_OK
    assert completed.json()["status"] == MatchStatus.COMPLETED
    assert client.post(f"/api/v1/matches/{match['id']}/cancel", headers={"Authorization": f"Bearer {creator_token}"}).status_code == status.HTTP_409_CONFLICT


def test_private_code_regeneration_and_booking_cancellation_blocks_join(client, db_session):
    _, creator_token, _, booking_id, match = setup_match(client, db_session, visibility="private")
    _, player_token = register_user(client, db_session, "code_player@example.com")
    regenerated = client.post(f"/api/v1/matches/{match['id']}/regenerate-invite-code", headers={"Authorization": f"Bearer {creator_token}"})
    assert regenerated.status_code == status.HTTP_200_OK
    assert regenerated.json()["invite_code"] != match["invite_code"]
    assert client.post("/api/v1/matches/join-by-code", json={"invite_code": match["invite_code"]}, headers={"Authorization": f"Bearer {player_token}"}).status_code == status.HTTP_404_NOT_FOUND
    booking = db_session.get(Booking, booking_id)
    booking.status = "cancelled"
    db_session.commit()
    blocked = client.post("/api/v1/matches/join-by-code", json=regenerated.json(), headers={"Authorization": f"Bearer {player_token}"})
    assert blocked.status_code == status.HTTP_409_CONFLICT


def test_match_endpoints_require_authentication(client):
    assert client.get("/api/v1/matches").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/v1/matches/join-by-code", json={"invite_code": "x" * 32}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/v1/matches/1/join").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/v1/matches/1/leave").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.patch("/api/v1/matches/1", json={}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/v1/matches/1/cancel").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/v1/matches/1/complete").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/v1/matches/1/regenerate-invite-code").status_code == status.HTTP_401_UNAUTHORIZED


def test_static_match_routes_are_not_parsed_as_match_ids(client, db_session):
    _, token = register_user(client, db_session, "route_player@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/matches/me/created", headers=headers).status_code == status.HTTP_200_OK
    assert client.get("/api/v1/matches/me/joined", headers=headers).status_code == status.HTTP_200_OK
    assert client.post("/api/v1/matches/join-by-code", json={"invite_code": "x" * 32}, headers=headers).status_code == status.HTTP_404_NOT_FOUND


def test_full_approval_match_rejects_new_pending_join(client, db_session):
    _, creator_token, _, _, match = setup_match(client, db_session, join_policy="approval_required", max_players=2)
    _, first_token = register_user(client, db_session, "approval_first@example.com")
    _, second_token = register_user(client, db_session, "approval_second@example.com")
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers={"Authorization": f"Bearer {first_token}"}).status_code == status.HTTP_200_OK
    participant = next(item for item in client.get(f"/api/v1/matches/{match['id']}/participants", headers={"Authorization": f"Bearer {creator_token}"}).json() if item["user_id"] != match["creator"]["id"])
    assert client.post(f"/api/v1/matches/{match['id']}/participants/{participant['id']}/approve", headers={"Authorization": f"Bearer {creator_token}"}).json()["status"] == MatchStatus.FULL
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers={"Authorization": f"Bearer {second_token}"}).status_code == status.HTTP_409_CONFLICT


def test_left_participant_rejoins_same_historical_row(client, db_session):
    _, _, _, _, match = setup_match(client, db_session, max_players=3)
    player_id, player_token = register_user(client, db_session, "rejoin_player@example.com")
    headers = {"Authorization": f"Bearer {player_token}"}
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers=headers).status_code == status.HTTP_200_OK
    participant = db_session.query(MatchParticipant).filter_by(match_id=match["id"], user_id=player_id).one()
    participant_id = participant.id
    assert client.post(f"/api/v1/matches/{match['id']}/leave", headers=headers).status_code == status.HTTP_200_OK
    left_at = db_session.get(MatchParticipant, participant_id).left_at
    rejoined = client.post(f"/api/v1/matches/{match['id']}/join", headers=headers)
    assert rejoined.status_code == status.HTTP_200_OK
    participant = db_session.get(MatchParticipant, participant_id)
    assert participant.status == ParticipantStatus.APPROVED
    assert participant.left_at == left_at
    assert db_session.query(MatchParticipant).filter_by(match_id=match["id"], user_id=player_id).count() == 1


def test_create_ignores_server_owned_fields_and_court_owner_isolated(client, db_session):
    _, admin_token = register_user(client, db_session, "isolation_admin@example.com", UserRole.ADMIN)
    creator_id, creator_token = register_user(client, db_session, "isolation_creator@example.com")
    owner_id, owner_token = register_user(client, db_session, "court_only_owner@example.com", UserRole.OWNER)
    court_id = create_court(client, db_session, admin_token)
    db_session.get(Court, court_id).owner_id = owner_id
    db_session.commit()
    booking_id = confirmed_booking(client, court_id, creator_token)
    response = client.post("/api/v1/matches", json={
        "booking_id": booking_id, "title": "Protected", "min_players": 2, "max_players": 4,
        "creator_id": owner_id, "court_id": 999, "status": "cancelled", "start_time": "2030-01-01T00:00:00Z",
    }, headers={"Authorization": f"Bearer {creator_token}"})
    assert response.status_code == status.HTTP_201_CREATED
    match = response.json()
    assert match["creator"]["id"] == creator_id
    assert match["court"]["id"] == court_id
    assert match["status"] == MatchStatus.OPEN
    assert client.post(f"/api/v1/matches/{match['id']}/cancel", headers={"Authorization": f"Bearer {owner_token}"}).status_code == status.HTTP_403_FORBIDDEN
    assert client.post(f"/api/v1/matches/{match['id']}/cancel", headers={"Authorization": f"Bearer {admin_token}"}).status_code == status.HTTP_200_OK


def test_creation_rejects_pending_booking_and_inactive_court(client, db_session):
    _, admin_token = register_user(client, db_session, "creation_admin@example.com", UserRole.ADMIN)
    _, creator_token = register_user(client, db_session, "creation_player@example.com")
    headers = {"Authorization": f"Bearer {creator_token}"}
    first_court = create_court(client, db_session, admin_token)
    start = (datetime.now(timezone.utc) + timedelta(days=5)).replace(hour=10, minute=0, second=0, microsecond=0)
    pending = client.post("/api/v1/bookings/hold", json={"court_id": first_court, "start_time": start.isoformat(), "end_time": (start + timedelta(hours=1)).isoformat()}, headers=headers)
    rejected = client.post("/api/v1/matches", json={"booking_id": pending.json()["id"], "title": "Pending", "min_players": 2, "max_players": 4}, headers=headers)
    assert rejected.status_code == status.HTTP_409_CONFLICT
    inactive_court = create_court(client, db_session, admin_token)
    inactive_booking = confirmed_booking(client, inactive_court, creator_token)
    db_session.get(Court, inactive_court).is_active = False
    db_session.commit()
    inactive = client.post("/api/v1/matches", json={"booking_id": inactive_booking, "title": "Inactive", "min_players": 2, "max_players": 4}, headers=headers)
    assert inactive.status_code == status.HTTP_409_CONFLICT


def test_pending_participant_can_view_private_match(client, db_session):
    _, _, _, _, match = setup_match(client, db_session, visibility="private", join_policy="approval_required")
    _, player_token = register_user(client, db_session, "private_pending@example.com")
    headers = {"Authorization": f"Bearer {player_token}"}
    joined = client.post("/api/v1/matches/join-by-code", json={"invite_code": match["invite_code"]}, headers=headers)
    assert joined.status_code == status.HTTP_200_OK
    assert joined.json()["current_user_participant_status"] == ParticipantStatus.PENDING
    assert client.get(f"/api/v1/matches/{match['id']}", headers=headers).status_code == status.HTTP_200_OK
