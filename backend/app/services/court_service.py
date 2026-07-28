from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.court import Court
from app.models.sport import Sport
from app.schemas.court import CourtCreate, CourtUpdate


def get_court_by_id(db: Session, court_id: int) -> Court | None:
    statement = select(Court).options(joinedload(Court.sport)).where(Court.id == court_id)
    return db.execute(statement).scalar_one_or_none()


def get_courts(
    db: Session,
    sport_id: int | None = None,
    area: str | None = None,
    min_price: Decimal | float | None = None,
    max_price: Decimal | float | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Court]:
    query = select(Court).options(joinedload(Court.sport))

    if sport_id is not None:
        query = query.where(Court.sport_id == sport_id)

    if area is not None:
        query = query.where(Court.area.ilike(f"%{area}%"))

    if min_price is not None:
        query = query.where(Court.price_per_hour >= min_price)

    if max_price is not None:
        query = query.where(Court.price_per_hour <= max_price)

    if is_active is not None:
        query = query.where(Court.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Court.name_en.ilike(search_pattern),
                Court.name_ar.ilike(search_pattern),
                Court.area.ilike(search_pattern),
                Court.address.ilike(search_pattern),
            )
        )

    query = query.offset(skip).limit(limit)
    return list(db.execute(query).scalars().all())


def create_court(db: Session, court_in: CourtCreate, owner_id: int) -> Court:
    # Verify sport exists
    sport_stmt = select(Sport).where(Sport.id == court_in.sport_id)
    sport = db.execute(sport_stmt).scalar_one_or_none()
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sport with id {court_in.sport_id} not found.",
        )

    db_court = Court(
        owner_id=owner_id,
        sport_id=court_in.sport_id,
        name_en=court_in.name_en,
        name_ar=court_in.name_ar,
        description_en=court_in.description_en,
        description_ar=court_in.description_ar,
        area=court_in.area,
        address=court_in.address,
        latitude=court_in.latitude,
        longitude=court_in.longitude,
        price_per_hour=court_in.price_per_hour,
        currency=court_in.currency,
        capacity=court_in.capacity,
        image_url=court_in.image_url,
        is_active=court_in.is_active,
    )
    db.add(db_court)
    db.commit()
    db.refresh(db_court)
    return get_court_by_id(db, db_court.id)  # Returns with loaded sport


def update_court(db: Session, court: Court, court_in: CourtUpdate) -> Court:
    update_data = court_in.model_dump(exclude_unset=True)

    if "sport_id" in update_data:
        sport_stmt = select(Sport).where(Sport.id == update_data["sport_id"])
        if not db.execute(sport_stmt).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sport with id {update_data['sport_id']} not found.",
            )

    for field, value in update_data.items():
        setattr(court, field, value)

    db.commit()
    db.refresh(court)
    return get_court_by_id(db, court.id)


def delete_court(db: Session, court: Court) -> None:
    db.delete(court)
    db.commit()
