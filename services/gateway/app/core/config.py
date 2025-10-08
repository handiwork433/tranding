"""Configuration module for the trading gateway service."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    project_name: str = "Trading Gateway API"
    api_version: str = "0.1.0"
    api_prefix: str = ""
    database_url: str = "sqlite:///./gateway.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    starting_equity: float = 10000.0
    first_superuser_email: str = "admin@example.com"
    first_superuser_password: str = "admin"
    first_superuser_full_name: str = "Administrator"
    public_paths: tuple[str, ...] = (
        "/auth/login",
        "/auth/refresh",
        "/auth/2fa/verify",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    )

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()
