"""Stored interface language per Telegram user (table user_languages) with an in-process cache."""
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import LANGS
from app.models.user_language import UserLanguage

# telegram_id -> language, or None = looked up, nothing stored.
# Safe because the bot and the mini app server run in one process and every write goes
# through set_language().
_cache: Dict[int, Optional[str]] = {}


def cached_language(telegram_id: int) -> Optional[str]:
    """Language from the cache only (no DB). None = not stored OR not looked up yet."""
    return _cache.get(telegram_id)


def is_cached(telegram_id: int) -> bool:
    """True if the DB was already asked about this user."""
    return telegram_id in _cache


async def get_language(session: AsyncSession, telegram_id: int) -> Optional[str]:
    """The language the user picked ('uz' | 'ru' | 'en'), or None if never picked."""
    if telegram_id in _cache:
        return _cache[telegram_id]
    result = await session.execute(
        select(UserLanguage.language).where(UserLanguage.telegram_id == telegram_id)
    )
    lang = result.scalar_one_or_none()
    if lang not in LANGS:
        lang = None
    _cache[telegram_id] = lang
    return lang


async def set_language(session: AsyncSession, telegram_id: int, lang: str) -> None:
    """Save (insert or update) the user's language and commit."""
    if lang not in LANGS:
        raise ValueError(f"Unsupported language: {lang!r}")
    now = datetime.utcnow()
    stmt = insert(UserLanguage).values(telegram_id=telegram_id, language=lang, updated_at=now)
    stmt = stmt.on_conflict_do_update(
        index_elements=[UserLanguage.telegram_id],
        set_={"language": lang, "updated_at": now},
    )
    await session.execute(stmt)
    await session.commit()
    _cache[telegram_id] = lang


def clear_cache() -> None:
    """Forget everything cached (tests)."""
    _cache.clear()
