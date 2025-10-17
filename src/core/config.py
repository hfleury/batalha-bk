"""
Application configuration management using Pydantic and environment variables.

This module defines the `Settings` class, which centralizes all configuration for the
application (e.g., database, Redis, logging, environment mode) by loading values from
environment variables. It supports different environments
(development, staging, production)
and provides sensible defaults where appropriate.

Environment variables are loaded from a `.env` file if present (using `python-dotenv`),
making local development easier.

The settings are validated at startup using Pydantic, ensuring that:
- Required fields are present.
- Values are of the correct type (e.g., int, bool).
- Allowed options (like environment name) are valid.
"""

from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
Environment = Literal["local", "development", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class DatabaseSettings(BaseSettings):
    """Configuration settings for the PostgreSQL database."""

    host: str = "db"
    port: int = 5432
    user: str = "batalha_user"
    password: str = "nosecret"
    database: str = "batalha_naval_db"

    @property
    def url(self) -> str:
        """Constructs the full database connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        extra="ignore",
    )


class RedisSettings(BaseSettings):
    """Configuration settings for the Redis cache."""

    host: str = "redis"
    port: int = 6379
    decode_responses: bool = True
    username: str = "batalha_redis_user"
    password: str = "nosecret"
    db: int = 0

    @property
    def url(self) -> str:
        """Constructs the Redis connection URL."""
        return f"redis://{self.host}:{self.port}/{self.db}"

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore",
    )


class LoggingSettings(BaseSettings):
    """Configuration settings for application logging."""

    log_level: LogLevel = "INFO"
    auto_install: bool = False
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    log_date_format: str = "%d-%m-%Y %H:%M:%S"
    level_styles: dict[str, Any] = Field(default_factory=dict)
    field_styles: dict[str, Any] = Field(default_factory=dict)

    @property
    def should_install_coloredlogs(self) -> bool:
        """Determines if colored logs should be installed based on the environment."""
        return settings.app.is_local or settings.app.is_development

    model_config = SettingsConfigDict(
        env_prefix="COLOREDLOGS_",
        extra="ignore",
    )


class AppSettings(BaseSettings):
    """General application settings."""

    environment: Environment = "local"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def is_local(self) -> bool:
        """Checks if the current environment is 'local'."""
        return self.environment == "local"

    @property
    def is_development(self) -> bool:
        """Checks if the current environment is 'development'."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Checks if the current environment is 'production'."""
        return self.environment == "production"


class Settings:
    """
    Unified application settings composed of nested configuration objects.
    """

    app: AppSettings = AppSettings()
    db: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    log: LoggingSettings = LoggingSettings()


settings = Settings()
