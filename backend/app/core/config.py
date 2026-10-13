import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory (two levels up from backend/app/core)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    # Application configuration
    APP_NAME: str = "Scholarship Intelligence Crawler API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # CORS configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database configuration (SQLite with absolute Windows-friendly fallback)
    DATABASE_URL: str = f"sqlite:///{ROOT_DIR / 'data' / 'scholarships.db'}"

    # Crawler settings
    CRAWLER_USER_AGENT: str = (
        "ScholarshipIntelligenceCrawler/1.0 (+https://github.com/scholarship-intelligence-crawler; respectful-bot)"
    )
    CRAWLER_REQUEST_TIMEOUT: int = 15
    CRAWLER_DEFAULT_DELAY_SECONDS: float = 2.0
    CRAWLER_MAX_RETRIES: int = 3

    # Scheduler settings
    ENABLE_SCHEDULER: bool = False
    SCHEDULER_INTERVAL_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
