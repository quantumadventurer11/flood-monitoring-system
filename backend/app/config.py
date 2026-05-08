"""
Application configuration settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Flood Monitoring System"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "flood_user"
    POSTGRES_PASSWORD: str = "flood_pass"
    POSTGRES_DB: str = "flood_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Copernicus Data Space Ecosystem
    CDSE_CLIENT_ID: str | None = None
    CDSE_CLIENT_SECRET: str | None = None
    
    # Email Configuration
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    
    # Map Settings
    DEFAULT_LATITUDE: float = 23.6850
    DEFAULT_LONGITUDE: float = 90.3563
    DEFAULT_ZOOM: int = 8
    
    # Satellite Data
    SENTINEL_1_COLLECTION: str = "COPERNICUS/S1_GRD"
    SENTINEL_2_COLLECTION: str = "COPERNICUS/S2_SR_HARMONIZED"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()