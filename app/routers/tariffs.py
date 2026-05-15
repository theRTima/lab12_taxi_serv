from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models.tariff import Tariff
from app.models.user import User, UserRole
from app.schemas.tariff import TariffCreate, TariffRead, TariffUpdate

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


def _get_tariff_or_404(db: Session, tariff_id: int) -> Tariff:
    tariff = db.get(Tariff, tariff_id)
    if tariff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")
    return tariff


@router.get("/list", response_model=list[TariffRead])
def list_tariffs(db: Annotated[Session, Depends(get_db)]) -> list[Tariff]:
    return db.query(Tariff).all()


@router.get("/{tariff_id}", response_model=TariffRead)
def get_tariff(tariff_id: int, db: Annotated[Session, Depends(get_db)]) -> Tariff:
    return _get_tariff_or_404(db, tariff_id)


@router.post("", response_model=TariffRead, status_code=status.HTTP_201_CREATED)
def create_tariff(
    payload: TariffCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Tariff:
    tariff = Tariff(**payload.model_dump())
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff


@router.patch("/{tariff_id}", response_model=TariffRead)
def update_tariff(
    tariff_id: int,
    payload: TariffUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Tariff:
    tariff = _get_tariff_or_404(db, tariff_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(tariff, key, value)
    db.commit()
    db.refresh(tariff)
    return tariff


@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tariff(
    tariff_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> None:
    tariff = _get_tariff_or_404(db, tariff_id)
    db.delete(tariff)
    db.commit()
