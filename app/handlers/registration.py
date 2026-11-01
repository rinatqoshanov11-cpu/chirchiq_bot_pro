"""Registration handlers (and the /start welcome)."""
from html import escape

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import t, variants, is_text
from app.states import RegistrationStates
from app.services import UserService, ApartmentService
from app.keyboards import MainKeyboard, InlineKeyboards
from app.utils import validate_phone_number, get_logger

logger = get_logger(__name__)
router = Router()

BRAND = "Chirchiq Kvartira"


def _format_count(value: int) -> str:
    """Format a number with a space as thousands separator: 12345 -> '12 345'."""
    return f"{value:,}".replace(",", " ")


async def _active_listings_line(session: AsyncSession, lang: str) -> str:
    """Return a line with the live number of active listings, or '' on error / zero."""
    try:
        count = await ApartmentService.count_search(session)
    except Exception as e:
        logger.warning(f"Could not count active listings for /start: {e}")
        try:
            await session.rollback()
        except Exception:
            pass
        return ""

    if not count:
        return ""
    return t(lang, "start.listings_count", count=_format_count(count)) + "\n\n"


async def send_welcome(bot: Bot, chat_id: int, from_user: TgUser, session: AsyncSession, lang: str) -> None:
    """The /start welcome: greeting + live listings count + main menu, then the inline 'open app' button.

    Also called by app/handlers/language.py right after the user picks a language.
    """
    # Count first: on error it rolls back, which would expire an already loaded user
    listings_line = await _active_listings_line(session, lang)

    user = await UserService.get_by_telegram_id(session, from_user.id)
    is_registered = bool(user and user.is_registered)
    about = t(lang, "start.about", brand=BRAND)

    if is_registered:
        name = escape(user.full_name or from_user.first_name or "")
        greeting = t(lang, "start.greet_name", name=name)
        body = t(lang, "start.body_registered")
    else:
        first_name = escape(from_user.first_name or "")
        greeting = t(lang, "start.greet_name", name=first_name) if first_name else t(lang, "start.greet")
        body = t(lang, "start.body_guest")

    await bot.send_message(
        chat_id,
        f"{greeting}\n\n{about}\n\n{listings_line}{body}",
        reply_markup=MainKeyboard.get_main_menu(is_registered=is_registered, lang=lang),
    )

    # Inline 'open app' button (inline buttons pass the user's identity to the app)
    keyboard = InlineKeyboards.get_open_app(lang, t(lang, "btn.view_listings"))
    if keyboard:
        await bot.send_message(chat_id, t(lang, "start.open_app_hint"), reply_markup=keyboard)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, bot: Bot, lang: str = "uz"):
    """Handle /start command."""
    await state.clear()
    await send_welcome(bot, message.chat.id, message.from_user, session, lang)


async def _cancel(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t(lang, "reg.cancelled"), reply_markup=ReplyKeyboardRemove())


@router.message(F.text.in_(variants("btn.register")))
async def start_registration(message: Message, state: FSMContext, session: AsyncSession, lang: str = "uz"):
    """Start registration process."""
    telegram_id = message.from_user.id

    # Check if already registered
    user = await UserService.get_by_telegram_id(session, telegram_id)
    if user and user.is_registered:
        await message.answer(
            t(lang, "reg.already", add=t(lang, "btn.add_listing")),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )
        return

    await message.answer(
        t(lang, "reg.start", cancel=t(lang, "btn.cancel")),
        reply_markup=MainKeyboard.get_cancel_keyboard(lang)
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext, lang: str = "uz"):
    """Process full name input."""
    if is_text(message.text, "btn.cancel"):
        await _cancel(message, state, lang)
        return

    if not message.text or len(message.text) < 3:
        await message.answer(t(lang, "reg.name_short"))
        return

    await state.update_data(full_name=message.text.strip())
    await message.answer(
        t(lang, "reg.phone_prompt", send_phone=t(lang, "btn.send_phone")),
        reply_markup=MainKeyboard.get_phone_keyboard(lang)
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


async def _ask_address(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(t(lang, "reg.address_prompt"), reply_markup=MainKeyboard.get_cancel_keyboard(lang))
    await state.set_state(RegistrationStates.waiting_for_address)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext, lang: str = "uz"):
    """Process phone number from contact."""
    phone = message.contact.phone_number
    validated_phone = validate_phone_number(phone)

    if not validated_phone:
        await message.answer(
            t(lang, "reg.phone_contact_invalid"),
            reply_markup=MainKeyboard.get_phone_keyboard(lang)
        )
        return

    await state.update_data(phone_number=validated_phone)
    await _ask_address(message, state, lang)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext, lang: str = "uz"):
    """Process phone number from text."""
    if is_text(message.text, "btn.cancel"):
        await _cancel(message, state, lang)
        return

    send_phone = t(lang, "btn.send_phone")

    if not message.text:
        await message.answer(
            t(lang, "reg.phone_not_text", send_phone=send_phone),
            reply_markup=MainKeyboard.get_phone_keyboard(lang)
        )
        return

    validated_phone = validate_phone_number(message.text)

    if not validated_phone:
        await message.answer(
            t(lang, "reg.phone_invalid", send_phone=send_phone),
            reply_markup=MainKeyboard.get_phone_keyboard(lang)
        )
        return

    await state.update_data(phone_number=validated_phone)
    await _ask_address(message, state, lang)


@router.message(RegistrationStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext, session: AsyncSession, lang: str = "uz"):
    """Process address and complete registration."""
    if is_text(message.text, "btn.cancel"):
        await _cancel(message, state, lang)
        return

    if not message.text or len(message.text) < 5:
        await message.answer(t(lang, "reg.address_short"))
        return

    # Get all registration data
    data = await state.get_data()

    try:
        # Create user in database
        user = await UserService.create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=data['full_name'],
            phone_number=data['phone_number'],
            address=message.text.strip(),
            username=message.from_user.username
        )

        await state.clear()

        await message.answer(
            t(
                lang, "reg.success",
                name=escape(user.full_name or ''),
                phone=escape(user.phone_number or ''),
                address=escape(user.address or ''),
            ),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )

        logger.info(f"New user registered: {user.telegram_id} - {user.full_name}")

    except Exception as e:
        logger.error(f"Registration error: {e}")
        await message.answer(t(lang, "reg.error"), reply_markup=ReplyKeyboardRemove())
        await state.clear()
