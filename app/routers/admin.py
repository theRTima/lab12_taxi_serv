from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.admin import UserAdminRead, UserRoleUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/list", response_model=list[UserAdminRead])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> list[User]:
    return db.query(User).order_by(User.id).all()


@router.patch("/users/{user_id}/role", response_model=UserAdminRead)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
