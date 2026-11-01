"""The interface language each Telegram user picked (also for users who never registered)."""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserLanguage(Base):
    """telegram_id -> 'uz' | 'ru' | 'en'."""

    __tablename__ = "user_languages"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<UserLanguage(telegram_id={self.telegram_id}, language='{self.language}')>"
