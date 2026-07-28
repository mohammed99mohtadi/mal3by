from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.sport import Sport

DEFAULT_SPORTS = [
    {
        "slug": "football",
        "name_en": "Football",
        "name_ar": "كرة القدم",
        "icon": "soccer-ball",
    },
    {
        "slug": "padel",
        "name_en": "Padel",
        "name_ar": "بادل",
        "icon": "padel-racket",
    },
    {
        "slug": "tennis",
        "name_en": "Tennis",
        "name_ar": "كرة المضرب",
        "icon": "tennis-ball",
    },
    {
        "slug": "basketball",
        "name_en": "Basketball",
        "name_ar": "كرة السلة",
        "icon": "basketball",
    },
]


def seed_sports(db: Session) -> list[Sport]:
    """Seed initial sports into the database idempotently."""
    created_sports = []
    for sport_data in DEFAULT_SPORTS:
        stmt = select(Sport).where(Sport.slug == sport_data["slug"])
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            sport = Sport(
                slug=sport_data["slug"],
                name_en=sport_data["name_en"],
                name_ar=sport_data["name_ar"],
                icon=sport_data["icon"],
                is_active=True,
            )
            db.add(sport)
            created_sports.append(sport)
    db.commit()
    return created_sports


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        added = seed_sports(session)
        print(f"Seeding completed. Added {len(added)} new sports.")
