"""Admin "forward import": a forwarded / pasted listing post -> a published listing.

The admin forwards (or pastes) a post from a channel, OLX, a realtor's message, with or
without photos (albums too). The parser (app.utils.listing_parser) pulls out what it can,
the bot asks ONLY for the required fields it could not find, shows the normal preview and
on "✅ Tasdiqlash" saves the listing with source='import' and approves it at once.

Admin-only feature -> every text here is Uzbek. Router order: after admin_router, before
fallback_router (fallback answers any stateless text and swallows unknown callbacks).
"""
import asyncio
import html
from typing import Any, Dict, List, Optional

from aiogram import Router, F
from aiogram.filters import BaseFilter, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states import ImportStates
from app.services import UserService
from app.keyboards import MainKeyboard
from app.models.apartment import ApartmentType
from app.models.base import async_session_maker
from app.utils import format_price, get_logger
from app.utils.formatters import validate_phone_number
from app.i18n import DEFAULT_LANG, is_text
from app.handlers.apartments import _import_next_missing, _next_or_preview, _handle_cancel, _ask_import_phone
from config import settings

try:  # the parser module is a separate deliverable; the bot must still start without it
    from app.utils.listing_parser import parse_listing_text, address_from
except ImportError:  # pragma: no cover
    parse_listing_text = None
    address_from = None

logger = get_logger(__name__)
router = Router()

ALBUM_DEBOUNCE = 1.5  # seconds to wait for the rest of a media group

INTRO_TEXT = (
    "📥 <b>E'lon import</b>\n\n"
    "E'lon matnini forward qiling yoki shu yerga qo'ying (rasm bilan ham bo'ladi, albom ham). "
    "Men narx, xonalar, telefon va manzilni o'zim ajratib olaman."
)
NO_RIGHTS = "❌ Sizda admin huquqlari yo'q."
CANCELLED = "❌ Import bekor qilindi."

# Media groups being collected: (chat_id, media_group_id) -> {"messages": [...], "task": Task}
_albums: Dict[tuple, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Filters / helpers
# ---------------------------------------------------------------------------

async def _is_admin(session: Optional[AsyncSession], telegram_id: int) -> bool:
    """settings.admin_ids first (no DB); then the users table (own session when needed)."""
    if telegram_id in settings.admin_ids:
        return True
    try:
        if session is not None:
            return await UserService.is_admin(session, telegram_id)
        async with async_session_maker() as own_session:
            return await UserService.is_admin(own_session, telegram_id)
    except Exception as e:
        logger.warning(f"Admin check failed for {telegram_id}: {e}")
        return False


class IsAdmin(BaseFilter):
    """Filter form of _is_admin (inner middlewares run after filters -> no data['session'] here)."""

    async def __call__(self, event, session: Optional[AsyncSession] = None, **kwargs) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return await _is_admin(session, user.id)


def _origin_name(message: Message) -> Optional[str]:
    """Channel / chat / user the post was forwarded from (title or @username), or None."""
    origin = getattr(message, "forward_origin", None)
    if origin is None:
        return None
    chat = getattr(origin, "chat", None) or getattr(origin, "sender_chat", None)
    if chat is not None:
        if getattr(chat, "title", None):
            return chat.title
        if getattr(chat, "username", None):
            return f"@{chat.username}"
    sender = getattr(origin, "sender_user", None)
    if sender is not None:
        if getattr(sender, "username", None):
            return f"@{sender.username}"
        return getattr(sender, "full_name", None) or getattr(sender, "first_name", None)
    return getattr(origin, "sender_user_name", None)


def _photo_id(message: Message) -> Optional[str]:
    """file_id of the largest size of the message photo, or None."""
    if message.photo:
        return message.photo[-1].file_id
    return None


def _text_of(message: Message) -> str:
    return (message.text or message.caption or "").strip()


def _price_line(price: Optional[int], currency: Optional[str], type_key: Optional[str]) -> str:
    text = format_price(price, currency or "UZS", lang="uz")
    if type_key == "rent":
        text += " / oy"
    return text


def _summary(parsed, photos: List[str], address: Optional[str]) -> str:
    """'🔎 Topildi:' message: ✅ for found, ❌ '— so'rayman' for the missing required ones."""
    lines = ["🔎 <b>Topildi:</b>", ""]

    if parsed.type:
        lines.append("✅ Turi: " + ("Ijaraga" if parsed.type == "rent" else "Sotiladi"))
    else:
        lines.append("❌ Turi topilmadi — so'rayman")

    if parsed.rooms:
        lines.append(f"✅ Xonalar: {parsed.rooms}")
    else:
        lines.append("❌ Xonalar soni topilmadi — so'rayman")

    if address:
        lines.append(f"✅ Manzil: {html.escape(address)}")
    else:
        lines.append("❌ Manzil topilmadi — so'rayman")

    if parsed.price is not None:
        lines.append("✅ Narx: " + html.escape(_price_line(parsed.price, parsed.currency, parsed.type)))
    else:
        lines.append("❌ Narx topilmadi — so'rayman")

    if parsed.phone:
        lines.append(f"✅ Telefon: {html.escape(parsed.phone)}")
    else:
        lines.append("❌ Telefon topilmadi — so'rayman")

    if photos:
        lines.append(f"✅ Rasmlar: {len(photos)} ta")
    else:
        lines.append("❌ Rasmlar topilmadi — so'rayman")

    # Optional fields (shown only when found)
    if parsed.area:
        lines.append(f"✅ Maydon: {parsed.area:g} m²")
    if parsed.floor:
        floor_text = f"{parsed.floor}/{parsed.total_floors}" if parsed.total_floors else str(parsed.floor)
        lines.append(f"✅ Qavat: {floor_text}")
    elif parsed.total_floors:
        lines.append(f"✅ Uy qavatlari: {parsed.total_floors}")
    if parsed.description:
        lines.append("✅ Tavsif: matndan olindi")

    notes = [n for n in (getattr(parsed, "notes", None) or []) if n]
    if notes:
        lines.append("")
        lines.extend(f"ℹ️ {html.escape(str(n))}" for n in notes)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Triggers: /import, admin-panel button, forwarded message without a state
# ---------------------------------------------------------------------------

async def _start_import(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await state.set_state(ImportStates.waiting_for_post)
    await message.answer(INTRO_TEXT, reply_markup=MainKeyboard.get_cancel_keyboard("uz"))


@router.message(Command("import"))
async def cmd_import(message: Message, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    """/import -> wait for the post."""
    if not await _is_admin(session, message.from_user.id):
        await message.answer(NO_RIGHTS)
        return
    await _start_import(message, state, lang)


@router.callback_query(F.data == "admin_import")
async def cb_admin_import(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    """'📥 E'lon import qilish' in the admin panel."""
    if not await _is_admin(session, callback.from_user.id):
        await callback.answer(NO_RIGHTS, show_alert=True)
        return
    await callback.answer()
    await _start_import(callback.message, state, lang)


@router.message(StateFilter(None), F.forward_origin, IsAdmin())
async def forwarded_without_state(message: Message, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    """An admin forwards a post with no flow running -> import it right away."""
    await state.clear()
    await state.set_state(ImportStates.waiting_for_post)
    await _collect(message, state, session, lang)


# ---------------------------------------------------------------------------
# waiting_for_post: text / photo(+caption) / album
# ---------------------------------------------------------------------------

@router.message(ImportStates.waiting_for_post)
async def receive_post(message: Message, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    if is_text(message.text, "btn.cancel"):
        await state.clear()
        await message.answer(CANCELLED, reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang))
        return
    await _collect(message, state, session, lang)


async def _collect(message: Message, state: FSMContext, session: AsyncSession, lang: str):
    """Single message -> process now; album item -> buffer and process after a short pause."""
    text = _text_of(message)
    photo = _photo_id(message)

    if not text and not photo:
        await message.answer(
            "⚠️ Matn yoki rasm yuboring. E'lon postini forward qiling yoki matnini qo'ying.",
            reply_markup=MainKeyboard.get_cancel_keyboard("uz")
        )
        return

    group_id = getattr(message, "media_group_id", None)
    if not group_id:
        await _process_post(message, state, session, text, [photo] if photo else [], _origin_name(message))
        return

    key = (message.chat.id, group_id)
    entry = _albums.get(key)
    if entry is None:
        entry = _albums[key] = {"messages": [], "task": None}
    entry["messages"].append(message)
    if entry["task"] is not None:
        entry["task"].cancel()
    entry["task"] = asyncio.get_running_loop().create_task(_flush_album(key, state, lang))


async def _flush_album(key: tuple, state: FSMContext, lang: str):
    """Runs ALBUM_DEBOUNCE after the last album item: one import with all the photos."""
    try:
        await asyncio.sleep(ALBUM_DEBOUNCE)
    except asyncio.CancelledError:
        return
    entry = _albums.pop(key, None)
    if not entry or not entry["messages"]:
        return
    messages: List[Message] = entry["messages"]
    first = messages[0]
    text = next((_text_of(m) for m in messages if _text_of(m)), "")
    photos = [pid for pid in (_photo_id(m) for m in messages) if pid]
    origin = next((_origin_name(m) for m in messages if _origin_name(m)), None)
    try:
        # The handler's DB session is closed by now -> a session of our own
        async with async_session_maker() as session:
            await _process_post(first, state, session, text, photos, origin)
    except Exception as e:
        logger.error(f"Album import failed: {e}")
        try:
            await first.answer("⚠️ Albomni qayta ishlashda xatolik. Qaytadan yuboring.")
        except Exception:
            pass


async def _process_post(message: Message, state: FSMContext, session: AsyncSession,
                        text: str, photos: List[str], origin: Optional[str]):
    """Parse the post, fill the FSM like the manual flow would, then ask only what is missing."""
    data = await state.get_data()
    # Photos sent earlier without any text are kept and merged with this message
    photos = (list(data.get('import_photos') or []) + list(photos))[:settings.photos_per_ad]

    if not text:
        await state.update_data(import_photos=photos)
        await message.answer(
            f"🖼 {len(photos)} ta rasm qabul qilindi. Matnni ham yuboring (e'lon tavsifi, narx, telefon...).",
            reply_markup=MainKeyboard.get_cancel_keyboard("uz")
        )
        return

    if parse_listing_text is None or address_from is None:
        await state.clear()
        await message.answer("⚠️ Import moduli (listing_parser) topilmadi. Administratorga xabar bering.")
        return

    user = await UserService.get_by_telegram_id(session, message.chat.id)
    if user is None or not getattr(user, "is_registered", False):
        await state.clear()
        await message.answer(
            "⚠️ Import uchun avval botda ro'yxatdan o'ting: /start → 📝 Ro'yxatdan o'tish.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=False, lang="uz")
        )
        return

    try:
        parsed = parse_listing_text(text, settings.max_description_length)
    except Exception as e:  # the parser promises not to raise; stay safe anyway
        logger.error(f"parse_listing_text failed: {e}")
        await message.answer("⚠️ Matnni tahlil qilib bo'lmadi. Boshqa matn yuboring yoki ❌ Bekor qiling.")
        return

    try:
        address = address_from(parsed)
    except Exception as e:
        logger.error(f"address_from failed: {e}")
        address = None

    apartment_type = None
    if parsed.type in ("rent", "sale"):
        apartment_type = ApartmentType(parsed.type)

    description = (parsed.description or "").strip()[:settings.max_description_length] or None

    await state.set_data({
        'owner_id': user.id,
        'phone_number': parsed.phone or None,
        'admin_phone': getattr(user, "phone_number", None),
        'type': apartment_type,
        'rooms': parsed.rooms,
        'address': address,
        'latitude': None,
        'longitude': None,
        'price': parsed.price,
        'currency': parsed.currency or ('UZS' if parsed.price is not None else None),
        'area': parsed.area,
        'floor': parsed.floor,
        'total_floors': parsed.total_floors,
        'description': description,
        'photos': photos,
        'lang': 'uz',
        'import_mode': True,
        'import_complete': False,
        'editing': True,
        'import_source_chat': origin,
    })

    await message.answer(_summary(parsed, photos, address))
    await _import_next_missing(message, state, 'uz')


# ---------------------------------------------------------------------------
# waiting_for_phone (only reached when the post had no phone number)
# ---------------------------------------------------------------------------

@router.message(ImportStates.waiting_for_phone)
async def receive_import_phone(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    if await _handle_cancel(message, state, lang):
        return

    raw = message.contact.phone_number if message.contact else (message.text or "")
    phone = validate_phone_number(raw) if raw else None
    if not phone:
        await message.answer("⚠️ Raqam noto'g'ri. Masalan: +998901234567")
        await _ask_import_phone(message, state, lang)
        return

    await state.update_data(phone_number=phone)
    await _next_or_preview(message, state, _import_next_missing, lang)
