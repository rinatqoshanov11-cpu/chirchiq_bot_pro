"""Apartment handlers (listing-creation flow, localized: uz / ru / en).

Every handler takes ``lang`` (injected by LanguageMiddleware) and passes it explicitly to the
_ask_* / preview helpers. Button taps are matched in ANY language (is_text / keyboard helpers),
so an old keyboard left in the chat after a language switch still works.
The admin notification (notify_admins_new_apartment) stays Uzbek on purpose.
"""
import html
import math

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states import ApartmentStates
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


# ---------------------------------------------------------------------------
# Step prompts (used both by the normal flow and by "✏️ Tahrirlash")
# ---------------------------------------------------------------------------

async def _ask_type(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await message.answer(
        t(lang, "listing.ask_type"),
        reply_markup=ApartmentKeyboard.get_apartment_type(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_type)


async def _ask_rooms(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await message.answer(
        t(lang, "listing.ask_rooms"),
        reply_markup=ApartmentKeyboard.get_rooms_keyboard(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_rooms)


async def _ask_address(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await message.answer(
        t(lang, "listing.ask_address"),
        reply_markup=ApartmentKeyboard.get_city_area_keyboard(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_address)


async def _ask_address_detail(message: Message, state: FSMContext, area: str, lang: str = DEFAULT_LANG):
    """``area`` is the canonical (Uzbek) area name; it is shown in ``lang``."""
    await message.answer(
        t(lang, "listing.ask_address_detail", area=html.escape(area_label(area, lang))),
        reply_markup=ApartmentKeyboard.get_address_detail_keyboard(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_address_detail)


async def _ask_location(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await message.answer(
        t(lang, "listing.ask_location"),
        reply_markup=ApartmentKeyboard.get_location_keyboard(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_location)


async def _ask_price(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    type_key = _type_key(data)
    key = "listing.ask_price_rent" if type_key == "rent" else "listing.ask_price_sale"
    await message.answer(t(lang, key), reply_markup=ApartmentKeyboard.get_price_keyboard(type_key, lang))
    await state.set_state(ApartmentStates.waiting_for_price)


async def _ask_area(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    await message.answer(
        t(lang, "listing.ask_area"),
        reply_markup=ApartmentKeyboard.get_area_keyboard(data.get('rooms'), lang)
    )
    await state.set_state(ApartmentStates.waiting_for_area)


async def _ask_floor(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await message.answer(
        t(lang, "listing.ask_floor"),
        reply_markup=ApartmentKeyboard.get_floor_keyboard(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_floor)


async def _ask_total_floors(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    await message.answer(
        t(lang, "listing.ask_total_floors"),
        reply_markup=ApartmentKeyboard.get_total_floors_keyboard(data.get('floor'), lang)
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
    """Inline chips; tapped ones get a ✅."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for i, tag in enumerate(description_tags(type_key, lang)):
        mark = "✅ " if i in selected else ""
        builder.button(text=f"{mark}{tag}", callback_data=f"dtag_{i}")
    builder.adjust(2)
    return builder.as_markup()


async def _ask_description(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    type_key = _type_key(data)
    await state.update_data(desc_tags=[])
    await message.answer(
        t(lang, "listing.ask_description"),
        reply_markup=ApartmentKeyboard.get_description_keyboard(lang)
    )
    chips = await message.answer(
        t(lang, "listing.chips_hint"),
        reply_markup=_description_tags_keyboard(type_key, [], lang)
    )
    await state.update_data(desc_chips_msg=chips.message_id)
    await state.set_state(ApartmentStates.waiting_for_description)


async def _ask_photos(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await message.answer(
        t(lang, "listing.ask_photos", max=settings.photos_per_ad),
        reply_markup=ApartmentKeyboard.get_photos_done_keyboard(lang)
    )
    await state.set_state(ApartmentStates.waiting_for_photos)


async def _show_preview(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Show how the listing will look, with ✅ / ✏️ / ❌ buttons."""
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

    keyboard = ApartmentKeyboard.get_confirm_keyboard(lang)
    try:
        await message.answer_photo(photo=data['photos'][0], caption=preview, reply_markup=keyboard)
    except Exception as e:
        # Caption too long (e.g. emoji-heavy text): send photo and text separately
        logger.warning(f"Preview caption failed, sending separately: {e}")
        if data.get('photos'):
            try:
                await message.answer_photo(photo=data['photos'][0])
            except Exception:
                pass
        await message.answer(preview, reply_markup=keyboard)
    await state.set_state(ApartmentStates.confirm_apartment)


async def _next_or_preview(message: Message, state: FSMContext, next_step, lang: str = DEFAULT_LANG):
    """After a field is saved: in edit mode go back to the preview, otherwise continue."""
    data = await state.get_data()
    if data.get('editing'):
        await state.update_data(editing=False, photos_backup=None, type_backup=None, floor_backup=None, address_backup=None)
        await message.answer(t(lang, "listing.changed"))
        await _show_preview(message, state, lang)
    else:
        await next_step(message, state, lang)


async def _handle_cancel(message: Message, state: FSMContext, lang: str = DEFAULT_LANG) -> bool:
    """'❌ Bekor qilish' (any language): in edit mode undo just this change, otherwise drop the listing."""
    if not is_text(message.text, "btn.cancel"):
        return False
    data = await state.get_data()
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
        await message.answer(t(lang, "listing.change_cancelled"))
        await _show_preview(message, state, lang)
    else:
        await state.clear()
        await message.answer(
            t(lang, "listing.cancelled"),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )
    return True


# ---------------------------------------------------------------------------
# Flow handlers
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

    await message.answer(t(lang, "listing.new"))
    await _ask_type(message, state, lang)


@router.message(ApartmentStates.waiting_for_type)
async def process_apartment_type(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Process apartment type."""
    if await _handle_cancel(message, state, lang):
        return

    type_value = ApartmentKeyboard.type_from_text(message.text)
    apartment_type = ApartmentType(type_value) if type_value else None
    if not apartment_type:
        await message.answer(
            t(lang, "listing.type_invalid"),
            reply_markup=ApartmentKeyboard.get_apartment_type(lang)
        )
        return

    data = await state.get_data()
    old_type = _type_key(data) if data.get('type') else None

    # Type changed while editing and a price exists -> the price must be re-entered
    if data.get('editing') and data.get('price') and old_type != apartment_type.value:
        await state.update_data(type=apartment_type, type_backup=data.get('type'))
        await message.answer(t(lang, "listing.type_changed"))
        await _ask_price(message, state, lang)
        return

    await state.update_data(type=apartment_type)
    await _next_or_preview(message, state, _ask_rooms, lang)


@router.message(ApartmentStates.waiting_for_rooms)
async def process_rooms(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Process number of rooms."""
    if await _handle_cancel(message, state, lang):
        return

    text = (message.text or "").strip()
    try:
        rooms = 6 if text == "6+" else int(text)
        if rooms < 1 or rooms > 10:
            raise ValueError
    except ValueError:
        await message.answer(
            t(lang, "listing.rooms_invalid"),
            reply_markup=ApartmentKeyboard.get_rooms_keyboard(lang)
        )
        return

    await state.update_data(rooms=rooms)
    await _next_or_preview(message, state, _ask_address, lang)


@router.message(ApartmentStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Area button -> ask street/house; '✍️ Boshqa hudud' or typed text -> full address."""
    if await _handle_cancel(message, state, lang):
        return

    text = (message.text or "").strip()

    area = area_from_label(text)
    if area:
        # FSM keeps the canonical (Uzbek) name; the address is written in the poster's language
        await state.update_data(address_area=area)
        await _ask_address_detail(message, state, area, lang)
        return

    if is_text(text, "btn.other_area"):
        await state.update_data(address_area=None)
        await message.answer(
            t(lang, "listing.ask_full_address"),
            reply_markup=MainKeyboard.get_cancel_keyboard(lang)
        )
        return

    if len(text) < 5:
        await message.answer(
            t(lang, "listing.address_invalid"),
            reply_markup=ApartmentKeyboard.get_city_area_keyboard(lang)
        )
        return

    # Free text: add the city name if the user didn't (checked in every language)
    lowered = text.lower()
    has_city = any(name.lower() in lowered for name in variants("city"))
    address = text if has_city else f"{t(lang, 'city')}, {text}"
    await state.update_data(address=address[:300], address_area=None)
    await _ask_location(message, state, lang)


@router.message(ApartmentStates.waiting_for_address_detail)
async def process_address_detail(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Street / house after an area button (optional)."""
    if await _handle_cancel(message, state, lang):
        return

    data = await state.get_data()
    area = area_label(data.get('address_area') or "", lang)
    city = t(lang, "city")

    if is_text(message.text, "btn.skip"):
        address = f"{city}, {area}"
    else:
        detail = (message.text or "").strip()
        if len(detail) < 2:
            await message.answer(
                t(lang, "listing.address_detail_invalid"),
                reply_markup=ApartmentKeyboard.get_address_detail_keyboard(lang)
            )
            return
        address = f"{city}, {area}, {detail}"

    await state.update_data(address=address[:300], address_area=None)
    await _ask_location(message, state, lang)


@router.message(ApartmentStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """A shared location (pin) or skip."""
    if await _handle_cancel(message, state, lang):
        return

    if message.location:
        lat, lon = message.location.latitude, message.location.longitude
        await state.update_data(latitude=lat, longitude=lon)
        await message.answer(
            t(lang, "listing.location_saved"),
            reply_markup=ApartmentKeyboard.get_location_keyboard(lang)
        )
    elif is_text(message.text, "btn.skip"):
        await state.update_data(latitude=None, longitude=None)
    else:
        await message.answer(
            t(lang, "listing.location_invalid"),
            reply_markup=ApartmentKeyboard.get_location_keyboard(lang)
        )
        return

    await _next_or_preview(message, state, _ask_price, lang)


@router.message(ApartmentStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Process apartment price: '3 mln', '500 ming', '3 млн', '$45 000', '1 500 000'..."""
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
        await message.answer(
            t(lang, "listing.price_retry", reason=reason),
            reply_markup=ApartmentKeyboard.get_price_keyboard(type_key, lang)
        )
        return

    await state.update_data(price=amount, currency=currency)
    shown = _price_text(amount, currency, type_key, lang)
    note = t(lang, "listing.price_guessed_usd") if error == "guessed_usd" else ""
    data = await state.get_data()
    if not data.get('editing') or note:
        await message.answer(t(lang, "listing.price_saved", price=shown, note=note))
    await _next_or_preview(message, state, _ask_area, lang)


@router.message(ApartmentStates.waiting_for_area)
async def process_area(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Process apartment area ('65', '65 m²', '65 м²')."""
    if await _handle_cancel(message, state, lang):
        return

    if is_text(message.text, "btn.skip"):
        area = None
    else:
        area = ApartmentKeyboard.parse_area_text(message.text)
        if area is None or not math.isfinite(area) or area < 5 or area > 1000:
            data = await state.get_data()
            await message.answer(
                t(lang, "listing.area_invalid"),
                reply_markup=ApartmentKeyboard.get_area_keyboard(data.get('rooms'), lang)
            )
            return

    await state.update_data(area=area)
    await _next_or_preview(message, state, _ask_floor, lang)


@router.message(ApartmentStates.waiting_for_floor)
async def process_floor(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Floor: a button (then building height is asked), or typed '5/9' / '5'."""
    if await _handle_cancel(message, state, lang):
        return

    if is_text(message.text, "btn.skip"):
        await state.update_data(floor=None, total_floors=None)
        await _next_or_preview(message, state, _ask_description, lang)
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
        await message.answer(
            t(lang, "listing.floor_invalid"),
            reply_markup=ApartmentKeyboard.get_floor_keyboard(lang)
        )
        return

    if total_floors is not None:
        await state.update_data(floor=floor, total_floors=total_floors)
        await _next_or_preview(message, state, _ask_description, lang)
        return

    await state.update_data(floor=floor, total_floors=None)
    await _ask_total_floors(message, state, lang)


@router.message(ApartmentStates.waiting_for_total_floors)
async def process_total_floors(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Building height: '9 qavatli' / '9-этажный' / '9 floors' button, a typed number, or skip."""
    if await _handle_cancel(message, state, lang):
        return

    data = await state.get_data()
    floor = data.get('floor') or 0

    if is_text(message.text, "btn.skip"):
        total_floors = None
    else:
        total_floors = ApartmentKeyboard.parse_total_floors_text(message.text)
        if total_floors is None or total_floors < max(floor, 1) or total_floors > 100:
            await message.answer(
                t(lang, "listing.total_floors_invalid", floor=floor),
                reply_markup=ApartmentKeyboard.get_total_floors_keyboard(floor, lang)
            )
            return

    await state.update_data(total_floors=total_floors)
    await _next_or_preview(message, state, _ask_description, lang)


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


@router.message(ApartmentStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """'✅ Tayyor' -> ticked chips; free text -> chips + text; skip -> nothing."""
    if await _handle_cancel(message, state, lang):
        return

    data = await state.get_data()
    type_key = _type_key(data)
    all_tags = description_tags(type_key, lang)
    tags = [all_tags[i] for i in sorted(data.get('desc_tags') or []) if 0 <= i < len(all_tags)]

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

    await state.update_data(description=description, desc_tags=None, desc_chips_msg=None)

    # Freeze the chips message so old chips can't be tapped later
    if data.get('desc_chips_msg'):
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


@router.message(ApartmentStates.waiting_for_photos, F.photo)
async def process_photo(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Process apartment photos."""
    data = await state.get_data()
    photos = data.get('photos', [])

    if len(photos) >= settings.photos_per_ad:
        await message.answer(t(lang, "listing.photos_limit", max=settings.photos_per_ad))
        return

    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(t(lang, "listing.photo_added", n=len(photos), max=settings.photos_per_ad))


@router.message(ApartmentStates.waiting_for_photos, F.text.in_(variants("btn.done")))
async def photos_done(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Finalize photos and show confirmation."""
    data = await state.get_data()

    if not data.get('photos'):
        await message.answer(t(lang, "listing.photos_required"))
        return

    await state.update_data(editing=False, photos_backup=None, type_backup=None, floor_backup=None, address_backup=None)
    await _show_preview(message, state, lang)


@router.message(ApartmentStates.waiting_for_photos)
async def invalid_photo_input(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Handle anything else during photo upload."""
    if await _handle_cancel(message, state, lang):
        return
    await message.answer(t(lang, "listing.photos_invalid"))


@router.message(ApartmentStates.confirm_apartment)
async def confirm_apartment(message: Message, state: FSMContext, session: AsyncSession, lang: str = DEFAULT_LANG):
    """Confirm, edit or cancel the listing."""
    if is_text(message.text, "btn.cancel"):
        await state.clear()
        await message.answer(
            t(lang, "listing.cancelled"),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )
        return

    if is_text(message.text, "btn.edit"):
        await message.answer(
            t(lang, "listing.edit_menu"),
            reply_markup=ApartmentKeyboard.get_edit_fields_keyboard(lang)
        )
        await state.set_state(ApartmentStates.choosing_edit_field)
        return

    if not is_text(message.text, "btn.confirm"):
        await message.answer(
            t(lang, "listing.confirm_invalid"),
            reply_markup=ApartmentKeyboard.get_confirm_keyboard(lang)
        )
        return

    data = await state.get_data()
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
            source='manual'
        )

        await state.clear()

        is_rent = apartment.type == ApartmentType.RENT
        type_text = t(lang, "listing.success_type_rent" if is_rent else "listing.success_type_sale")
        price_text = _price_text(apartment.price, apartment.currency, "rent" if is_rent else "sale", lang)

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


@router.message(ApartmentStates.choosing_edit_field)
async def choose_edit_field(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """User picked which field to change."""
    if is_text(message.text, "btn.edit_back") or is_text(message.text, "btn.cancel"):
        await _show_preview(message, state, lang)
        return

    field = ApartmentKeyboard.edit_field_from_text(message.text)
    if not field:
        await message.answer(
            t(lang, "listing.edit_field_invalid"),
            reply_markup=ApartmentKeyboard.get_edit_fields_keyboard(lang)
        )
        return

    await state.update_data(editing=True)

    if field == "address":
        data = await state.get_data()
        await state.update_data(address_backup=[data.get('address'), data.get('latitude'), data.get('longitude')])

    if field == "floor":
        # Keep old floor/height so cancelling at the building-height step can restore them
        data = await state.get_data()
        await state.update_data(floor_backup=[data.get('floor'), data.get('total_floors')])

    if field == "photos":
        data = await state.get_data()
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
