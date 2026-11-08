"""Telegram bot profile setup: name, descriptions, command menu and avatar.

Called once on startup. Every step is idempotent (reads the current value and
only writes when it differs) and isolated in try/except, so a failure here
never stops the bot.
"""
import hashlib
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    FSInputFile,
    InputProfilePhotoStatic,
    MenuButtonDefault,
    MenuButtonWebApp,
    WebAppInfo,
)

from app.i18n import t
from config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
AVATAR_PATH = ASSETS_DIR / "avatar.png"
AVATAR_MARKER = ASSETS_DIR / ".avatar_set"

BOT_NAME = "Chirchiq Kvartira"

# Telegram shows the description / short description / command menu in the
# user's Telegram app language: language_code "ru" / "en" get their own text,
# everyone else gets the default (no language_code), which is Uzbek.
# (language_code passed to the Bot API, bot language)
PROFILE_LANGUAGES: tuple[tuple[str | None, str], ...] = (
    (None, "uz"),
    ("ru", "ru"),
    ("en", "en"),
)

DESCRIPTION_LIMIT = 512
SHORT_DESCRIPTION_LIMIT = 120
COMMAND_DESCRIPTION_LIMIT = 256


def bot_description(lang: str = "uz") -> str:
    """Shown in the empty chat before the user presses START (max 512 chars)."""
    return t(lang, "profile.bot_description", open_app=t(lang, "btn.open_app"))


def bot_short_description(lang: str = "uz") -> str:
    """Shown on the bot profile page and in shared links (max 120 chars)."""
    return t(lang, "profile.bot_short_description")


def user_commands(lang: str = "uz") -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t(lang, "profile.cmd_start")),
        BotCommand(command="help", description=t(lang, "profile.cmd_help")),
        BotCommand(command="language", description=t(lang, "profile.cmd_language")),
    ]


def admin_commands(lang: str = "uz") -> list[BotCommand]:
    # The admin panel itself stays Uzbek; its command label is the same everywhere.
    return user_commands(lang) + [
        BotCommand(command="admin", description="Admin panel"),
        BotCommand(command="import", description="E'lonni forward orqali qo'shish"),
    ]


# Uzbek defaults (kept for backward compatibility)
BOT_DESCRIPTION = bot_description("uz")
BOT_SHORT_DESCRIPTION = bot_short_description("uz")
USER_COMMANDS = user_commands("uz")
ADMIN_COMMANDS = admin_commands("uz")


def _lang_label(language_code: str | None) -> str:
    return language_code or "default"


def _commands_key(commands) -> list[tuple[str, str]]:
    return [(c.command, c.description) for c in commands]


async def _setup_name(bot: Bot) -> None:
    current = await bot.get_my_name()
    if current.name == BOT_NAME:
        logger.info("Bot profile: name already up to date")
        return
    await bot.set_my_name(name=BOT_NAME)
    logger.info("Bot profile: name set to %r", BOT_NAME)


async def _setup_description(bot: Bot) -> None:
    for language_code, lang in PROFILE_LANGUAGES:
        label = _lang_label(language_code)
        try:
            text = bot_description(lang)
            current = await bot.get_my_description(language_code=language_code)
            if current.description == text:
                logger.info("Bot profile: description (%s) already up to date", label)
                continue
            await bot.set_my_description(description=text, language_code=language_code)
            logger.info("Bot profile: description (%s) updated", label)
        except Exception as e:
            logger.warning("Bot profile: failed to set description (%s): %s", label, e)


async def _setup_short_description(bot: Bot) -> None:
    for language_code, lang in PROFILE_LANGUAGES:
        label = _lang_label(language_code)
        try:
            text = bot_short_description(lang)
            current = await bot.get_my_short_description(language_code=language_code)
            if current.short_description == text:
                logger.info("Bot profile: short description (%s) already up to date", label)
                continue
            await bot.set_my_short_description(
                short_description=text, language_code=language_code
            )
            logger.info("Bot profile: short description (%s) updated", label)
        except Exception as e:
            logger.warning(
                "Bot profile: failed to set short description (%s): %s", label, e
            )


async def _setup_commands_for_scope(
    bot: Bot, commands, scope, label: str, language_code: str | None = None
) -> None:
    label = f"{label}, {_lang_label(language_code)}"
    current = await bot.get_my_commands(scope=scope, language_code=language_code)
    if _commands_key(current) == _commands_key(commands):
        logger.info("Bot profile: commands for %s already up to date", label)
        return
    await bot.set_my_commands(commands=commands, scope=scope, language_code=language_code)
    logger.info("Bot profile: commands for %s updated", label)


async def _setup_commands(bot: Bot) -> None:
    for language_code, lang in PROFILE_LANGUAGES:
        try:
            await _setup_commands_for_scope(
                bot, user_commands(lang), BotCommandScopeDefault(), "everyone",
                language_code,
            )
        except Exception as e:
            logger.warning(
                "Bot profile: failed to set default commands (%s): %s",
                _lang_label(language_code), e,
            )

    for admin_id in settings.admin_ids:
        for language_code, lang in PROFILE_LANGUAGES:
            try:
                await _setup_commands_for_scope(
                    bot,
                    admin_commands(lang),
                    BotCommandScopeChat(chat_id=admin_id),
                    f"admin {admin_id}",
                    language_code,
                )
            except Exception as e:
                # Chat may not exist yet (admin never opened the bot)
                logger.warning(
                    "Bot profile: failed to set admin commands for %s (%s): %s",
                    admin_id, _lang_label(language_code), e,
                )
                break  # same chat, the other languages would fail too


async def _setup_profile_photo(bot: Bot) -> None:
    if not AVATAR_PATH.is_file():
        logger.info("Bot profile: %s not found, skipping profile photo", AVATAR_PATH)
        return

    digest = hashlib.sha256(AVATAR_PATH.read_bytes()).hexdigest()
    try:
        if AVATAR_MARKER.read_text(encoding="utf-8").strip() == digest:
            logger.info("Bot profile: profile photo already set")
            return
    except FileNotFoundError:
        # No marker (fresh server / redeploy): if the bot already has a photo, don't re-upload
        try:
            photos = await bot.get_user_profile_photos(bot.id, limit=1)
            if photos.total_count > 0:
                AVATAR_MARKER.write_text(digest, encoding="utf-8")
                logger.info("Bot profile: profile photo already present, marker restored")
                return
        except Exception as e:
            logger.warning("Bot profile: could not check current photo: %s", e)

    await bot.set_my_profile_photo(
        photo=InputProfilePhotoStatic(photo=FSInputFile(AVATAR_PATH))
    )
    AVATAR_MARKER.write_text(digest, encoding="utf-8")
    logger.info("Bot profile: profile photo updated")


# The global button is Uzbek; chats that picked a language get their own
# per-chat button (app/handlers/language.py).
MENU_BUTTON_TEXT = t("uz", "btn.app_menu")


async def _setup_menu_button(bot: Bot) -> None:
    """Chat menu button opens the mini app when WEBAPP_URL is an https:// URL."""
    url = (settings.webapp_url or "").strip()
    use_webapp = url.startswith("https://")

    current = await bot.get_chat_menu_button()
    if use_webapp:
        current_url = getattr(getattr(current, "web_app", None), "url", None)
        if (
            current.type == "web_app"
            and current_url == url
            and getattr(current, "text", None) == MENU_BUTTON_TEXT
        ):
            logger.info("Bot profile: menu button already up to date")
            return
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text=MENU_BUTTON_TEXT, web_app=WebAppInfo(url=url))
        )
        logger.info("Bot profile: menu button set to mini app %s", url)
    else:
        if current.type == "default":
            logger.info("Bot profile: menu button already default")
            return
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
        logger.info("Bot profile: menu button reset to default (no WEBAPP_URL)")


async def setup_bot_profile(bot: Bot) -> None:
    """Configure bot name, descriptions, commands and avatar. Never raises."""
    steps = (
        ("name", _setup_name),
        ("description", _setup_description),
        ("short description", _setup_short_description),
        ("commands", _setup_commands),
        ("menu button", _setup_menu_button),
        ("profile photo", _setup_profile_photo),
    )
    for label, step in steps:
        try:
            await step(bot)
        except Exception as e:
            logger.warning("Bot profile: failed to set %s: %s", label, e)
