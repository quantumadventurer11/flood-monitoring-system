from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    database_url: str = "sqlite:///./flood_monitoring.db"
    copernicus_user: str | None = None
    copernicus_password: str | None = None
    allowed_origins: str | None = None
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"
    cors_origin_regex: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = self.allowed_origins or self.cors_origins
        return [origin.strip() for origin in origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
