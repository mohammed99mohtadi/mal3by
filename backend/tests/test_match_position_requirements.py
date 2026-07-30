import pytest
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models.match import Match, MatchPositionRequirement
from tests.test_matches import setup_match


def make_requirement(db_session, match_id, code="goalkeeper", count=1):
    requirement = MatchPositionRequirement(match_id=match_id, position_code=code, required_count=count)
    db_session.add(requirement)
    return requirement


def test_position_requirement_persists_and_relationships_work(client, db_session):
    *_, match = setup_match(client, db_session)
    requirement = make_requirement(db_session, match["id"])
    db_session.commit()
    loaded = db_session.get(MatchPositionRequirement, requirement.id)
    assert loaded.match.id == match["id"]
    assert loaded in db_session.get(Match, match["id"]).position_requirements


def test_multiple_positions_and_same_position_on_different_matches(client, db_session):
    *_, first = setup_match(client, db_session)
    *_, second = setup_match(client, db_session, suffix="_second")
    make_requirement(db_session, first["id"], "goalkeeper")
    make_requirement(db_session, first["id"], "defender", 2)
    make_requirement(db_session, second["id"], "goalkeeper")
    db_session.commit()
    assert db_session.query(MatchPositionRequirement).count() == 3


@pytest.mark.parametrize("code,count", [("goalkeeper", 0), ("goalkeeper", -1), ("", 1), ("   ", 1)])
def test_position_requirement_database_checks(client, db_session, code, count):
    *_, match = setup_match(client, db_session)
    make_requirement(db_session, match["id"], code, count)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_position_for_match_is_rejected(client, db_session):
    *_, match = setup_match(client, db_session)
    make_requirement(db_session, match["id"], "goalkeeper")
    make_requirement(db_session, match["id"], "goalkeeper")
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_match_deletion_is_restricted_by_requirement(client, db_session):
    *_, match = setup_match(client, db_session)
    make_requirement(db_session, match["id"])
    db_session.commit()
    db_session.delete(db_session.get(Match, match["id"]))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_position_requirement_is_registered_in_metadata():
    assert "match_position_requirements" in Base.metadata.tables
