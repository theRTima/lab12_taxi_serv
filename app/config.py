from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Taxi Order Service"
    database_url: str = "sqlite:///./taxi.db"
    debug: bool = False


settings = Settings()
