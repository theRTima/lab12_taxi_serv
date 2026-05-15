import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Taxi Order Service"
    database_url: str = "sqlite:///./taxi.db"
    debug: bool = False

    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


settings = Settings()

# Generate ephemeral secret if using the insecure default
if settings.jwt_secret_key == "change-me-in-production-use-a-long-random-string":
    logging.warning(
        "Default insecure JWT secret detected; generating an ephemeral secret. "
        "Set JWT_SECRET_KEY environment variable for production."
    )
    settings.jwt_secret_key = secrets.token_urlsafe(32)
