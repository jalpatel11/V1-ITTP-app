"""Configuration module for Centralized Environment Settings.

Rule 1.12: Environment variables MUST be accessed only inside this config module.
Never call os.getenv or process.env directly inside business or route code.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings loaded from environment variables or defaults."""

    app_name: str = "Community Tourism Portal API"
    environment: str = "development"
    debug: bool = True
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # Database URL: defaults to SQLite file database for easy local execution without PostGIS requirement
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tourism_portal.db")

    # CORS origins
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    """Returns application configuration settings instance.

    Returns:
        Settings: Configured settings object.
    """
    return Settings()


# Singleton settings object for application use
settings = get_settings()
