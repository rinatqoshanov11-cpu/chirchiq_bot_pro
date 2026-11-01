"""Language picker (must be the FIRST router).

- /start while the user has no stored language -> picker (the welcome comes after a choice).
  With a stored language this router does not match /start, so registration's /start runs.
- /language command and the 'lang_menu' callback -> picker at any time.
- 'setlang_<code>' callback -> save, confirm, per-chat menu button, then registration.send_welcome.
"""
from typing import Any

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, MenuButtonWebApp, Message, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import LANGS, t
from app.keyboards import InlineKeyboards, MainKeyboard, webapp_url_for
from app.middlewares.language import lookup_language
from app.services.language_service import cached_language, is_cached, set_language
from app.utils import get_logger

logger = get_logger(__name__)
router = Router(name="language")


class LanguageNotChosen(Filter):
    """True when the sender has never picked a language.

    Filters run BEFORE inner middlewares, so data['lang_chosen'] is usually not there yet:
    the cache is checked, then the DB with a short-lived session. On a DB error -> False
    (the update falls through to the normal handlers, as before translations existed).
    """

    async def __call__(self, event: Any, **data: Any) -> bool:
        if "lang_chosen" in data:
            return not data["lang_chosen"]
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        if is_cached(user.id):
            return cached_language(user.id) is None
        stored = await lookup_language(None, user.id)
        # lookup_language returns None on a DB error too: only trust it if it got cached
        return stored is None and is_cached(user.id)


async def _send_picker(bot: Bot, chat_id: int) -> None:
    await bot.send_message(chat_id, t("uz", "lang.picker"), reply_markup=InlineKeyboards.get_language_picker())


@router.message(CommandStart(), LanguageNotChosen())
async def start_without_language(message: Message, state: FSMContext, bot: Bot):
    """First /start: ask for the language before anything else."""
    await state.clear()
    await _send_picker(bot, message.chat.id)


@router.message(Command("language", "lang", "til"))
async def cmd_language(message: Message, bot: Bot):
    """/language: open the picker at any time."""
    await _send_picker(bot, message.chat.id)


@router.callback_query(F.data == "lang_menu")
async def open_language_menu(callback: CallbackQuery, bot: Bot):
    """Inline '🌐 Tilni o'zgartirish' button (settings screen)."""
    await callback.answer()
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    await _send_picker(bot, chat_id)


@router.callback_query(F.data.startswith("setlang_"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Save the picked language and show the welcome in it."""
    lang = callback.data.removeprefix("setlang_")
    if lang not in LANGS:
        await callback.answer()
        return

    try:
        await set_language(session, callback.from_user.id, lang)
    except Exception as e:
        logger.error(f"Could not save language for {callback.from_user.id}: {e}")
        try:
            await session.rollback()
        except Exception:
            pass
        await callback.answer(t(lang, "lang.save_error"), show_alert=True)
        return

    # The old reply keyboard / flow was in the previous language -> start clean
    await state.clear()
    await callback.answer()

    chat_id = callback.message.chat.id if callback.message else callback.from_user.id

    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(t(lang, "lang.confirm"))
        except TelegramBadRequest:
            pass

    url = webapp_url_for(lang)
    if url.startswith("https://"):
        try:
            await bot.set_chat_menu_button(
                chat_id=chat_id,
                menu_button=MenuButtonWebApp(text=t(lang, "btn.app_menu"), web_app=WebAppInfo(url=url)),
            )
        except Exception as e:
            logger.warning(f"Could not set menu button for chat {chat_id}: {e}")

    try:
        from app.handlers.registration import send_welcome
    except ImportError:
        send_welcome = None

    if send_welcome is not None:
        await send_welcome(bot, chat_id, callback.from_user, session, lang)
        return

    # Fallback until registration.send_welcome exists: just show the main menu in the new language
    from app.services import UserService
    user = await UserService.get_by_telegram_id(session, callback.from_user.id)
    await bot.send_message(
        chat_id,
        t(lang, "lang.menu_hint"),
        reply_markup=MainKeyboard.get_main_menu(is_registered=bool(user and user.is_registered), lang=lang),
    )
