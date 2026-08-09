"""
Application settings, loaded from environment variables / .env file.

Mirrors the relevant bits of the old Django settings.py:
- SECRET_KEY               -> SECRET_KEY
- SIMPLE_JWT lifetimes      -> ACCESS_TOKEN_EXPIRE_MINUTES / REFRESH_TOKEN_EXPIRE_MINUTES
- DATABASES['default']     -> DATABASE_URL
- CORS_ALLOW_ALL_ORIGINS   -> CORS_ALLOW_ALL_ORIGINS
- GEMINI_API_KEY           -> GEMINI_API_KEY (used by the AI insight endpoint)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Expense Tracker API"
    PROJECT_DESCRIPTION: str = "API documentation for Personal Expense Tracker App"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120   # Django: timedelta(hours=2)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 180  # Django: timedelta(hours=3)

    DATABASE_URL: str = "sqlite+aiosqlite:///./db.sqlite3"

    CORS_ALLOW_ALL_ORIGINS: bool = True
    CORS_ALLOWED_ORIGINS: list[str] = ["https://gettrackflow-ai.vercel.app/"]

    GEMINI_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()