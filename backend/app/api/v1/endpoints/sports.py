from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.sport import SportCreate, SportResponse
from app.services.sport_service import create_sport, get_sport_by_id, get_sports

router = APIRouter()


@router.post("", response_model=SportResponse, status_code=status.HTTP_201_CREATED)
def create_new_sport(
    sport_in: SportCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create a new sport (admin only)."""
    return create_sport(db=db, sport_in=sport_in)


@router.get("", response_model=list[SportResponse])
def list_sports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve list of sports (public)."""
    return get_sports(db=db, skip=skip, limit=limit)


@router.get("/{sport_id}", response_model=SportResponse)
def get_sport(
    sport_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details of a specific sport by ID (public)."""
    sport = get_sport_by_id(db=db, sport_id=sport_id)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sport with id {sport_id} not found",
        )
    return sport
