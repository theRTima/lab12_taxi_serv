from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate

router = APIRouter(prefix="/payments", tags=["payments"])


def _get_payment_or_404(db: Session, payment_id: int) -> Payment:
    payment = (
        db.query(Payment)
        .options(joinedload(Payment.order))
        .filter(Payment.id == payment_id)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


def _can_read_payment(user: User, payment: Payment) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    return payment.order.client_id == user.id


@router.get("", response_model=list[PaymentRead])
def list_payments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Payment]:
    query = db.query(Payment).options(joinedload(Payment.order))
    if current_user.role != UserRole.ADMIN:
        query = query.join(Order).filter(Order.client_id == current_user.id)
    return query.all()


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Payment:
    payment = _get_payment_or_404(db, payment_id)
    if not _can_read_payment(current_user, payment):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return payment


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.CLIENT))],
) -> Payment:
    order = db.get(Order, payload.order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    if db.query(Payment).filter(Payment.order_id == payload.order_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already exists for this order",
        )

    payment = Payment(order_id=payload.order_id, amount=payload.amount)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.patch("/{payment_id}", response_model=PaymentRead)
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Payment:
    payment = _get_payment_or_404(db, payment_id)
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] == PaymentStatus.PAID:
        payment.paid_at = datetime.now(UTC)
    for key, value in data.items():
        setattr(payment, key, value)
    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> None:
    payment = _get_payment_or_404(db, payment_id)
    db.delete(payment)
    db.commit()
