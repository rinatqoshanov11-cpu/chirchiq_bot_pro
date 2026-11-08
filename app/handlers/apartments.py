"""Apartment handlers (listing-creation flow, localized: uz / ru / en).

The whole form is driven by INLINE buttons attached to each step message (callback_data
prefix "lf:", see ApartmentKeyboard.inline_*). Typed answers still work where they make
sense (address detail, custom price, m², floor, description, phone) and the old reply-button
labels are still understood (is_text) so a stale keyboard in the chat does no harm.
The only reply keyboard left is Telegram's "share location" button at the location step.

After a tap the step message loses its buttons (and shows the chosen value), callbacks whose
state no longer matches are answered with a short "step is over" toast — so double taps and
old buttons are harmless. Every handler takes ``lang`` (injected by LanguageMiddleware).
The admin notification (notify_admins_new_apartment) stays Uzbek on purpose.
"""
import html
import math
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states import ApartmentStates, ImportStates
from app.services import UserService, ApartmentService
from app.keyboards import MainKeyboard, ApartmentKeyboard, InlineKeyboards
from app.models.apartment import ApartmentType
from app.utils import format_apartment_card, format_price, truncate_text, get_logger
from app.utils.price import resolve_price, PRICE_LIMITS
from app.utils.contact import admin_username, admin_link_html
from app.utils.areas import CHIRCHIQ_AREAS, OTHER_AREA, CITY, area_from_label, area_label
from app.i18n import DEFAULT_LANG, t, variants, is_text
from app.i18n.texts_listing import TAG_COUNT
from config import settings

logger = get_logger(__name__)
router = Router()


# Uzbek labels (kept for old code); matching uses is_text(text, "btn.cancel" / "btn.skip")
CANCEL = t("uz", "btn.cancel")
SKIP = t("uz", "btn.skip")

# States where "⏩ O'tkazib yuborish" (lf:skip) is allowed
SKIPPABLE_STATES = (
    ApartmentStates.waiting_for_address_detail,
    ApartmentStates.waiting_for_location,
    ApartmentStates.waiting_for_area,
    ApartmentStates.waiting_for_floor,
    ApartmentStates.waiting_for_total_floors,
    ApartmentStates.waiting_for_description,
)


def _type_key(data: dict) -> str:
    """'rent' or 'sale' (FSM data may hold the enum or its string value)."""
    value = data.get('type')
    return value.value if isinstance(value, ApartmentType) else str(value or "rent")


def _price_text(amount, currency, type_key: str, lang: str) -> str:
    """'3 000 000 so'm / oy' (rent gets the per-month suffix)."""
    text = format_price(amount, currency, lang=lang)
    if type_key == "rent":
        text += t(lang, "price.per_month")
    return text


def _contact_admin(lang: str) -> str:
    """'admin bilan bog'laning: @name' in ``lang`` (HTML)."""
    if admin_username():
        return t(lang, "listing.contact_admin_link", link=admin_link_html())
    return t(lang, "listing.contact_admin")


def _min_photos() -> int:
    return max(1, int(settings.min_photos_per_ad))


# ---------------------------------------------------------------------------
# Inline-step plumbing
# ---------------------------------------------------------------------------

async def _send_step(message: Message, state: FSMContext, text: str, keyboard, **extra) -> Message:
    """Send a step prompt with its inline keyboard and remember it (lf_msg) so the buttons can be removed later."""
    sent = await message.answer(text, reply_markup=keyboard, **extra)
    await state.update_data(lf_msg=sent.message_id)
    return sent


async def _freeze_step(message: Message, state: FSMContext, except_id: Optional[int] = None):
    """Remove the inline keyboard of the remembered step message (answer typed / step passed)."""
    data = await state.get_data()
    msg_id = data.get('lf_msg')
    if not msg_id:
        return
    await state.update_data(lf_msg=None)
    if msg_id == except_id:
        return
    try:
        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=msg_id, reply_markup=None)
    except Exception:
        pass


async def _choose(callback: CallbackQuery, state: FSMContext, lang: str, chosen: Optional[str] = None) -> Optional[Message]:
    """A step button was tapped: show the chosen value on the step message and drop its buttons.

    Returns the message to continue the dialogue with (None if Telegram gave no accessible message).
    """
    message = callback.message
    if not isinstance(message, Message):
        return None
    done = False
    if chosen is not None and message.text:
        try:
            await message.edit_text(f"{message.html_text}\n\n{t(lang, 'lf.chosen', value=html.escape(chosen))}")
            done = True
        except Exception:
            pass
    if not done:
        try:
            await message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
    await _freeze_step(message, state, except_id=message.message_id)
    return message


# ---------------------------------------------------------------------------
# Step prompts (used by the normal flow, by "✏️ Tahrirlash" and by the admin import)
# ---------------------------------------------------------------------------

async def _ask_type(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_type"), ApartmentKeyboard.inline_type(lang))
    await state.set_state(ApartmentStates.waiting_for_type)


async def _ask_rooms(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_rooms"), ApartmentKeyboard.inline_rooms(lang))
    await state.set_state(ApartmentStates.waiting_for_rooms)


async def _ask_address(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_address"), ApartmentKeyboard.inline_areas(lang))
    await state.set_state(ApartmentStates.waiting_for_address)


async def _ask_address_detail(message: Message, state: FSMContext, area: str, lang: str = DEFAULT_LANG):
    """``area`` is the canonical (Uzbek) area name; it is shown in ``lang``."""
    await _send_step(
        message, state,
        t(lang, "listing.ask_address_detail", area=html.escape(area_label(area, lang))),
        ApartmentKeyboard.inline_skip_cancel(lang),
    )
    await state.set_state(ApartmentStates.waiting_for_address_detail)


async def _ask_location(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """The one step with a reply keyboard (Telegram's location button); skip / cancel are inline."""
    await message.answer(t(lang, "listing.ask_location"), reply_markup=ApartmentKeyboard.location_reply_keyboard(lang))
    await _send_step(message, state, t(lang, "listing.location_or_skip"), ApartmentKeyboard.inline_skip_cancel(lang))
    await state.set_state(ApartmentStates.waiting_for_location)


async def _ask_price(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    type_key = _type_key(data)
    key = "listing.ask_price_rent" if type_key == "rent" else "listing.ask_price_sale"
    await _send_step(message, state, t(lang, key), ApartmentKeyboard.inline_price(type_key, lang))
    await state.set_state(ApartmentStates.waiting_for_price)


async def _ask_area(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    await _send_step(message, state, t(lang, "listing.ask_area"), ApartmentKeyboard.inline_m2(data.get('rooms'), lang))
    await state.set_state(ApartmentStates.waiting_for_area)


async def _ask_floor(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_floor"), ApartmentKeyboard.inline_floor(lang))
    await state.set_state(ApartmentStates.waiting_for_floor)


async def _ask_total_floors(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    await _send_step(
        message, state, t(lang, "listing.ask_total_floors"), ApartmentKeyboard.inline_tf(data.get('floor'), lang)
    )
    await state.set_state(ApartmentStates.waiting_for_total_floors)


def description_tags(type_key: str, lang: str = DEFAULT_LANG) -> list:
    """Tick-box features for the description (different for rent and sale), in ``lang``.

    Index i is the same feature in every language (chips are stored as indexes in FSM).
    """
    kind = type_key if type_key in TAG_COUNT else "rent"
    return [t(lang, f"listing.tag_{kind}_{i}") for i in range(TAG_COUNT[kind])]


# Uzbek chips (kept for old code)
DESCRIPTION_TAGS = {kind: description_tags(kind, "uz") for kind in TAG_COUNT}


def _description_tags_keyboard(type_key: str, selected: list, lang: str = DEFAULT_LANG):
    """Inline chips (tapped ones get a ✅) + done / skip / cancel."""
    return ApartmentKeyboard.inline_description(description_tags(type_key, lang), selected, lang)


async def _ask_description(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    type_key = _type_key(data)
    await state.update_data(desc_tags=[])
    chips = await _send_step(
        message, state,
        t(lang, "listing.ask_description") + "\n\n" + t(lang, "listing.chips_hint"),
        _description_tags_keyboard(type_key, [], lang),
    )
    await state.update_data(desc_chips_msg=chips.message_id)
    await state.set_state(ApartmentStates.waiting_for_description)


async def _ask_photos(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Photos prompt; the photos already in the FSM (import / nothing) are counted in."""
    data = await state.get_data()
    count = len(data.get('photos') or [])
    text = t(lang, "listing.ask_photos", min=_min_photos(), max=settings.photos_per_ad)
    if count:
        text += "\n\n" + t(lang, "listing.photos_have", n=count)
    sent = await _send_step(
        message, state, text, ApartmentKeyboard.inline_photos(count, _min_photos(), settings.photos_per_ad, lang)
    )
    await state.update_data(photos_status_msg=sent.message_id)
    await state.set_state(ApartmentStates.waiting_for_photos)


# ---------------------------------------------------------------------------
# Admin "forward import" mode (app/handlers/import_listing.py fills the FSM, then
# only the REQUIRED fields the parser could not find are asked here)
# ---------------------------------------------------------------------------

def _import_in_progress(data: dict) -> bool:
    """True while an imported listing still has required fields to fill."""
    return bool(data.get('import_mode')) and not data.get('import_complete')


def _import_price_ok(data: dict) -> bool:
    """A parsed price counts only when it fits the limits of the (now known) type."""
    price = data.get('price')
    if price is None:
        return False
    limits = PRICE_LIMITS.get((_type_key(data), data.get('currency') or 'UZS'))
    if not limits:
        return False
    low, high = limits
    return low <= price <= high


async def _ask_import_phone(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Import mode: contact phone not found in the post -> admin's own number as a one-tap inline button."""
    data = await state.get_data()
    await _send_step(
        message, state,
        t(lang, "listing.import_ask_phone"),
        ApartmentKeyboard.inline_import_phone(data.get('admin_phone'), lang),
    )
    await state.set_state(ImportStates.waiting_for_phone)


async def _import_next_missing(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Ask the first REQUIRED field the parser did not find; when none is missing -> preview.

    Order: type -> rooms -> address -> price -> phone -> photos (at least settings.min_photos_per_ad).
    """
    data = await state.get_data()
    photos = data.get('photos') or []
    if not data.get('type'):
        await _ask_type(message, state, lang)
    elif not data.get('rooms'):
        await _ask_rooms(message, state, lang)
    elif not data.get('address'):
        await _ask_address(message, state, lang)
    elif not _import_price_ok(data):
        if data.get('price') is not None:
            await message.answer("⚠️ Topilgan narx tanlangan tur uchun mos emas, qaytadan kiriting.")
            await state.update_data(price=None)
        await _ask_price(message, state, lang)
    elif not data.get('phone_number'):
        await _ask_import_phone(message, state, lang)
    elif len(photos) < _min_photos():
        if photos:
            await message.answer(t(lang, "listing.import_photos_more", k=len(photos), min=_min_photos()))
        await _ask_photos(message, state, lang)
    else:
        await state.update_data(import_complete=True, editing=False)
        await _show_preview(message, state, lang)


async def _show_preview(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Show how the listing will look, with inline ✅ / ✏️ / ❌ buttons."""
    data = await state.get_data()
    type_key = _type_key(data)
    type_text = t(lang, "listing.badge_rent" if type_key == "rent" else "listing.badge_sale")
    price_text = _price_text(data['price'], data.get('currency', 'UZS'), type_key, lang)

    preview = t(lang, "listing.preview_title") + "\n\n"
    preview += f"<b>{type_text} · {t(lang, 'listing.rooms_n', n=data['rooms'])}</b>\n"
    preview += f"💵 <b>{price_text}</b>\n"
    preview += f"📍 {html.escape(truncate_text(data['address'], 150))}\n"
    if data.get('latitude') is not None:
        preview += t(lang, "listing.on_map") + "\n"

    if data.get('area'):
        preview += t(lang, "listing.area_value", area=f"{data['area']:g}") + "\n"

    if data.get('floor'):
        floor_text = f"{data['floor']} / {data['total_floors']}" if data.get('total_floors') else str(data['floor'])
        preview += t(lang, "listing.floor_value", floor=floor_text) + "\n"

    if data.get('description'):
        # Caption limit is 1024, description can be up to 1000 -> keep it short here
        preview += f"\n📝 <i>{html.escape(truncate_text(data['description'], 300))}</i>\n"

    preview += "\n" + t(lang, "listing.photos_count", n=len(data.get('photos', []))) + "\n\n"
    preview += t(lang, "listing.preview_hint")

    keyboard = ApartmentKeyboard.inline_confirm(lang)
    try:
        sent = await message.answer_photo(photo=data['photos'][0], caption=preview, reply_markup=keyboard)
    except Exception as e:
        # Caption too long (e.g. emoji-heavy text): send photo and text separately
        logger.warning(f"Preview caption failed, sending separately: {e}")
        if data.get('photos'):
            try:
                await message.answer_photo(photo=data['photos'][0])
            except Exception:
                pass
        sent = await message.answer(preview, reply_markup=keyboard)
    await state.update_data(lf_msg=sent.message_id)
    await state.set_state(ApartmentStates.confirm_apartment)


async def _next_or_preview(message: Message, state: FSMContext, next_step, lang: str = DEFAULT_LANG):
    """After a field is saved: in edit mode go back to the preview, otherwise continue."""
    data = await state.get_data()
    if data.get('editing') and _import_in_progress(data):
        # Import mode: keep asking only the required fields that are still missing
        await _import_next_missing(message, state, lang)
        return
    if data.get('editing'):
        await state.update_data(editing=False, photos_backup=None, type_backup=None, floor_backup=None, address_backup=None)
        await message.answer(t(lang, "listing.changed"), reply_markup=ReplyKeyboardRemove())
        await _show_preview(message, state, lang)
    else:
        await next_step(message, state, lang)


async def _cancel_flow(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Cancel: in edit mode undo just this change, in the edit menu go back, otherwise drop the listing."""
    current = await state.get_state()
    data = await state.get_data()
    if current == ApartmentStates.choosing_edit_field.state:
        await _show_preview(message, state, lang)
        return
    if _import_in_progress(data):
        await state.clear()
        await message.answer(
            "❌ Import bekor qilindi.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )
        return
    if data.get('editing'):
        restore = {'editing': False}
        if data.get('photos_backup') is not None:
            restore.update(photos=data['photos_backup'], photos_backup=None)
        if data.get('type_backup') is not None:
            # Type was changed and the new price was not given -> put the old type back
            restore.update(type=data['type_backup'], type_backup=None)
        if data.get('address_backup') is not None:
            old_address, old_lat, old_lon = data['address_backup']
            restore.update(address=old_address, latitude=old_lat, longitude=old_lon, address_backup=None)
        if data.get('floor_backup') is not None:
            # Floor was changed but the building height step was cancelled -> old floor/height back
            old_floor, old_total = data['floor_backup']
            restore.update(floor=old_floor, total_floors=old_total, floor_backup=None)
        await state.update_data(**restore)
        await message.answer(t(lang, "listing.change_cancelled"), reply_markup=ReplyKeyboardRemove())
        await _show_preview(message, state, lang)
    else:
        await state.clear()
        await message.answer(
            t(lang, "listing.cancelled"),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )


async def _handle_cancel(message: Message, state: FSMContext, lang: str = DEFAULT_LANG) -> bool:
    """Typed '❌ Bekor qilish' (any language, e.g. from an old reply keyboard)."""
    if not is_text(message.text, "btn.cancel"):
        return False
    await _freeze_step(message, state)
    await _cancel_flow(message, state, lang)
    return True


# ---------------------------------------------------------------------------
# Generic inline buttons: cancel (every listing / import-phone state) and skip
# ---------------------------------------------------------------------------

@router.callback_query(StateFilter(ApartmentStates, ImportStates.waiting_for_phone), F.data == "lf:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    message = await _choose(callback, state, lang)
    if message:
        await _cancel_flow(message, state, lang)


@router.callback_query(StateFilter(*SKIPPABLE_STATES), F.data == "lf:skip")
async def cb_skip(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    current = await state.get_state()
    message = await _choose(callback, state, lang, t(lang, "btn.skip"))
    if not message:
        return
    if current == ApartmentStates.waiting_for_address_detail.state:
        await _set_address_detail(message, state, lang, None)
    elif current == ApartmentStates.waiting_for_location.state:
        await message.answer(t(lang, "listing.location_skipped"), reply_markup=ReplyKeyboardRemove())
        await _set_location(message, state, lang, None, None)
    elif current == ApartmentStates.waiting_for_area.state:
        await _set_area(message, state, lang, None)
    elif current == ApartmentStates.waiting_for_floor.state:
        await _set_floor(message, state, lang, None, None)
    elif current == ApartmentStates.waiting_for_total_floors.state:
        await _set_total_floors(message, state, lang, None)
    elif current == ApartmentStates.waiting_for_description.state:
        await _finish_description(message, state, lang, None)


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

@router.message(F.text.in_(variants("btn.add_listing")))
async def start_add_apartment(message: Message, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    """Start adding new apartment."""
    user = await UserService.get_by_telegram_id(session, message.from_user.id)

    if not user or not user.is_registered:
        await message.answer(
            t(lang, "listing.need_register"),
            reply_markup=MainKeyboard.get_main_menu(is_registered=False, lang=lang)
        )
        return

    if user.is_blocked:
        await message.answer(t(lang, "listing.blocked", contact=_contact_admin(lang)))
        return

    await state.clear()

    await state.update_data(owner_id=user.id, phone_number=user.phone_number)

    # The form is inline from here on: hide the main-menu reply keyboard
    await message.answer(t(lang, "listing.new"), reply_markup=ReplyKeyboardRemove())
    await _ask_type(message, state, lang)


# ---------------------------------------------------------------------------
# Type
# ---------------------------------------------------------------------------

async def _set_type(message: Message, state: FSMContext, lang: str, type_value: str):
    apartment_type = ApartmentType(type_value)
    data = await state.get_data()
    old_type = _type_key(data) if data.get('type') else None

    # Type changed while editing and a price exists -> the price must be re-entered
    if data.get('editing') and data.get('price') and old_type and old_type != apartment_type.value:
        await state.update_data(type=apartment_type, type_backup=data.get('type'))
        await message.answer(t(lang, "listing.type_changed"))
        await _ask_price(message, state, lang)
        return

    await state.update_data(type=apartment_type)
    await _next_or_preview(message, state, _ask_rooms, lang)


@router.callback_query(ApartmentStates.waiting_for_type, F.data.startswith("lf:type:"))
async def cb_type(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    type_value = callback.data.removeprefix("lf:type:")
    if type_value not in ("rent", "sale"):
        return
    label = t(lang, "btn.type_rent" if type_value == "rent" else "btn.type_sale")
    message = await _choose(callback, state, lang, label)
    if message:
        await _set_type(message, state, lang, type_value)


@router.message(ApartmentStates.waiting_for_type)
async def process_apartment_type(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed type label (old reply keyboard) or cancel."""
    if await _handle_cancel(message, state, lang):
        return
    type_value = ApartmentKeyboard.type_from_text(message.text)
    if not type_value:
        await message.answer(t(lang, "listing.type_invalid"))
        return
    await _freeze_step(message, state)
    await _set_type(message, state, lang, type_value)


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

async def _set_rooms(message: Message, state: FSMContext, lang: str, rooms: int):
    await state.update_data(rooms=rooms)
    await _next_or_preview(message, state, _ask_address, lang)


@router.callback_query(ApartmentStates.waiting_for_rooms, F.data.startswith("lf:rooms:"))
async def cb_rooms(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    try:
        rooms = int(callback.data.removeprefix("lf:rooms:"))
        if not 1 <= rooms <= 6:
            raise ValueError
    except ValueError:
        return
    message = await _choose(callback, state, lang, "6+" if rooms == 6 else str(rooms))
    if message:
        await _set_rooms(message, state, lang, rooms)


@router.message(ApartmentStates.waiting_for_rooms)
async def process_rooms(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed number of rooms ('3', '6+')."""
    if await _handle_cancel(message, state, lang):
        return
    text = (message.text or "").strip()
    try:
        rooms = 6 if text == "6+" else int(text)
        if rooms < 1 or rooms > 10:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "listing.rooms_invalid"))
        return
    await _freeze_step(message, state)
    await _set_rooms(message, state, lang, rooms)


# ---------------------------------------------------------------------------
# Address: area button -> street/house (optional) -> location
# ---------------------------------------------------------------------------

async def _set_address(message: Message, state: FSMContext, lang: str, address: str):
    await state.update_data(address=address[:300], address_area=None)
    await _ask_location(message, state, lang)


async def _ask_full_address(message: Message, state: FSMContext, lang: str):
    """'✍️ Boshqa hudud': the whole address is typed (state stays waiting_for_address)."""
    await state.update_data(address_area=None)
    await _send_step(message, state, t(lang, "listing.ask_full_address"), ApartmentKeyboard.inline_cancel(lang))


@router.callback_query(ApartmentStates.waiting_for_address, F.data.startswith("lf:area:"))
async def cb_area(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    value = callback.data.removeprefix("lf:area:")
    if value == "other":
        message = await _choose(callback, state, lang, t(lang, "btn.other_area"))
        if message:
            await _ask_full_address(message, state, lang)
        return
    try:
        area = CHIRCHIQ_AREAS[int(value)]
    except (ValueError, IndexError):
        return
    message = await _choose(callback, state, lang, area_label(area, lang))
    if not message:
        return
    # FSM keeps the canonical (Uzbek) name; the address is written in the poster's language
    await state.update_data(address_area=area)
    await _ask_address_detail(message, state, area, lang)


@router.message(ApartmentStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed area name -> ask street/house; '✍️ Boshqa hudud' label or free text -> full address."""
    if await _handle_cancel(message, state, lang):
        return

    text = (message.text or "").strip()

    area = area_from_label(text)
    if area:
        await _freeze_step(message, state)
        await state.update_data(address_area=area)
        await _ask_address_detail(message, state, area, lang)
        return

    if is_text(text, "btn.other_area"):
        await _freeze_step(message, state)
        await _ask_full_address(message, state, lang)
        return

    if len(text) < 5:
        await message.answer(t(lang, "listing.address_invalid"))
        return

    # Free text: add the city name if the user didn't (checked in every language)
    lowered = text.lower()
    has_city = any(name.lower() in lowered for name in variants("city"))
    address = text if has_city else f"{t(lang, 'city')}, {text}"
    await _freeze_step(message, state)
    await _set_address(message, state, lang, address)


async def _set_address_detail(message: Message, state: FSMContext, lang: str, detail: Optional[str]):
    data = await state.get_data()
    area = area_label(data.get('address_area') or "", lang)
    city = t(lang, "city")
    address = f"{city}, {area}, {detail}" if detail else f"{city}, {area}"
    await _set_address(message, state, lang, address)


@router.message(ApartmentStates.waiting_for_address_detail)
async def process_address_detail(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Street / house after an area button (optional)."""
    if await _handle_cancel(message, state, lang):
        return
    if is_text(message.text, "btn.skip"):
        detail = None
    else:
        detail = (message.text or "").strip()
        if len(detail) < 2:
            await message.answer(t(lang, "listing.address_detail_invalid"))
            return
    await _freeze_step(message, state)
    await _set_address_detail(message, state, lang, detail)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

async def _set_location(message: Message, state: FSMContext, lang: str, lat, lon):
    await state.update_data(latitude=lat, longitude=lon)
    await _next_or_preview(message, state, _ask_price, lang)


@router.message(ApartmentStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """A shared location (pin / venue) or the typed skip label."""
    if await _handle_cancel(message, state, lang):
        return

    location = message.location or (message.venue.location if message.venue else None)
    if location:
        await _freeze_step(message, state)
        await message.answer(t(lang, "listing.location_saved"), reply_markup=ReplyKeyboardRemove())
        await _set_location(message, state, lang, location.latitude, location.longitude)
    elif is_text(message.text, "btn.skip"):
        await _freeze_step(message, state)
        await message.answer(t(lang, "listing.location_skipped"), reply_markup=ReplyKeyboardRemove())
        await _set_location(message, state, lang, None, None)
    else:
        await message.answer(t(lang, "listing.location_invalid"))


# ---------------------------------------------------------------------------
# Price
# ---------------------------------------------------------------------------

async def _set_price(message: Message, state: FSMContext, lang: str, amount, currency, guessed_usd: bool = False,
                     announce: bool = True):
    data = await state.get_data()
    type_key = _type_key(data)
    await state.update_data(price=amount, currency=currency)
    note = t(lang, "listing.price_guessed_usd") if guessed_usd else ""
    if (announce and not data.get('editing')) or note:
        shown = _price_text(amount, currency, type_key, lang)
        await message.answer(t(lang, "listing.price_saved", price=shown, note=note))
    await _next_or_preview(message, state, _ask_area, lang)


@router.callback_query(ApartmentStates.waiting_for_price, F.data.startswith("lf:price:"))
async def cb_price(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    data = await state.get_data()
    type_key = _type_key(data)
    try:
        amount_text, currency = callback.data.removeprefix("lf:price:").split(":", 1)
        amount = int(amount_text)
        low, high = PRICE_LIMITS[(type_key, currency)]
        if not low <= amount <= high:
            raise ValueError
    except (ValueError, KeyError):
        return
    message = await _choose(callback, state, lang, _price_text(amount, currency, type_key, lang))
    if message:
        await _set_price(message, state, lang, amount, currency, announce=False)


@router.message(ApartmentStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed price: '3 mln', '500 ming', '3 млн', '$45 000', '1 500 000'..."""
    if await _handle_cancel(message, state, lang):
        return

    data = await state.get_data()
    type_key = _type_key(data)
    amount, currency, error = resolve_price(message.text or "", type_key)

    if error and error != "guessed_usd":
        if error == "not_a_number":
            reason = t(lang, "listing.price_not_a_number")
        else:
            low, high = PRICE_LIMITS[(type_key, currency)]
            size = "too_low" if error == "too_low" else "too_high"
            kind = "rent" if type_key == "rent" else "sale"
            reason = t(
                lang, f"listing.price_{size}_{kind}",
                amount=format_price(amount, currency, lang=lang),
                low=format_price(low, currency, lang=lang),
                high=format_price(high, currency, lang=lang),
            )
        await message.answer(t(lang, "listing.price_retry", reason=reason))
        return

    await _freeze_step(message, state)
    await _set_price(message, state, lang, amount, currency, guessed_usd=(error == "guessed_usd"))


# ---------------------------------------------------------------------------
# Area (m²)
# ---------------------------------------------------------------------------

async def _set_area(message: Message, state: FSMContext, lang: str, area: Optional[float]):
    await state.update_data(area=area)
    await _next_or_preview(message, state, _ask_floor, lang)


@router.callback_query(ApartmentStates.waiting_for_area, F.data.startswith("lf:m2:"))
async def cb_m2(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    try:
        area = float(callback.data.removeprefix("lf:m2:"))
        if not math.isfinite(area) or area < 5 or area > 1000:
            raise ValueError
    except ValueError:
        return
    message = await _choose(callback, state, lang, t(lang, "btn.area_m2", n=f"{area:g}"))
    if message:
        await _set_area(message, state, lang, area)


@router.message(ApartmentStates.waiting_for_area)
async def process_area(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed area ('65', '65 m²', '65 м²') or the skip label."""
    if await _handle_cancel(message, state, lang):
        return
    if is_text(message.text, "btn.skip"):
        area = None
    else:
        area = ApartmentKeyboard.parse_area_text(message.text)
        if area is None or not math.isfinite(area) or area < 5 or area > 1000:
            await message.answer(t(lang, "listing.area_invalid"))
            return
    await _freeze_step(message, state)
    await _set_area(message, state, lang, area)


# ---------------------------------------------------------------------------
# Floor / building height
# ---------------------------------------------------------------------------

async def _set_floor(message: Message, state: FSMContext, lang: str, floor: Optional[int], total_floors: Optional[int]):
    """floor None -> skipped; total known -> on to the description; else ask the building height."""
    if floor is None or total_floors is not None:
        await state.update_data(floor=floor, total_floors=total_floors)
        await _next_or_preview(message, state, _ask_description, lang)
        return
    await state.update_data(floor=floor, total_floors=None)
    await _ask_total_floors(message, state, lang)


@router.callback_query(ApartmentStates.waiting_for_floor, F.data.startswith("lf:floor:"))
async def cb_floor(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    try:
        floor = int(callback.data.removeprefix("lf:floor:"))
        if not 1 <= floor <= 100:
            raise ValueError
    except ValueError:
        return
    message = await _choose(callback, state, lang, str(floor))
    if message:
        await _set_floor(message, state, lang, floor, None)


@router.message(ApartmentStates.waiting_for_floor)
async def process_floor(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed '5/9' / '5', or the skip label."""
    if await _handle_cancel(message, state, lang):
        return
    if is_text(message.text, "btn.skip"):
        await _freeze_step(message, state)
        await _set_floor(message, state, lang, None, None)
        return

    text = (message.text or "").strip()
    try:
        if "/" in text:
            left, right = text.split("/", 1)
            floor, total_floors = int(left.strip()), int(right.strip())
            if not (1 <= floor <= 100) or not (1 <= total_floors <= 100) or total_floors < floor:
                raise ValueError
        else:
            floor, total_floors = int(text), None
            if not (1 <= floor <= 100):
                raise ValueError
    except ValueError:
        await message.answer(t(lang, "listing.floor_invalid"))
        return

    await _freeze_step(message, state)
    await _set_floor(message, state, lang, floor, total_floors)


async def _set_total_floors(message: Message, state: FSMContext, lang: str, total_floors: Optional[int]):
    await state.update_data(total_floors=total_floors)
    await _next_or_preview(message, state, _ask_description, lang)


@router.callback_query(ApartmentStates.waiting_for_total_floors, F.data.startswith("lf:tf:"))
async def cb_total_floors(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    data = await state.get_data()
    floor = data.get('floor') or 0
    try:
        total_floors = int(callback.data.removeprefix("lf:tf:"))
        if total_floors < max(floor, 1) or total_floors > 100:
            raise ValueError
    except ValueError:
        return
    message = await _choose(callback, state, lang, t(lang, "btn.total_floors_n", n=total_floors))
    if message:
        await _set_total_floors(message, state, lang, total_floors)


@router.message(ApartmentStates.waiting_for_total_floors)
async def process_total_floors(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed building height ('9', '9 qavatli') or the skip label."""
    if await _handle_cancel(message, state, lang):
        return
    data = await state.get_data()
    floor = data.get('floor') or 0
    if is_text(message.text, "btn.skip"):
        total_floors = None
    else:
        total_floors = ApartmentKeyboard.parse_total_floors_text(message.text)
        if total_floors is None or total_floors < max(floor, 1) or total_floors > 100:
            await message.answer(t(lang, "listing.total_floors_invalid", floor=floor))
            return
    await _freeze_step(message, state)
    await _set_total_floors(message, state, lang, total_floors)


# ---------------------------------------------------------------------------
# Description: chips (dtag_N) + ✅ done / skip, or typed text
# ---------------------------------------------------------------------------

def _selected_tags(data: dict, lang: str) -> list:
    all_tags = description_tags(_type_key(data), lang)
    return [all_tags[i] for i in sorted(data.get('desc_tags') or []) if 0 <= i < len(all_tags)]


async def _finish_description(message: Message, state: FSMContext, lang: str, description: Optional[str]):
    data = await state.get_data()
    await state.update_data(description=description, desc_tags=None, desc_chips_msg=None)

    # Freeze the chips message so old chips can't be tapped later
    if data.get('desc_chips_msg') and data.get('desc_chips_msg') != message.message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id, message_id=data['desc_chips_msg'], reply_markup=None
            )
        except Exception:
            pass

    if data.get('editing'):
        await _next_or_preview(message, state, _ask_photos, lang)
    else:
        await state.update_data(photos=[])
        await _ask_photos(message, state, lang)


@router.callback_query(ApartmentStates.waiting_for_description, F.data.startswith("dtag_"))
async def toggle_description_tag(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    """Tick / untick a feature chip."""
    data = await state.get_data()
    type_key = _type_key(data)
    try:
        index = int(callback.data.removeprefix("dtag_"))
        if not 0 <= index < len(description_tags(type_key, lang)):
            raise ValueError
    except (ValueError, KeyError):
        await callback.answer()
        return

    selected = list(data.get('desc_tags') or [])
    if index in selected:
        selected.remove(index)
    else:
        selected.append(index)
    await state.update_data(desc_tags=selected)

    try:
        await callback.message.edit_reply_markup(
            reply_markup=_description_tags_keyboard(type_key, selected, lang)
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(ApartmentStates.waiting_for_description, F.data == "lf:done")
async def cb_description_done(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    """'✅ Tayyor' under the chips -> the ticked chips become the description."""
    await callback.answer()
    data = await state.get_data()
    description = " · ".join(_selected_tags(data, lang)) or None
    message = await _choose(callback, state, lang, t(lang, "btn.done"))
    if message:
        await _finish_description(message, state, lang, description)


@router.message(ApartmentStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Free text -> chips + text; typed done -> chips only; typed skip -> nothing."""
    if await _handle_cancel(message, state, lang):
        return

    data = await state.get_data()
    tags = _selected_tags(data, lang)

    if is_text(message.text, "btn.skip"):
        description = None
    elif is_text(message.text, "btn.done"):
        description = " · ".join(tags) or None
    else:
        extra = (message.text or "").strip()
        if not extra:
            await message.answer(t(lang, "listing.description_empty"))
            return
        description = " · ".join(tags) + ("\n" if tags else "") + extra

    if description and len(description) > settings.max_description_length:
        await message.answer(
            t(lang, "listing.description_too_long", n=len(description), max=settings.max_description_length)
        )
        return

    await _freeze_step(message, state)
    await _finish_description(message, state, lang, description)


# ---------------------------------------------------------------------------
# Photos (at least settings.min_photos_per_ad, at most settings.photos_per_ad)
# ---------------------------------------------------------------------------

async def _photos_status(message: Message, state: FSMContext, lang: str, photos: list):
    """One status message 'N/10 qabul qilindi' with the done button; edited after every photo."""
    data = await state.get_data()
    n, minimum, maximum = len(photos), _min_photos(), settings.photos_per_ad
    hint = t(lang, "listing.photos_need_more", more=minimum - n) if n < minimum else t(lang, "listing.photos_enough")
    text = t(lang, "listing.photos_progress", n=n, max=maximum, hint=hint)
    keyboard = ApartmentKeyboard.inline_photos(n, minimum, maximum, lang)

    status_id = data.get('photos_status_msg')
    if status_id and status_id != data.get('lf_msg'):
        # A status message exists already (the prompt itself is never rewritten) -> edit it
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id, message_id=status_id, text=text, reply_markup=keyboard
            )
            return
        except Exception:
            pass
    # First photo (or the status message is gone): drop the prompt's buttons, send the status message
    await _freeze_step(message, state)
    sent = await message.answer(text, reply_markup=keyboard)
    await state.update_data(photos_status_msg=sent.message_id)


@router.message(ApartmentStates.waiting_for_photos, F.photo)
async def process_photo(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Collect photos; progress is shown by editing one status message."""
    data = await state.get_data()
    photos = list(data.get('photos') or [])

    if len(photos) >= settings.photos_per_ad:
        await message.answer(t(lang, "listing.photos_limit", max=settings.photos_per_ad))
        return

    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await _photos_status(message, state, lang, photos)


async def _finish_photos(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    status_id = data.get('photos_status_msg')
    if status_id and status_id != message.message_id:
        # Typed '✅ Tayyor': the status message still shows the done button -> drop it
        try:
            await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=status_id, reply_markup=None)
        except Exception:
            pass
    await state.update_data(
        editing=False, photos_backup=None, type_backup=None, floor_backup=None, address_backup=None,
        photos_status_msg=None,
    )
    if data.get('import_mode'):
        # Photos are the last required field in import mode -> the import is complete
        await state.update_data(import_complete=True)
    await _show_preview(message, state, lang)


@router.callback_query(ApartmentStates.waiting_for_photos, F.data == "lf:photos_done")
async def cb_photos_done(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    """'✅ Tayyor' -> preview (refused while there are fewer than the minimum photos)."""
    data = await state.get_data()
    count = len(data.get('photos') or [])
    if count < _min_photos():
        await callback.answer(t(lang, "listing.photos_required", n=_min_photos(), k=count), show_alert=True)
        return
    await callback.answer()
    message = await _choose(callback, state, lang)
    if message:
        await _finish_photos(message, state, lang)


@router.message(ApartmentStates.waiting_for_photos, F.text.in_(variants("btn.done")))
async def photos_done(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed '✅ Tayyor' (old reply keyboard)."""
    data = await state.get_data()
    count = len(data.get('photos') or [])
    if count < _min_photos():
        await message.answer(t(lang, "listing.photos_required", n=_min_photos(), k=count))
        return
    await _freeze_step(message, state)
    await _finish_photos(message, state, lang)


@router.message(ApartmentStates.waiting_for_photos)
async def invalid_photo_input(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Handle anything else during photo upload."""
    if await _handle_cancel(message, state, lang):
        return
    await message.answer(t(lang, "listing.photos_invalid"))


# ---------------------------------------------------------------------------
# Preview: ✅ confirm / ✏️ edit / ❌ cancel
# ---------------------------------------------------------------------------

async def _save_listing(message: Message, state: FSMContext, session: AsyncSession, lang: str):
    """Save the listing (manual: pending + admins notified; import: approved at once)."""
    data = await state.get_data()
    import_mode = bool(data.get('import_mode'))
    # Leave the confirm state BEFORE saving, so a quick second tap can't save twice
    await state.set_state(None)

    try:
        apartment = await ApartmentService.create_apartment(
            session=session,
            owner_id=data['owner_id'],
            apartment_type=data['type'],
            rooms=data['rooms'],
            address=data['address'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            price=data['price'],
            currency=data.get('currency', 'UZS'),
            phone_number=data['phone_number'],
            area=data.get('area'),
            floor=data.get('floor'),
            total_floors=data.get('total_floors'),
            description=data.get('description'),
            photos=data.get('photos', []),
            source='import' if import_mode else 'manual'
        )

        if import_mode:
            # The admin posted it -> published at once, no admin notification
            await ApartmentService.approve_apartment(session, apartment)

        await state.clear()

        is_rent = apartment.type == ApartmentType.RENT
        type_text = t(lang, "listing.success_type_rent" if is_rent else "listing.success_type_sale")
        price_text = _price_text(apartment.price, apartment.currency, "rent" if is_rent else "sale", lang)

        if import_mode:
            uz_type = "🔑 Ijaraga" if is_rent else "💰 Sotiladi"
            uz_price = _price_text(apartment.price, apartment.currency, "rent" if is_rent else "sale", "uz")
            await message.answer(
                f"✅ <b>Import qilingan e'lon #{apartment.id} darhol e'lon qilindi.</b>\n\n"
                f"{uz_type} · {apartment.rooms} xonali\n"
                f"💵 {uz_price}\n"
                f"📍 {html.escape(truncate_text(apartment.address, 150))}",
                reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
            )
            logger.info(f"Imported apartment approved: #{apartment.id} by admin user {data['owner_id']}")
            return

        await message.answer(
            t(lang, "listing.success",
              id=apartment.id,
              type=type_text,
              rooms=t(lang, "listing.rooms_n", n=apartment.rooms),
              price=price_text),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )

        logger.info(f"New apartment added: #{apartment.id} by user {data['owner_id']}")

        await notify_admins_new_apartment(message.bot, session, apartment)

    except Exception as e:
        logger.error(f"Error creating apartment: {e}")
        await message.answer(
            t(lang, "listing.save_error"),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )
        await state.clear()


async def _open_edit_menu(message: Message, state: FSMContext, lang: str):
    await _send_step(message, state, t(lang, "listing.edit_menu"), ApartmentKeyboard.inline_edit_fields(lang))
    await state.set_state(ApartmentStates.choosing_edit_field)


@router.callback_query(ApartmentStates.confirm_apartment, F.data == "lf:confirm")
async def cb_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    await callback.answer()
    message = await _choose(callback, state, lang)
    if message:
        await _save_listing(message, state, session, lang)


@router.callback_query(ApartmentStates.confirm_apartment, F.data == "lf:edit")
async def cb_edit(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    message = await _choose(callback, state, lang)
    if message:
        await _open_edit_menu(message, state, lang)


@router.message(ApartmentStates.confirm_apartment)
async def confirm_apartment(message: Message, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    """Typed ✅ / ✏️ / ❌ labels (old reply keyboard)."""
    if await _handle_cancel(message, state, lang):
        return
    if is_text(message.text, "btn.edit"):
        await _freeze_step(message, state)
        await _open_edit_menu(message, state, lang)
        return
    if not is_text(message.text, "btn.confirm"):
        await message.answer(t(lang, "listing.confirm_invalid"))
        return
    await _freeze_step(message, state)
    await _save_listing(message, state, session, lang)


# ---------------------------------------------------------------------------
# Edit menu
# ---------------------------------------------------------------------------

async def _start_edit(message: Message, state: FSMContext, lang: str, field: str):
    """Remember what is needed to undo the change, then ask the field again."""
    await state.update_data(editing=True)
    data = await state.get_data()

    if field == "address":
        await state.update_data(address_backup=[data.get('address'), data.get('latitude'), data.get('longitude')])

    if field == "floor":
        # Keep old floor/height so cancelling at the building-height step can restore them
        await state.update_data(floor_backup=[data.get('floor'), data.get('total_floors')])

    if field == "photos":
        # Keep old photos so "❌ Bekor qilish" can restore them
        await state.update_data(photos_backup=data.get('photos', []), photos=[])
        await message.answer(t(lang, "listing.replace_photos"))

    prompts = {
        "type": _ask_type,
        "rooms": _ask_rooms,
        "address": _ask_address,
        "price": _ask_price,
        "area": _ask_area,
        "floor": _ask_floor,
        "description": _ask_description,
        "photos": _ask_photos,
    }
    await prompts[field](message, state, lang)


@router.callback_query(ApartmentStates.choosing_edit_field, F.data.startswith("lf:editf:"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    field = callback.data.removeprefix("lf:editf:")
    label_key = next((key for key, name in ApartmentKeyboard.EDIT_FIELD_KEYS.items() if name == field), None)
    if label_key is None:
        return
    message = await _choose(callback, state, lang, t(lang, label_key))
    if message:
        await _start_edit(message, state, lang, field)


@router.callback_query(ApartmentStates.choosing_edit_field, F.data == "lf:edit_back")
async def cb_edit_back(callback: CallbackQuery, state: FSMContext, lang: str = DEFAULT_LANG):
    await callback.answer()
    message = await _choose(callback, state, lang)
    if message:
        await _show_preview(message, state, lang)


@router.message(ApartmentStates.choosing_edit_field)
async def choose_edit_field(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Typed edit-field label (old reply keyboard)."""
    if is_text(message.text, "btn.edit_back") or is_text(message.text, "btn.cancel"):
        await _freeze_step(message, state)
        await _show_preview(message, state, lang)
        return
    field = ApartmentKeyboard.edit_field_from_text(message.text)
    if not field:
        await message.answer(t(lang, "listing.edit_field_invalid"))
        return
    await _freeze_step(message, state)
    await _start_edit(message, state, lang, field)


# ---------------------------------------------------------------------------
# Stale form buttons (double tap, old message): a quiet toast instead of the fallback alert.
# ImportStates.waiting_for_phone is left to import_listing.py (lf:phone:self lives there).
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("lf:"), ~StateFilter(ImportStates.waiting_for_phone))
async def stale_form_button(callback: CallbackQuery, lang: str = DEFAULT_LANG):
    await callback.answer(t(lang, "lf.stale"))


# ---------------------------------------------------------------------------
# Contact button under published listings
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("contact_"))
async def show_contact(callback: CallbackQuery, session: AsyncSession, lang: str = DEFAULT_LANG):
    """Show apartment contact information (plain-text alert)."""
    apartment_id = int(callback.data.split("_")[1])

    apartment = await ApartmentService.get_by_id(session, apartment_id)

    if not apartment:
        await callback.answer(t(lang, "listing.not_found"), show_alert=True)
        return

    # Increment contact count
    apartment.contact_count += 1
    await session.commit()

    contact_text = t(lang, "listing.contact_title") + "\n\n"
    contact_text += t(lang, "listing.contact_phone", phone=apartment.phone_number) + "\n"

    if apartment.contact_name:
        contact_text += t(lang, "listing.contact_name", name=apartment.contact_name) + "\n"

    await callback.answer(contact_text, show_alert=True)


async def notify_admins_new_apartment(bot, session: AsyncSession, apartment):
    """Notify admins about new apartment (admin texts stay Uzbek)."""
    from config import settings

    admin_ids = settings.admin_ids

    if not admin_ids:
        return

    type_text = "🔑 Ijaraga" if apartment.type == ApartmentType.RENT else "💰 Sotiladi"

    text = "🔔 <b>Yangi e'lon tasdiqlashni kutmoqda</b>\n\n"
    text += f"🆔 <b>#{apartment.id}</b> · {type_text} · {apartment.rooms} xonali\n"
    price_text = format_price(apartment.price, apartment.currency)
    if apartment.type == ApartmentType.RENT:
        price_text += " / oy"
    text += f"💵 <b>{price_text}</b>\n"
    text += f"📍 {html.escape(truncate_text(apartment.address, 150))}\n"
    if apartment.latitude is not None and apartment.longitude is not None:
        text += (f'🗺 <a href="https://maps.google.com/?q={apartment.latitude},{apartment.longitude}">'
                 'Xaritada ko\'rish</a>\n')
    if apartment.description:
        text += f"\n📝 <i>{html.escape(truncate_text(apartment.description, 300))}</i>\n"

    keyboard = InlineKeyboards.get_apartment_actions(
        apartment.id,
        show_admin=True,
        is_pending=True
    )

    for admin_id in admin_ids:
        try:
            if apartment.photos:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=apartment.photos[0],
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {e}")
