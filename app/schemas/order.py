from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    tariff_id: int
    pickup: str = Field(min_length=1, max_length=500)
    destination: str = Field(min_length=1, max_length=500)


class OrderUpdate(BaseModel):
    pickup: str | None = Field(default=None, min_length=1, max_length=500)
    destination: str | None = Field(default=None, min_length=1, max_length=500)
    tariff_id: int | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    driver_id: int | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    driver_id: int | None
    tariff_id: int
    status: OrderStatus
    created_at: datetime
    pickup: str
    destination: str
