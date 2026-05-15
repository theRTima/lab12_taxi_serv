from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models.driver import Driver
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.models.tariff import Tariff
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


def _get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def _can_read_order(user: User, order: Order, db: Session) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.CLIENT and order.client_id == user.id:
        return True
    if user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if driver is None:
            return False
        if order.driver_id == driver.id:
            return True
        return order.driver_id is None and order.status == OrderStatus.PENDING
    return False


@router.get("/list", response_model=list[OrderRead])
def list_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Order]:
    query = db.query(Order)
    if current_user.role == UserRole.CLIENT:
        query = query.filter(Order.client_id == current_user.id)
    elif current_user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if driver is None:
            return []
        query = query.filter(
            or_(
                Order.driver_id == driver.id,
                (Order.driver_id.is_(None)) & (Order.status == OrderStatus.PENDING),
            )
        )
    return query.order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Order:
    order = _get_order_or_404(db, order_id)
    if not _can_read_order(current_user, order, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return order


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.CLIENT))],
) -> Order:
    tariff = db.get(Tariff, payload.tariff_id)
    if tariff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")

    order = Order(
        client_id=current_user.id,
        tariff_id=payload.tariff_id,
        pickup=payload.pickup,
        destination=payload.destination,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Order:
    order = _get_order_or_404(db, order_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.CLIENT) or (
        current_user.role == UserRole.CLIENT and order.client_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if order.status not in (OrderStatus.PENDING, OrderStatus.ASSIGNED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be updated in current status",
        )

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Order:
    order = _get_order_or_404(db, order_id)

    if current_user.role == UserRole.CLIENT:
        if order.client_id != current_user.id or payload.status != OrderStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        order.status = OrderStatus.CANCELLED
        db.commit()
        db.refresh(order)
        return order

    if current_user.role not in (UserRole.DRIVER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if driver is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver profile not found")
        if order.driver_id is not None and order.driver_id != driver.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
        if payload.driver_id is not None and payload.driver_id != driver.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign another driver")
        order.driver_id = driver.id
    elif payload.driver_id is not None:
        order.driver_id = payload.driver_id

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    order = _get_order_or_404(db, order_id)
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.CLIENT and order.client_id == current_user.id:
        if order.status not in (OrderStatus.PENDING, OrderStatus.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or cancelled orders can be deleted",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(order)
    db.commit()
