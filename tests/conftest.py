import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
# ensure models are imported so metadata is populated
import importlib
importlib.import_module("app.models")  # register models with SQLAlchemy metadata
from app.seed import seed_tariffs
from app.models.user import User, UserRole
from app.models.driver import Driver
from app.auth import get_password_hash, create_access_token

# In-memory SQLite that persists across connections
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Point app.database and app.main to the testing engine/session to ensure lifespan uses the test DB
import importlib
_db_mod = importlib.import_module("app.database")
_db_mod.engine = engine
_db_mod.SessionLocal = TestingSessionLocal
_main_mod = importlib.import_module("app.main")
_main_mod.SessionLocal = TestingSessionLocal

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency override for tests
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Seed data and create users/driver
_db = TestingSessionLocal()
seed_tariffs(_db)

admin_user = User(
    name="Admin",
    email="admin@example.com",
    hashed_password=get_password_hash("adminpass"),
    role=UserRole.ADMIN,
)
client_user = User(
    name="Client",
    email="client@example.com",
    hashed_password=get_password_hash("clientpass"),
    role=UserRole.CLIENT,
)
driver_user = User(
    name="Driver",
    email="driver@example.com",
    hashed_password=get_password_hash("driverpass"),
    role=UserRole.DRIVER,
)
_db.add_all([admin_user, client_user, driver_user])
_db.commit()
_db.refresh(admin_user)
_db.refresh(client_user)
_db.refresh(driver_user)

# create driver profile for driver_user
driver_profile = Driver(user_id=driver_user.id, car="TestCar", is_available=True)
_db.add(driver_profile)
_db.commit()
_db.refresh(driver_profile)

# create tokens fixtures
_admin_token = create_access_token(subject=admin_user.email)
_client_token = create_access_token(subject=client_user.email)
_driver_token = create_access_token(subject=driver_user.email)

_db.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin_token():
    return _admin_token

@pytest.fixture
def client_token():
    return _client_token

@pytest.fixture
def driver_token():
    return _driver_token
