from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    order_id: int
    amount: float = Field(gt=0)


class PaymentSimulate(BaseModel):
    order_id: int
    amount: float = Field(gt=0)
    card_number: str = Field(min_length=13, max_length=19)
    card_holder: str = Field(min_length=1, max_length=100)

    @field_validator("card_number")
    @classmethod
    def digits_only(cls, value: str) -> str:
        cleaned = value.replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("Card number must contain only digits")
        return cleaned


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
