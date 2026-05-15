from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    price_per_km: Mapped[float] = mapped_column(Float, nullable=False)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="tariff")
