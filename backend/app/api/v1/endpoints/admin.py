from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserRoleUpdate
from app.services.auth_service import update_user_role

router = APIRouter()


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Update user role (Admin only)."""
    updated_user = update_user_role(db=db, target_user_id=user_id, new_role=role_update.role)
    return updated_user
