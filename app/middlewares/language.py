"""Language middleware: data['lang'] and data['lang_chosen'] for every handler.

Registered as an INNER middleware right after DatabaseMiddleware (it reuses data['session']).
Inner middlewares run after filters, so filters cannot see data['lang']; use
app.handlers.language.LanguageNotChosen (or language_service directly) inside filters.
"""
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from app.i18n import normalize_lang
from app.models.base import async_session_maker
from app.services.language_service import get_language
from app.utils import get_logger

logger = get_logger(__name__)


async def lookup_language(session, telegram_id: int) -> Optional[str]:
    """Stored language or None. Never raises; a failed query is rolled back."""
    try:
        if session is not None:
            return await get_language(session, telegram_id)
        async with async_session_maker() as own_session:
            return await get_language(own_session, telegram_id)
    except Exception as e:
        logger.warning(f"Could not read language of {telegram_id}: {e}")
        if session is not None:
            try:
                await session.rollback()
            except Exception:
                pass
        return None


class LanguageMiddleware(BaseMiddleware):
    """Puts the user's language into data['lang'] ('uz' | 'ru' | 'en') and data['lang_chosen'] (bool)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: Optional[User] = data.get("event_from_user") or getattr(event, "from_user", None)
        stored = None
        if user is not None:
            stored = await lookup_language(data.get("session"), user.id)

        data["lang"] = stored or normalize_lang(getattr(user, "language_code", None))
        data["lang_chosen"] = stored is not None
        return await handler(event, data)
