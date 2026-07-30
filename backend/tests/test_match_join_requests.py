import pytest
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models.match import Match, MatchJoinRequest, MatchJoinRequestStatus, MatchParticipant
from app.models.user import User
from tests.test_matches import register_user, setup_match


def make_request(db_session, match_id, user_id, *, status=MatchJoinRequestStatus.PENDING, position_code=None, reviewer_id=None):
    request = MatchJoinRequest(
        match_id=match_id,
        user_id=user_id,
        status=status,
        requested_position_code=position_code,
        reviewed_by_user_id=reviewer_id,
    )
    db_session.add(request)
    return request


def make_match_and_requester(client, db_session, suffix=""):
    *_, match = setup_match(client, db_session, suffix=f"_join_request{suffix}")
    requester_id, _ = register_user(client, db_session, f"join_request_player{suffix}@example.com")
    return match, requester_id


def test_join_request_is_registered_and_persists_with_match_and_requester_relationships(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session)
    request = make_request(db_session, match["id"], requester_id)
    db_session.commit()

    loaded = db_session.get(MatchJoinRequest, request.id)
    assert "match_join_requests" in Base.metadata.tables
    assert loaded.status == MatchJoinRequestStatus.PENDING
    assert loaded.match.id == match["id"]
    assert loaded in db_session.get(Match, match["id"]).join_requests
    assert loaded.requester.id == requester_id


def test_reviewed_by_relationship_and_null_are_supported(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session)
    reviewer_id, _ = register_user(client, db_session, "join_request_reviewer@example.com")
    reviewed = make_request(db_session, match["id"], requester_id, status=MatchJoinRequestStatus.APPROVED, reviewer_id=reviewer_id)
    unreviewed = make_request(db_session, match["id"], requester_id, status=MatchJoinRequestStatus.REJECTED)
    db_session.commit()

    assert db_session.get(MatchJoinRequest, reviewed.id).reviewed_by.id == reviewer_id
    assert db_session.get(MatchJoinRequest, unreviewed.id).reviewed_by is None


@pytest.mark.parametrize("status", list(MatchJoinRequestStatus))
def test_all_allowed_statuses_persist(client, db_session, status):
    match, requester_id = make_match_and_requester(client, db_session, suffix=f"_{status.value}")
    request = make_request(db_session, match["id"], requester_id, status=status)
    db_session.commit()
    assert db_session.get(MatchJoinRequest, request.id).status == status


def test_invalid_status_is_rejected(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session, suffix="_invalid")
    make_request(db_session, match["id"], requester_id, status="invalid")
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_valid_and_null_requested_position_codes_persist(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session, suffix="_positions")
    valid = make_request(db_session, match["id"], requester_id, position_code="goalkeeper")
    null = make_request(db_session, match["id"], requester_id, status=MatchJoinRequestStatus.REJECTED)
    db_session.commit()
    assert db_session.get(MatchJoinRequest, valid.id).requested_position_code == "goalkeeper"
    assert db_session.get(MatchJoinRequest, null.id).requested_position_code is None


@pytest.mark.parametrize("position_code", ["", "   "])
def test_empty_requested_position_codes_are_rejected(client, db_session, position_code):
    match, requester_id = make_match_and_requester(client, db_session, suffix=f"_empty{len(position_code)}")
    make_request(db_session, match["id"], requester_id, position_code=position_code)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_historical_requests_are_not_broadly_unique(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session, suffix="_history")
    for status in (MatchJoinRequestStatus.REJECTED, MatchJoinRequestStatus.REJECTED, MatchJoinRequestStatus.WITHDRAWN, MatchJoinRequestStatus.WITHDRAWN):
        make_request(db_session, match["id"], requester_id, status=status)
    db_session.commit()
    assert db_session.query(MatchJoinRequest).filter_by(match_id=match["id"], user_id=requester_id).count() == 4


def test_sqlite_partial_index_rejects_duplicate_pending_requests(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session, suffix="_pending")
    make_request(db_session, match["id"], requester_id)
    db_session.commit()
    make_request(db_session, match["id"], requester_id)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_join_request_does_not_change_confirmed_participants(client, db_session):
    match, requester_id = make_match_and_requester(client, db_session, suffix="_participants")
    before = db_session.query(MatchParticipant).filter_by(match_id=match["id"]).count()
    make_request(db_session, match["id"], requester_id)
    db_session.commit()
    assert db_session.query(MatchParticipant).filter_by(match_id=match["id"]).count() == before


def test_foreign_key_deletion_behaviour_when_sqlite_enforces_foreign_keys(client, db_session):
    if db_session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() != 1:
        pytest.skip("SQLite foreign-key enforcement is disabled in shared test fixture")

    match, requester_id = make_match_and_requester(client, db_session, suffix="_foreign_keys")
    reviewer_id, _ = register_user(client, db_session, "join_request_fk_reviewer@example.com")
    request = make_request(db_session, match["id"], requester_id, status=MatchJoinRequestStatus.REJECTED, reviewer_id=reviewer_id)
    db_session.commit()

    db_session.delete(db_session.get(Match, match["id"]))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.delete(db_session.get(User, reviewer_id))
    db_session.commit()
    assert db_session.get(MatchJoinRequest, request.id).reviewed_by_user_id is None
