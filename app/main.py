from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.config import settings
from app.routers.admin import router as admin_router
from app.routers.drivers import router as drivers_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.reports import router as reports_router
from app.routers.tariffs import router as tariffs_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(drivers_router)
app.include_router(tariffs_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(reports_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/admin/users", include_in_schema=False)
def admin_users_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin_users.html")


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
