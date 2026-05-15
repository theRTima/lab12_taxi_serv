from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    order_id: int
    amount: float = Field(gt=0)


class PaymentUpdate(BaseModel):
    status: PaymentStatus | None = None
    amount: float | None = Field(default=None, gt=0)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: float
    status: PaymentStatus
    paid_at: datetime | None
