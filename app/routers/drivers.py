from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models.driver import Driver
from app.models.user import User, UserRole
from app.schemas.driver import (
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverRead,
    DriverUpdate,
)

router = APIRouter(prefix="/drivers", tags=["drivers"])


def _get_driver_or_404(db: Session, driver_id: int) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


def _get_driver_for_user(db: Session, user: User) -> Driver:
    driver = db.query(Driver).filter(Driver.user_id == user.id).first()
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found",
        )
    return driver


@router.get("/me", response_model=DriverRead)
def get_my_driver(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.DRIVER))],
) -> Driver:
    return _get_driver_for_user(db, current_user)


@router.patch("/me", response_model=DriverRead)
def update_my_availability(
    payload: DriverAvailabilityUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.DRIVER))],
) -> Driver:
    driver = _get_driver_for_user(db, current_user)
    driver.is_available = payload.is_available
    db.commit()
    db.refresh(driver)
    return driver


@router.get("/list", response_model=list[DriverRead])
def list_drivers(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Driver]:
    return db.query(Driver).all()


@router.get("/{driver_id}", response_model=DriverRead)
def get_driver(
    driver_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Driver:
    return _get_driver_or_404(db, driver_id)


@router.post("", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Driver:
    if db.query(Driver).filter(Driver.user_id == payload.user_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver profile already exists for this user",
        )
    driver = Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.patch("/{driver_id}", response_model=DriverRead)
def update_driver(
    driver_id: int,
    payload: DriverUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Driver:
    driver = _get_driver_or_404(db, driver_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(driver, key, value)
    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    driver_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> None:
    driver = _get_driver_or_404(db, driver_id)
    db.delete(driver)
    db.commit()
