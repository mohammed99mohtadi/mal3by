from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.models.profile import UserProfile
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.execute(statement).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.execute(statement).scalar_one_or_none()


def register_new_user(db: Session, user_in: UserCreate) -> User:
    """Register a new user. Public registration ALWAYS defaults to PLAYER role."""
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    if user_in.phone_number:
        stmt_phone = select(User).where(User.phone_number == user_in.phone_number)
        if db.execute(stmt_phone).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this phone number already exists.",
            )

    db_user = User(
        email=user_in.email.lower(),
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        phone_number=user_in.phone_number,
        role=UserRole.PLAYER,  # Always PLAYER for public registration
        is_admin=False,        # Always False for public registration
    )
    try:
        db.add(db_user)
        db.flush()
        db.add(UserProfile(user_id=db_user.id, display_name=user_in.full_name))
        db.commit()
        db.refresh(db_user)
    except Exception:
        db.rollback()
        raise
    return db_user


def update_user_role(db: Session, target_user_id: int, new_role: UserRole) -> User:
    """Update user role (Admin only). Protects against demoting the last active administrator."""
    target_user = get_user_by_id(db, target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {target_user_id} not found.",
        )

    is_currently_admin = (target_user.role == UserRole.ADMIN or target_user.is_admin)
    is_demotion = is_currently_admin and (new_role != UserRole.ADMIN)

    if is_demotion:
        # Check active admin count in DB
        admin_count_stmt = select(func.count()).select_from(User).where(
            User.is_active == True,
            or_(User.role == UserRole.ADMIN, User.is_admin == True),
        )
        active_admin_count = db.scalar(admin_count_stmt) or 0

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only remaining active administrator.",
            )

    target_user.role = new_role
    target_user.is_admin = (new_role == UserRole.ADMIN)
    db.commit()
    db.refresh(target_user)
    return target_user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
