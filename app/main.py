from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.config import settings
from app.database import SessionLocal
from app.routers.admin import router as admin_router
from app.routers.drivers import router as drivers_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.reports import router as reports_router
from app.routers.tariffs import router as tariffs_router
from app.seed import seed_tariffs

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        seed_tariffs(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

# HTML pages (registered before API routers where paths overlap)
@app.get("/admin/users", include_in_schema=False)
def admin_users_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin_users.html")


@app.get("/orders", include_in_schema=False)
def orders_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "orders.html")


@app.get("/orders/new", include_in_schema=False)
def order_new_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "order_new.html")


@app.get("/orders/detail", include_in_schema=False)
def order_detail_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "order_detail.html")


@app.get("/drivers", include_in_schema=False)
def drivers_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "drivers.html")


@app.get("/tariffs", include_in_schema=False)
def tariffs_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "tariffs.html")


@app.get("/profile", include_in_schema=False)
def profile_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "profile.html")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login")
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/register")
def register_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "register.html")


@app.get("/dashboard")
def dashboard_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(drivers_router)
app.include_router(tariffs_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(reports_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
