from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.user import User


def get_profile(user: User) -> UserProfile:
    return user.profile


def set_preferred_language(db: Session, user: User, language: str) -> UserProfile:
    profile = user.profile
    profile.preferred_language = language
    db.commit()
    db.refresh(profile)
    return profile
