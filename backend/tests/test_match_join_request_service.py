import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.match import (
    MatchJoinPolicy,
    MatchJoinRequest,
    MatchJoinRequestStatus,
    MatchParticipant,
    MatchPositionRequirement,
    MatchStatus,
    ParticipantStatus,
)
from app.models.user import User, UserRole
from app.services.match_service import approve_join_request, create_join_request, reject_join_request, withdraw_join_request
from tests.test_matches import register_user, setup_match


def make_service_match_and_users(client, db_session, suffix="", join_policy=MatchJoinPolicy.APPROVAL_REQUIRED):
    *_, match_dict = setup_match(client, db_session, suffix=f"_svc{suffix}")
    from app.services.match_service import get_match
    match = get_match(db_session, match_dict["id"])
    match.join_policy = join_policy
    db_session.commit()

    player1_id, _ = register_user(client, db_session, f"svc_player1{suffix}@example.com")
    player2_id, _ = register_user(client, db_session, f"svc_player2{suffix}@example.com")
    admin_id, _ = register_user(client, db_session, f"svc_admin{suffix}@example.com")
    admin = db_session.get(User, admin_id)
    admin.role = UserRole.ADMIN
    db_session.commit()

    player1 = db_session.get(User, player1_id)
    player2 = db_session.get(User, player2_id)
    creator = db_session.get(User, match.creator_id)

    return match, creator, player1, player2, admin


def test_create_join_request_success_without_position(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_no_pos")

    req = create_join_request(db_session, match.id, player1)
    assert req.id is not None
    assert req.match_id == match.id
    assert req.user_id == player1.id
    assert req.status == MatchJoinRequestStatus.PENDING
    assert req.requested_position_code is None
    assert req.reviewed_by_user_id is None
    assert req.reviewed_at is None


def test_create_join_request_success_with_normalized_position(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_pos")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    req = create_join_request(db_session, match.id, player1, position_code="  goalkeeper  ")
    assert req.requested_position_code == "goalkeeper"


def test_create_join_request_rejection_for_open_policy(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_open_pol", join_policy=MatchJoinPolicy.OPEN)

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Match does not require approval to join"


def test_create_join_request_rejection_for_creator(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_creator")

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Match creator cannot create a join request for their own match"


def test_create_join_request_rejection_for_approved_participant(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_approved_part")
    participant = MatchParticipant(match_id=match.id, user_id=player1.id, status=ParticipantStatus.APPROVED)
    db_session.add(participant)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "You are already an approved participant in this match"


def test_create_join_request_rejection_for_duplicate_pending(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_dup_pending")
    create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "You already have a pending join request for this match"


def test_create_join_request_rejection_for_invalid_position(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_inv_pos")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        create_join_request(db_session, match.id, player1, position_code="forward")
    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc.value.detail == "Requested position is not available for this match"


def test_pending_requests_do_not_consume_position_capacity(client, db_session):
    match, creator, player1, player2, _ = make_service_match_and_users(client, db_session, suffix="_pending_cap")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    req1 = create_join_request(db_session, match.id, player1, position_code="goalkeeper")
    assert req1.status == MatchJoinRequestStatus.PENDING

    req2 = create_join_request(db_session, match.id, player2, position_code="goalkeeper")
    assert req2.status == MatchJoinRequestStatus.PENDING


def test_withdraw_join_request_success_by_owner(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_ok")
    req = create_join_request(db_session, match.id, player1)

    withdrawn = withdraw_join_request(db_session, req.id, player1)
    assert withdrawn.status == MatchJoinRequestStatus.WITHDRAWN
    assert withdrawn.reviewed_by_user_id is None
    assert withdrawn.reviewed_at is None


def test_withdraw_join_request_rejection_by_non_owner(client, db_session):
    match, creator, player1, player2, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_403")
    req = create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        withdraw_join_request(db_session, req.id, player2)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "You can only withdraw your own join request"


def test_withdraw_join_request_rejection_for_non_pending(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_non_pending")
    req = create_join_request(db_session, match.id, player1)
    req.status = MatchJoinRequestStatus.WITHDRAWN
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        withdraw_join_request(db_session, req.id, player1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Only pending join requests can be withdrawn"


def test_withdraw_join_request_missing_returns_404(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_withdraw_404")

    with pytest.raises(HTTPException) as exc:
        withdraw_join_request(db_session, 99999, player1)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Join request not found"


def test_approve_join_request_success_by_creator_and_populates_fields(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_app_creator")
    req = create_join_request(db_session, match.id, player1)

    approved = approve_join_request(db_session, req.id, creator)
    assert approved.status == MatchJoinRequestStatus.APPROVED
    assert approved.reviewed_by_user_id == creator.id
    assert approved.reviewed_at is not None

    participant = next((p for p in match.participants if p.user_id == player1.id), None)
    assert participant is not None
    assert participant.status == ParticipantStatus.APPROVED
    assert participant.approved_at is not None


def test_approve_join_request_success_by_admin(client, db_session):
    match, creator, player1, _, admin = make_service_match_and_users(client, db_session, suffix="_app_admin")
    req = create_join_request(db_session, match.id, player1)

    approved = approve_join_request(db_session, req.id, admin)
    assert approved.status == MatchJoinRequestStatus.APPROVED
    assert approved.reviewed_by_user_id == admin.id


def test_approve_join_request_rejection_by_non_manager_returns_403(client, db_session):
    match, creator, player1, player2, _ = make_service_match_and_users(client, db_session, suffix="_app_403")
    req = create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        approve_join_request(db_session, req.id, player2)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Only the match creator or an administrator can manage this match"


def test_approve_join_request_rejection_for_non_pending_returns_409(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_app_non_pending")
    req = create_join_request(db_session, match.id, player1)
    req.status = MatchJoinRequestStatus.WITHDRAWN
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        approve_join_request(db_session, req.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Only pending join requests can be approved"


def test_approve_join_request_missing_returns_404(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_app_404")

    with pytest.raises(HTTPException) as exc:
        approve_join_request(db_session, 99999, creator)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Join request not found"


def test_approve_join_request_reuses_existing_left_participant(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_app_reuse")
    part = MatchParticipant(match_id=match.id, user_id=player1.id, status=ParticipantStatus.LEFT)
    db_session.add(part)
    db_session.commit()

    req = create_join_request(db_session, match.id, player1)
    approved = approve_join_request(db_session, req.id, creator)

    assert approved.status == MatchJoinRequestStatus.APPROVED
    assert part.status == ParticipantStatus.APPROVED
    assert part.left_at is None


def test_approve_join_request_already_approved_participant_returns_409(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_app_already")
    part = MatchParticipant(match_id=match.id, user_id=player1.id, status=ParticipantStatus.APPROVED)
    db_session.add(part)

    # Insert pending request manually bypassing create_join_request check
    req = MatchJoinRequest(match_id=match.id, user_id=player1.id, status=MatchJoinRequestStatus.PENDING)
    db_session.add(req)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        approve_join_request(db_session, req.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "User is already an approved participant in this match"


def test_approve_join_request_final_slot_updates_match_status_to_full(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_app_full_slot")
    match.max_players = 2  # creator (1) + player1 (1) = 2 (full)
    db_session.commit()

    req = create_join_request(db_session, match.id, player1)
    approve_join_request(db_session, req.id, creator)

    assert match.status == MatchStatus.FULL


def test_approve_join_request_full_match_returns_409(client, db_session):
    match, creator, player1, player2, _ = make_service_match_and_users(client, db_session, suffix="_app_full_match")
    # Match has min_players=2, max_players=2. Creator is spot 1, player2 is spot 2 (2/2 full).
    match.max_players = 2
    part2 = MatchParticipant(match_id=match.id, user_id=player2.id, status=ParticipantStatus.APPROVED)
    db_session.add(part2)
    db_session.commit()

    req = create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        approve_join_request(db_session, req.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Match is full"


def test_approve_join_request_enforces_position_capacity(client, db_session):
    match, creator, player1, player2, _ = make_service_match_and_users(client, db_session, suffix="_app_pos_cap")
    pos_req = MatchPositionRequirement(match_id=match.id, position_code="goalkeeper", required_count=1)
    db_session.add(pos_req)
    db_session.commit()

    req1 = create_join_request(db_session, match.id, player1, position_code="goalkeeper")
    req2 = create_join_request(db_session, match.id, player2, position_code="goalkeeper")

    approve_join_request(db_session, req1.id, creator)

    with pytest.raises(HTTPException) as exc:
        approve_join_request(db_session, req2.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Requested position is at full capacity"


def test_reject_join_request_success_by_manager(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_rej_ok")
    req = create_join_request(db_session, match.id, player1)

    rejected = reject_join_request(db_session, req.id, creator)
    assert rejected.status == MatchJoinRequestStatus.REJECTED
    assert rejected.reviewed_by_user_id == creator.id
    assert rejected.reviewed_at is not None

    # Verify roster is NOT altered
    participant = next((p for p in match.participants if p.user_id == player1.id), None)
    assert participant is None


def test_reject_join_request_rejection_by_non_manager_returns_403(client, db_session):
    match, creator, player1, player2, _ = make_service_match_and_users(client, db_session, suffix="_rej_403")
    req = create_join_request(db_session, match.id, player1)

    with pytest.raises(HTTPException) as exc:
        reject_join_request(db_session, req.id, player2)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Only the match creator or an administrator can manage this match"


def test_reject_join_request_rejection_for_non_pending_returns_409(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_rej_non_pending")
    req = create_join_request(db_session, match.id, player1)
    req.status = MatchJoinRequestStatus.WITHDRAWN
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        reject_join_request(db_session, req.id, creator)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Only pending join requests can be rejected"


def test_reject_join_request_missing_returns_404(client, db_session):
    match, creator, player1, _, _ = make_service_match_and_users(client, db_session, suffix="_rej_404")

    with pytest.raises(HTTPException) as exc:
        reject_join_request(db_session, 99999, creator)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Join request not found"
