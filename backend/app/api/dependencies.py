from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN] and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only court owners or administrators can perform this action",
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action",
        )
    return current_user


def check_court_owner_or_admin(
    db: Session,
    court_id: int,
    current_user: User,
) -> "Court":  # type: ignore[name-defined]
    """Shared helper: verify court exists and caller owns it (or is admin).

    Importing Court here would create a circular import chain, so we import
    it locally inside the function.
    """
    from app.models.court import Court
    from sqlalchemy import select

    court = db.execute(select(Court).where(Court.id == court_id)).scalar_one_or_none()
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
            detail="Only administrators or court owners can perform this action.",
        )
    return court
