import pytest
from fastapi import HTTPException, status

from app.models.match import MatchJoinRequest, MatchJoinRequestStatus, MatchParticipant, MatchPositionRequirement, ParticipantStatus
from app.services.match_service import (
    _approved_position_count,
    _ensure_position_capacity,
    _get_join_request,
    _has_active_join_request,
    _pending_join_request_count,
    _validate_requested_position,
)
from tests.test_matches import register_user, setup_match


def make_helper_match_and_requester(client, db_session, suffix=""):
    *_, match = setup_match(client, db_session, suffix=f"_helper{suffix}")
    requester_id, _ = register_user(client, db_session, f"helper_player{suffix}@example.com")
    return match, requester_id


def test_get_join_request_retrieves_request_and_supports_locking(client, db_session):
    match, requester_id = make_helper_match_and_requester(client, db_session, suffix="_get")
    req = MatchJoinRequest(match_id=match["id"], user_id=requester_id, status=MatchJoinRequestStatus.PENDING)
    db_session.add(req)
    db_session.commit()

    loaded = _get_join_request(db_session, req.id)
    assert loaded is not None
    assert loaded.id == req.id

    locked = _get_join_request(db_session, req.id, lock=True)
    assert locked is not None
    assert locked.id == req.id

    assert _get_join_request(db_session, 99999) is None


def test_pending_join_request_count_filters_by_match_and_pending_status(client, db_session):
    match, requester_id1 = make_helper_match_and_requester(client, db_session, suffix="_count1")
    requester_id2, _ = register_user(client, db_session, "helper_player_count2@example.com")

    req1 = MatchJoinRequest(match_id=match["id"], user_id=requester_id1, status=MatchJoinRequestStatus.PENDING)
    req2 = MatchJoinRequest(match_id=match["id"], user_id=requester_id2, status=MatchJoinRequestStatus.REJECTED)
    db_session.add_all([req1, req2])
    db_session.commit()

    assert _pending_join_request_count(db_session, match["id"]) == 1


def test_has_active_join_request_detects_pending_request(client, db_session):
    match, requester_id = make_helper_match_and_requester(client, db_session, suffix="_active")
    assert _has_active_join_request(db_session, match["id"], requester_id) is False

    req = MatchJoinRequest(match_id=match["id"], user_id=requester_id, status=MatchJoinRequestStatus.PENDING)
    db_session.add(req)
    db_session.commit()

    assert _has_active_join_request(db_session, match["id"], requester_id) is True

    req.status = MatchJoinRequestStatus.APPROVED
    db_session.commit()
    assert _has_active_join_request(db_session, match["id"], requester_id) is False


def test_validate_requested_position_normalizes_whitespace_and_validates(client, db_session):
    match, _ = make_helper_match_and_requester(client, db_session, suffix="_pos_val")
    pos_req = MatchPositionRequirement(match_id=match["id"], position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    assert _validate_requested_position(db_session, match["id"], None) is None
    assert _validate_requested_position(db_session, match["id"], "goalkeeper") == "goalkeeper"
    assert _validate_requested_position(db_session, match["id"], "  goalkeeper  ") == "goalkeeper"

    with pytest.raises(HTTPException) as exc_empty:
        _validate_requested_position(db_session, match["id"], "   ")
    assert exc_empty.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    with pytest.raises(HTTPException) as exc_invalid:
        _validate_requested_position(db_session, match["id"], "striker")
    assert exc_invalid.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_approved_position_count_counts_distinct_users_exactly_once(client, db_session):
    match, user_id1 = make_helper_match_and_requester(client, db_session, suffix="_distinct1")
    user_id2, _ = register_user(client, db_session, "helper_player_distinct2@example.com")

    # User 1: Has multiple APPROVED requests (e.g., historical re-joins) but single active APPROVED participant
    req1a = MatchJoinRequest(match_id=match["id"], user_id=user_id1, status=MatchJoinRequestStatus.APPROVED, requested_position_code="goalkeeper")
    req1b = MatchJoinRequest(match_id=match["id"], user_id=user_id1, status=MatchJoinRequestStatus.APPROVED, requested_position_code="goalkeeper")
    participant1 = MatchParticipant(match_id=match["id"], user_id=user_id1, status=ParticipantStatus.APPROVED)

    # User 2: Active APPROVED request and participant for same position
    req2 = MatchJoinRequest(match_id=match["id"], user_id=user_id2, status=MatchJoinRequestStatus.APPROVED, requested_position_code="goalkeeper")
    participant2 = MatchParticipant(match_id=match["id"], user_id=user_id2, status=ParticipantStatus.APPROVED)

    db_session.add_all([req1a, req1b, participant1, req2, participant2])
    db_session.commit()

    # Must count 2 distinct users, NOT 3 rows
    assert _approved_position_count(db_session, match["id"], "goalkeeper") == 2
    assert _approved_position_count(db_session, match["id"], "  goalkeeper  ") == 2


def test_ensure_position_capacity_not_prematurely_reached_by_duplicate_records(client, db_session):
    match, user_id = make_helper_match_and_requester(client, db_session, suffix="_capacity_dup")
    pos_req = MatchPositionRequirement(match_id=match["id"], position_code="goalkeeper", required_count=2)
    db_session.add(pos_req)

    # User has 2 approved requests (historical) and 1 participant record
    req1 = MatchJoinRequest(match_id=match["id"], user_id=user_id, status=MatchJoinRequestStatus.APPROVED, requested_position_code="goalkeeper")
    req2 = MatchJoinRequest(match_id=match["id"], user_id=user_id, status=MatchJoinRequestStatus.APPROVED, requested_position_code="goalkeeper")
    participant = MatchParticipant(match_id=match["id"], user_id=user_id, status=ParticipantStatus.APPROVED)

    db_session.add_all([req1, req2, participant])
    db_session.commit()

    # Capacity is 2, distinct user count is 1. Position must NOT be marked full.
    _ensure_position_capacity(db_session, match["id"], "goalkeeper")

    # Add second distinct user participant to fill capacity (2/2)
    user_id2, _ = register_user(client, db_session, "helper_player_cap_fill@example.com")
    req3 = MatchJoinRequest(match_id=match["id"], user_id=user_id2, status=MatchJoinRequestStatus.APPROVED, requested_position_code="goalkeeper")
    participant2 = MatchParticipant(match_id=match["id"], user_id=user_id2, status=ParticipantStatus.APPROVED)
    db_session.add_all([req3, participant2])
    db_session.commit()

    # Now position is at full capacity (2/2)
    with pytest.raises(HTTPException) as exc:
        _ensure_position_capacity(db_session, match["id"], "goalkeeper")
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Requested position is at full capacity"
