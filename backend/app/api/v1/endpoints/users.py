from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import PreferredLanguageUpdate, UserProfileResponse
from app.schemas.user import UserResponse
from app.services.profile_service import get_profile, set_preferred_language
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Retrieve authenticated current user profile."""
    return current_user


@router.get("/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return get_profile(current_user)


@router.patch("/me/profile/language", response_model=UserProfileResponse)
def update_my_language(
    payload: PreferredLanguageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return set_preferred_language(db, current_user, payload.preferred_language)
