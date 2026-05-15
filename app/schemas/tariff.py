from pydantic import BaseModel, ConfigDict, Field


class TariffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price_per_km: float = Field(gt=0)


class TariffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price_per_km: float | None = Field(default=None, gt=0)


class TariffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_per_km: float
