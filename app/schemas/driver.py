from pydantic import BaseModel, ConfigDict, Field


class DriverCreate(BaseModel):
    user_id: int
    car: str = Field(min_length=1, max_length=255)
    is_available: bool = True


class DriverUpdate(BaseModel):
    car: str | None = Field(default=None, min_length=1, max_length=255)
    is_available: bool | None = None


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    car: str
    is_available: bool
