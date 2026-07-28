from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sport import Sport
from app.schemas.sport import SportCreate, SportUpdate


def get_sport_by_id(db: Session, sport_id: int) -> Sport | None:
    statement = select(Sport).where(Sport.id == sport_id)
    return db.execute(statement).scalar_one_or_none()


def get_sport_by_slug(db: Session, slug: str) -> Sport | None:
    statement = select(Sport).where(Sport.slug == slug.lower())
    return db.execute(statement).scalar_one_or_none()


def get_sports(db: Session, skip: int = 0, limit: int = 100) -> list[Sport]:
    statement = select(Sport).offset(skip).limit(limit)
    return list(db.execute(statement).scalars().all())


def create_sport(db: Session, sport_in: SportCreate) -> Sport:
    existing = get_sport_by_slug(db, sport_in.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sport with slug '{sport_in.slug}' already exists.",
        )

    db_sport = Sport(
        name_en=sport_in.name_en,
        name_ar=sport_in.name_ar,
        slug=sport_in.slug.lower(),
        icon=sport_in.icon,
        is_active=sport_in.is_active,
    )
    db.add(db_sport)
    db.commit()
    db.refresh(db_sport)
    return db_sport
