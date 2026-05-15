from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.driver import Driver
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.tariff import Tariff
from app.models.user import User
from app.schemas.report import OrdersPerDay, ReportSummary, RevenueByTariff, TopDriver

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummary)
def report_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ReportSummary:
    total_orders = db.query(func.count(Order.id)).scalar() or 0

    revenue_rows = (
        db.query(
            Tariff.id,
            Tariff.name,
            func.coalesce(func.sum(Payment.amount), 0.0),
        )
        .outerjoin(Order, Order.tariff_id == Tariff.id)
        .outerjoin(
            Payment,
            (Payment.order_id == Order.id) & (Payment.status == PaymentStatus.PAID),
        )
        .group_by(Tariff.id, Tariff.name)
        .all()
    )
    revenue_by_tariff = [
        RevenueByTariff(tariff_id=row[0], tariff_name=row[1], revenue=float(row[2]))
        for row in revenue_rows
    ]

    top_driver_rows = (
        db.query(
            Driver.id,
            User.name,
            func.count(Order.id),
        )
        .join(User, User.id == Driver.user_id)
        .join(Order, Order.driver_id == Driver.id)
        .group_by(Driver.id, User.name)
        .order_by(func.count(Order.id).desc())
        .limit(5)
        .all()
    )
    top_drivers = [
        TopDriver(driver_id=row[0], driver_name=row[1], order_count=row[2])
        for row in top_driver_rows
    ]

    since = datetime.now(UTC) - timedelta(days=7)
    day_rows = (
        db.query(
            func.date(Order.created_at),
            func.count(Order.id),
        )
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    orders_per_day = [
        OrdersPerDay(date=str(row[0]), count=row[1]) for row in day_rows
    ]

    return ReportSummary(
        total_orders=total_orders,
        revenue_by_tariff=revenue_by_tariff,
        top_drivers=top_drivers,
        orders_per_day=orders_per_day,
    )
