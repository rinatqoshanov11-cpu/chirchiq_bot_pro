"""Application settings and configuration."""
import os
from typing import List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator


def to_asyncpg_url(url: str) -> str:
    """Make any Postgres URL usable by SQLAlchemy + asyncpg.

    Hosting providers (Neon, Render, Supabase...) give 'postgres://' or
    'postgresql://...?sslmode=require&channel_binding=require'; asyncpg needs
    'postgresql+asyncpg://...?ssl=require' and does not know channel_binding.
    """
    url = (url or "").strip()
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql", "postgresql+psycopg2", "postgresql+psycopg"):
        scheme = "postgresql+asyncpg"

    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            key = "ssl"
        if key == "channel_binding":
            continue
        query.append((key, value))
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


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
    admin_username: str = Field(default="", description="Admin's Telegram @username shown in 'contact the admin' texts")

    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL (any postgres:// form)")
    db_echo: bool = Field(default=False, description="Echo SQL queries")

    # Application
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    photos_per_ad: int = Field(default=10)
    min_photos_per_ad: int = Field(default=3, description="Minimum number of photos a listing must have")
    max_description_length: int = Field(default=1000)

    # Mini app web server
    webapp_host: str = Field(default="0.0.0.0")
    webapp_port: int = Field(default=8080)

    # Telegram Mini App (served by the aiohttp server inside the bot process)
    webapp_enabled: bool = Field(default=True, description="Start the mini app web server")
    webapp_url: str = Field(
        default="",
        description="Public HTTPS URL of the mini app (server address or tunnel). Empty = buttons hidden",
    )

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        return to_asyncpg_url(value)

    @model_validator(mode="after")
    def _hosting_port(self):
        # Render / Railway / Heroku tell the app which port to listen on via $PORT
        port = os.environ.get("PORT")
        if port and port.isdigit():
            self.webapp_port = int(port)
        # Render sets RENDER_EXTERNAL_URL to the service's public https address:
        # always trust it over a hand-typed WEBAPP_URL
        external = (os.environ.get("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
        if external.startswith("https://"):
            self.webapp_url = external
        return self



# Global settings instance
settings = Settings()
