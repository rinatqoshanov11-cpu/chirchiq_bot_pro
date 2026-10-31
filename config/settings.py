"""Application settings and configuration."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Bot Configuration
    bot_token: str = Field(..., description="Telegram Bot Token")
    admin_ids: List[int] = Field(default_factory=list, description="List of admin Telegram IDs")

    # Database
    database_url: PostgresDsn = Field(..., description="PostgreSQL connection URL")
    db_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    # Scraper
    scraper_enabled: bool = Field(default=True)
    scraper_interval: int = Field(default=3600, description="Scraper interval in seconds")
    scraper_timeout: int = Field(default=30)

    # Application
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    photos_per_ad: int = Field(default=10)
    max_description_length: int = Field(default=1000)

    # Webhook
    use_webhook: bool = Field(default=False)
    webhook_url: str = Field(default="")
    webhook_path: str = Field(default="/webhook")
    webapp_host: str = Field(default="0.0.0.0")
    webapp_port: int = Field(default=8080)

    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance
settings = Settings()
