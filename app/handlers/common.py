"""Common handlers: settings, usage guide. Browsing listings lives in the mini app."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings as app_settings

from app.i18n import LANG_NAMES, t, variants
from app.services import UserService
from app.keyboards import MainKeyboard, InlineKeyboards
from app.utils import get_logger
from app.utils.contact import contact_admin_html

logger = get_logger(__name__)
router = Router()

BRAND = "Chirchiq Kvartira"


@router.message(F.text.in_(variants("btn.open_app")))
async def open_app(message: Message, lang: str = "uz"):
    """Reply-keyboard button -> inline web-app button (only inline/menu buttons pass the user's identity)."""
    keyboard = InlineKeyboards.get_open_app(lang)
    if not keyboard:
        await message.answer(t(lang, "menu.app_unavailable"))
        return
    await message.answer(t(lang, "menu.app_text", brand=BRAND), reply_markup=keyboard)


@router.message(F.text.in_(variants("btn.settings")))
async def settings(message: Message, session: AsyncSession, lang: str = "uz"):
    """Show user settings: profile card + language + the guide menu."""
    user = await UserService.get_by_telegram_id(session, message.from_user.id)

    if not user:
        await message.answer(
            t(lang, "settings.register_first", register=t(lang, "btn.register")),
            reply_markup=MainKeyboard.get_main_menu(is_registered=False, lang=lang)
        )
        return

    from app.utils import format_user_info

    text = format_user_info(user, lang)
    text += "\n" + t(lang, "lang.current", name=LANG_NAMES.get(lang, LANG_NAMES["uz"]))
    text += "\n\n" + t(lang, "settings.edit_contact", admin=contact_admin_html(lang))

    # Reply keyboard is re-sent so it matches the current language
    await message.answer(text, reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang))
    await message.answer(_guide_menu_text(lang), reply_markup=_guide_menu_keyboard(lang))


# ---------------------------------------------------------------------------
# Bot usage guide (opened from "⚙️ Sozlamalar" or the /help command)
# ---------------------------------------------------------------------------

# section key -> (button label key, text key)
GUIDE_SECTIONS = {
    "app": ("guide.btn_app", "guide.app"),
    "add": ("guide.btn_add", "guide.add"),
    "mine": ("guide.btn_mine", "guide.mine"),
    "help": ("guide.btn_help", "guide.help"),
}


def _guide_menu_text(lang: str) -> str:
    return t(lang, "guide.menu_text", brand=BRAND)


def _guide_section_text(key: str, lang: str) -> str:
    return t(
        lang, GUIDE_SECTIONS[key][1],
        photos=str(app_settings.photos_per_ad),
        admin=contact_admin_html(lang),
        open_app=t(lang, "btn.open_app"),
        app_menu=t(lang, "btn.app_menu"),
        settings=t(lang, "btn.settings"),
    )


def _guide_menu_keyboard(lang: str):
    """Guide sections + '🌐 Tilni o'zgartirish' (callback 'lang_menu', handled by language.py)."""
    builder = InlineKeyboardBuilder()
    for key, (button_key, _) in GUIDE_SECTIONS.items():
        builder.button(text=t(lang, button_key), callback_data=f"guide_{key}")
    builder.button(text=t(lang, "btn.change_language"), callback_data="lang_menu")
    builder.adjust(1)
    return builder.as_markup()


def _guide_back_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn.back"), callback_data="guide_menu")
    return builder.as_markup()


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str = "uz"):
    """Show the usage guide to anyone (registration not required)."""
    await message.answer(_guide_menu_text(lang), reply_markup=_guide_menu_keyboard(lang))


@router.callback_query(F.data.startswith("guide_"))
async def show_guide_section(callback: CallbackQuery, lang: str = "uz"):
    """Switch the guide message between the menu and a section."""
    key = callback.data.removeprefix("guide_")

    if key == "menu":
        text, keyboard = _guide_menu_text(lang), _guide_menu_keyboard(lang)
    elif key in GUIDE_SECTIONS:
        text = _guide_section_text(key, lang)
        keyboard = _guide_back_keyboard(lang)
    else:
        await callback.answer()
        return

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as e:
        # Same button pressed twice -> nothing to change; otherwise send a fresh message
        if "message is not modified" not in str(e):
            await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()
