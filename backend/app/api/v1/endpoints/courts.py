from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_owner
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.court import CourtCreate, CourtResponse, CourtUpdate
from app.services.court_service import (
    create_court,
    delete_court,
    get_court_by_id,
    get_courts,
    update_court,
)

router = APIRouter()


@router.post("", response_model=CourtResponse, status_code=status.HTTP_201_CREATED)
def create_new_court(
    court_in: CourtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create a new court (court owner or admin only)."""
    return create_court(db=db, court_in=court_in, owner_id=current_user.id)


@router.get("", response_model=list[CourtResponse])
def list_courts(
    sport_id: int | None = None,
    area: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve list of courts with filtering, search, and pagination (public)."""
    return get_courts(
        db=db,
        sport_id=sport_id,
        area=area,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{court_id}", response_model=CourtResponse)
def get_court(
    court_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details of a court by ID (public)."""
    court = get_court_by_id(db=db, court_id=court_id)
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )
    return court


@router.patch("/{court_id}", response_model=CourtResponse)
def update_existing_court(
    court_id: int,
    court_in: CourtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing court (owner of court or admin only)."""
    court = get_court_by_id(db=db, court_id=court_id)
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    # Permission check: must be court owner or admin
    is_owner = court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this court",
        )

    return update_court(db=db, court=court, court_in=court_in)


@router.delete("/{court_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_court(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a court (owner of court or admin only)."""
    court = get_court_by_id(db=db, court_id=court_id)
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    is_owner = court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this court",
        )

    delete_court(db=db, court=court)
    return None
