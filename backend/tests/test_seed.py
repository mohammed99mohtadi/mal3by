from app.db.seed import seed_sports
from app.models.sport import Sport


def test_seed_sports_idempotent(db_session):
    # Initial seed
    added1 = seed_sports(db_session)
    assert len(added1) == 4

    slugs = [s.slug for s in added1]
    assert "football" in slugs
    assert "padel" in slugs
    assert "tennis" in slugs
    assert "basketball" in slugs

    # Second seed run -> 0 new sports added
    added2 = seed_sports(db_session)
    assert len(added2) == 0

    all_sports = db_session.query(Sport).all()
    assert len(all_sports) == 4
