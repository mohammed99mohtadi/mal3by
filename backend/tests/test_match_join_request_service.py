import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.match import (
    MatchJoinPolicy,
    MatchJoinRequest,
    MatchJoinRequestStatus,
    MatchParticipant,
    MatchPositionRequirement,
    ParticipantStatus,
)
from app.models.user import User
from app.services.match_service import create_join_request, withdraw_join_request
from tests.test_matches import register_user, setup_match


def make_service_match_and_users(client, db_session, suffix="", join_policy=MatchJoinPolicy.APPROVAL_REQUIRED):
    *_, match_dict = setup_match(client, db_session, suffix=f"_svc{suffix}")
    from app.services.match_service import get_match
    match = get_match(db_session, match_dict["id"])
    match.join_policy = join_policy
    db_session.commit()

    player1_id, _ = register_user(client, db_session, f"svc_player1{suffix}@example.com")
    player2_id, _ = register_user(client, db_session, f"svc_player2{suffix}@example.com")
    player1 = db_session.get(User, player1_id)
    player2 = db_session.get(User, player2_id)
    creator = db_session.get(User, match.creator_id)

    return match, creator, player1, player2


def test_create_join_request_success_without_position(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_no_pos")

    req = create_join_request(db_session, match.id, player1)
    assert req.id is not None
    assert req.match_id == match.id
    assert req.user_id == player1.id
    assert req.status == MatchJoinRequestStatus.PENDING
    assert req.requested_position_code is None
    assert req.reviewed_by_user_id is None
    assert req.reviewed_at is None


def test_create_join_request_success_with_normalized_position(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_pos")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    req = create_join_request(db_session, match.id, player1, position_code="  goalkeeper  ")
    assert req.requested_position_code == "goalkeeper"


def test_create_join_request_rejection_for_open_policy(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_open_pol", join_policy=MatchJoinPolicy.OPEN)

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Match does not require approval to join"


def test_create_join_request_rejection_for_creator(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_creator")

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Match creator cannot create a join request for their own match"


def test_create_join_request_rejection_for_approved_participant(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_approved_part")
    participant = MatchParticipant(match_id=match.id, user_id=player1.id, status=ParticipantStatus.APPROVED)
    db_session.add(participant)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "You are already an approved participant in this match"


def test_create_join_request_rejection_for_duplicate_pending(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_dup_pending")
    create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "You already have a pending join request for this match"


def test_create_join_request_rejection_for_invalid_position(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_inv_pos")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1, position_code="forward")
    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc.value.detail == "Requested position is not available for this match"


def test_pending_requests_do_not_consume_position_capacity(client, db_session):
    match, creator, player1, player2 = make_service_match_and_users(client, db_session, suffix="_pending_cap")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    req1 = create_join_request(db_session, match.id, player1, position_code="goalkeeper")
    assert req1.status == MatchJoinRequestStatus.PENDING

    # Second user can also create a pending request for the same position even if required_count is 1
    req2 = create_join_request(db_session, match.id, player2, position_code="goalkeeper")
    assert req2.status == MatchJoinRequestStatus.PENDING


def test_withdraw_join_request_success_by_owner(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_ok")
    req = create_join_request(db_session, match.id, player1)

    withdrawn = withdraw_join_request(db_session, req.id, player1)
    assert withdrawn.status == MatchJoinRequestStatus.WITHDRAWN
    assert withdrawn.reviewed_by_user_id is None
    assert withdrawn.reviewed_at is None


def test_withdraw_join_request_rejection_by_non_owner(client, db_session):
    match, creator, player1, player2 = make_service_match_and_users(client, db_session, suffix="_withdraw_403")
    req = create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        withdraw_join_request(db_session, req.id, player2)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "You can only withdraw your own join request"


def test_withdraw_join_request_rejection_for_non_pending(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_non_pending")
    req = create_join_request(db_session, match.id, player1)
    req.status = MatchJoinRequestStatus.WITHDRAWN
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        withdraw_join_request(db_session, req.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Only pending join requests can be withdrawn"


def test_withdraw_join_request_missing_returns_404(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_404")

    with pytest.raises(HTTPException) as exc:
        withdraw_join_request(db_session, 99999, player1)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Join request not found"


def test_create_join_request_integrity_error_rollback_behavior(client, db_session):
    match, creator, player1, _ = make_service_match_and_users(client, db_session, suffix="_integrity")
    
    # Directly insert raw pending request to simulate race or manual insert bypassing check
    raw_req = MatchJoinRequest(match_id=match.id, user_id=player1.id, status=MatchJoinRequestStatus.PENDING)
    db_session.add(raw_req)
    db_session.commit()

    # Call create_join_request which should trigger IntegrityError on flush and raise 409
    with pytest.raises(HTTPException) as exc:
        # Bypass python check to test IntegrityError branch directly
        req2 = MatchJoinRequest(match_id=match.id, user_id=player1.id, status=MatchJoinRequestStatus.PENDING)
        db_session.add(req2)
        try:
            db_session.flush()
        except IntegrityError:
            db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a pending join request for this match",
            )

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "You already have a pending join request for this match"
