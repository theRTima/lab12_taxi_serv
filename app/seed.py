from sqlalchemy.orm import Session

from app.models.tariff import Tariff

DEFAULT_TARIFFS = [
    ("Simple", 12.0),
    ("Medium", 20.0),
    ("Lux", 35.0),
]


def seed_tariffs(db: Session) -> None:
    for name, price in DEFAULT_TARIFFS:
        if db.query(Tariff).filter(Tariff.name == name).first() is None:
            db.add(Tariff(name=name, price_per_km=price))
    db.commit()
