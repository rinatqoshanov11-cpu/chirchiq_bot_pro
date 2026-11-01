"""Fallback: answer messages no other handler understood (must be the LAST router)."""
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import t
from app.services import UserService
from app.keyboards import MainKeyboard

router = Router()


@router.message(StateFilter(None))
async def unknown_message(message: Message, session: AsyncSession, lang: str = "uz"):
    """Random text, stickers, etc. outside any flow -> point the user to the buttons."""
    user = await UserService.get_by_telegram_id(session, message.from_user.id)
    is_registered = bool(user and user.is_registered)

    await message.answer(
        t(lang, "fallback.unknown"),
        reply_markup=MainKeyboard.get_main_menu(is_registered=is_registered, lang=lang)
    )


@router.callback_query()
async def stale_callback(callback: CallbackQuery, lang: str = "uz"):
    """Buttons from old messages (e.g. the former '⬇️ Yana' listing pager)."""
    await callback.answer(
        t(lang, "fallback.stale_button", open_app=t(lang, "btn.open_app")),
        show_alert=True
    )
