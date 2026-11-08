"""Apartment handlers (listing-creation flow, localized: uz / ru / en).

The whole form is driven by INLINE buttons attached to each step message (callback_data
prefix "lf:", see ApartmentKeyboard.inline_*). Typed answers still work where they make
sense (address detail, custom price, m², floor, description, phone) and the old reply-button
labels are still understood (is_text) so a stale keyboard in the chat does no harm.
The only reply keyboard left is Telegram's "share location" button at the location step.

Clean chat: every message of the flow (bot steps, hints, errors AND the user's own replies,
photos, location, the "➕ E'lon qo'shish" trigger) is tracked in FSM 'lf_trash'. When a step is
answered everything tracked so far is deleted (_purge), so the chat only shows the current step;
the next step starts with a one-line recap of what was chosen. Received photos are deleted at
once (their file_id is kept) and ONE status message is edited in place. Confirm / cancel delete
everything and leave one result message + the main menu. Admin-import posts / summary are kept
until the end ('lf_sticky').

Photos can also come from the mini-app upload page ("📸 Rasm yuborish" = inline web_app button,
app/webapp/server.py -> add_uploaded_photos()).

Callbacks whose state no longer matches are answered with a short "step is over" toast — so
double taps and old buttons are harmless. Every handler takes ``lang`` (injected by
LanguageMiddleware). The admin notification (notify_admins_new_apartment) stays Uzbek on purpose.
"""
import asyncio
import html
import math
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional

from aiogram import BaseMiddleware, Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
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

# FSM state groups whose incoming messages belong to the listing / import flow
FLOW_GROUPS = ("ApartmentStates", "ImportStates")


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
# Clean chat: message tracking (FSM 'lf_trash') and deletion
# ---------------------------------------------------------------------------

def _ids(message_ids) -> list:
    out = []
    for m in message_ids:
        try:
            m = int(m)
        except (TypeError, ValueError):
            continue
        if m > 0 and m not in out:
            out.append(m)
    return out


async def _track(state: FSMContext, *message_ids) -> None:
    """Remember message ids (bot steps AND user replies) to delete later (FSM 'lf_trash')."""
    ids = _ids(message_ids)
    if not ids:
        return
    data = await state.get_data()
    trash = list(data.get('lf_trash') or [])
    trash.extend(m for m in ids if m not in trash)
    await state.update_data(lf_trash=trash)


async def _track_sticky(state: FSMContext, *message_ids) -> None:
    """Track ids that survive step-to-step purges and are deleted only at the end (import post / summary)."""
    ids = _ids(message_ids)
    if not ids:
        return
    await _track(state, *ids)
    data = await state.get_data()
    sticky = list(data.get('lf_sticky') or [])
    sticky.extend(m for m in ids if m not in sticky)
    await state.update_data(lf_sticky=sticky)


async def _delete_ids(bot: Bot, chat_id: int, message_ids: Iterable[int]) -> None:
    """Delete messages; missing / too old (> 48 h) ones are ignored. Never raises."""
    ids = sorted(_ids(message_ids))
    for start in range(0, len(ids), 100):
        chunk = ids[start:start + 100]
        if len(chunk) == 1:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=chunk[0])
            except Exception:
                pass
            continue
        try:
            # deleteMessages silently skips messages that can't be found / deleted
            await bot.delete_messages(chat_id=chat_id, message_ids=chunk)
            continue
        except Exception as e:
            logger.debug(f"delete_messages failed in {chat_id}, deleting one by one: {e}")
        for message_id in chunk:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception:
                pass


async def _purge(bot: Bot, chat_id: int, state: FSMContext, keep: Iterable[int] = (), final: bool = False) -> None:
    """Delete every tracked message except ``keep`` and clear the list.

    final=False (a step was answered): the sticky ids (import post / summary) are kept as well.
    Kept ids stay tracked, so the final purge (confirm / cancel) still removes them.
    """
    data = await state.get_data()
    trash = list(data.get('lf_trash') or [])
    kept = set(_ids(keep))
    if not final:
        kept |= set(_ids(data.get('lf_sticky') or []))
    doomed = [m for m in trash if m not in kept]
    update = {'lf_trash': [m for m in trash if m in kept]}
    if final:
        update['lf_sticky'] = []
    await state.update_data(**update)
    if doomed:
        await _delete_ids(bot, chat_id, doomed)


async def _say(message: Message, state: FSMContext, text: str, **kwargs) -> Message:
    """message.answer() whose message is tracked (deleted when the next step is answered)."""
    sent = await message.answer(text, **kwargs)
    await _track(state, sent.message_id)
    return sent


class TrackFlowMessages(BaseMiddleware):
    """Inner middleware (apartments + import routers): a message handled while a listing / import
    state is active belongs to the flow -> tracked BEFORE the handler runs, so its purge removes it."""

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        state: Optional[FSMContext] = data.get("state")
        raw_state = data.get("raw_state")
        if (state is not None and isinstance(event, Message) and isinstance(raw_state, str)
                and raw_state.split(":", 1)[0] in FLOW_GROUPS):
            try:
                await _track(state, event.message_id)
            except Exception as e:  # tracking must never break the flow
                logger.debug(f"Message tracking failed: {e}")
        return await handler(event, data)


router.message.middleware(TrackFlowMessages())


def _recap(data: dict, lang: str) -> str:
    """One line on top of each step: '✅ Ijaraga · 3 xonali · 8-mikrorayon · 4 350 000 so'm / oy' (HTML)."""
    items = []
    if data.get('type'):
        items.append(t(lang, "listing.success_type_rent" if _type_key(data) == "rent" else "listing.success_type_sale"))
    if data.get('rooms'):
        items.append(t(lang, "listing.rooms_n", n=data['rooms']))
    if data.get('address_area'):
        items.append(area_label(data['address_area'], lang))
    elif data.get('address'):
        address = str(data['address'])
        for city in variants("city"):
            if address.startswith(city + ", "):
                address = address[len(city) + 2:]
                break
        items.append(truncate_text(address, 40))
    if data.get('price') is not None and data.get('currency'):
        items.append(_price_text(data['price'], data['currency'], _type_key(data), lang))
    if data.get('area'):
        items.append(t(lang, "btn.area_m2", n=f"{data['area']:g}"))
    if data.get('floor'):
        floor = f"{data['floor']}/{data['total_floors']}" if data.get('total_floors') else str(data['floor'])
        items.append(t(lang, "lf.recap_floor", floor=floor))
    if not items:
        return ""
    return "<i>✅ " + html.escape(" · ".join(str(i) for i in items), quote=False) + "</i>"


def _with_recap(data: dict, lang: str, text: str) -> str:
    recap = _recap(data, lang)
    return f"{recap}\n\n{text}" if recap else text


# ---------------------------------------------------------------------------
# Inline-step plumbing
# ---------------------------------------------------------------------------

async def _send_step(message: Message, state: FSMContext, text: str, keyboard,
                     lang: Optional[str] = None, **extra) -> Message:
    """Send a step prompt and remember it (lf_msg, tracked for deletion).

    With ``lang`` the prompt starts with the recap line of what was chosen so far.
    """
    if lang:
        text = _with_recap(await state.get_data(), lang, text)
    sent = await message.answer(text, reply_markup=keyboard, **extra)
    await state.update_data(lf_msg=sent.message_id)
    await _track(state, sent.message_id)
    return sent


async def _freeze_step(message: Message, state: FSMContext, except_id: Optional[int] = None):
    """The current step was answered (typed answer or tapped button): delete the step message, the
    user's reply and everything else tracked so far (sticky import messages excepted)."""
    await state.update_data(lf_msg=None)
    await _purge(message.bot, message.chat.id, state)


async def _choose(callback: CallbackQuery, state: FSMContext, lang: str, chosen: Optional[str] = None) -> Optional[Message]:
    """A step button was tapped: the step message and the rest of the step's messages are deleted
    (``chosen`` is shown by the next step's recap line instead).

    Returns the message to continue the dialogue with (None if Telegram gave no accessible message).
    """
    message = callback.message
    if not isinstance(message, Message):
        return None
    await _track(state, message.message_id)
    await _freeze_step(message, state)
    return message


# ---------------------------------------------------------------------------
# Step prompts (used by the normal flow, by "✏️ Tahrirlash" and by the admin import)
# ---------------------------------------------------------------------------

async def _ask_type(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_type"), ApartmentKeyboard.inline_type(lang), lang=lang)
    await state.set_state(ApartmentStates.waiting_for_type)


async def _ask_rooms(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_rooms"), ApartmentKeyboard.inline_rooms(lang), lang=lang)
    await state.set_state(ApartmentStates.waiting_for_rooms)


async def _ask_address(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_address"), ApartmentKeyboard.inline_areas(lang), lang=lang)
    await state.set_state(ApartmentStates.waiting_for_address)


async def _ask_address_detail(message: Message, state: FSMContext, area: str, lang: str = DEFAULT_LANG):
    """``area`` is the canonical (Uzbek) area name; it is shown in ``lang``."""
    await _send_step(
        message, state,
        t(lang, "listing.ask_address_detail", area=html.escape(area_label(area, lang))),
        ApartmentKeyboard.inline_skip_cancel(lang), lang=lang,
    )
    await state.set_state(ApartmentStates.waiting_for_address_detail)


async def _ask_location(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """The one step with a reply keyboard (Telegram's location button); skip / cancel are inline."""
    await _say(message, state, t(lang, "listing.ask_location"), reply_markup=ApartmentKeyboard.location_reply_keyboard(lang))
    await _send_step(message, state, t(lang, "listing.location_or_skip"), ApartmentKeyboard.inline_skip_cancel(lang), lang=lang)
    await state.set_state(ApartmentStates.waiting_for_location)


async def _ask_price(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    type_key = _type_key(data)
    key = "listing.ask_price_rent" if type_key == "rent" else "listing.ask_price_sale"
    await _send_step(message, state, t(lang, key), ApartmentKeyboard.inline_price(type_key, lang), lang=lang)
    await state.set_state(ApartmentStates.waiting_for_price)


async def _ask_area(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    await _send_step(message, state, t(lang, "listing.ask_area"), ApartmentKeyboard.inline_m2(data.get('rooms'), lang),
                     lang=lang)
    await state.set_state(ApartmentStates.waiting_for_area)


async def _ask_floor(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    await _send_step(message, state, t(lang, "listing.ask_floor"), ApartmentKeyboard.inline_floor(lang), lang=lang)
    await state.set_state(ApartmentStates.waiting_for_floor)


async def _ask_total_floors(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    data = await state.get_data()
    await _send_step(
        message, state, t(lang, "listing.ask_total_floors"), ApartmentKeyboard.inline_tf(data.get('floor'), lang),
        lang=lang,
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
        _description_tags_keyboard(type_key, [], lang), lang=lang,
    )
    await state.update_data(desc_chips_msg=chips.message_id)
    await state.set_state(ApartmentStates.waiting_for_description)


def _photos_text(data: dict, lang: str, count: int) -> str:
    """Photos prompt = the ONE status message: recap + how to send + progress 'N/10' (once there are photos)."""
    text = t(lang, "listing.ask_photos", min=_min_photos(), max=settings.photos_per_ad)
    has_upload = bool(ApartmentKeyboard.photos_upload_url(lang))
    text += "\n\n" + t(lang, "listing.photos_how_webapp" if has_upload else "listing.photos_how_clip")
    if count:
        minimum = _min_photos()
        hint = (t(lang, "listing.photos_need_more", more=minimum - count) if count < minimum
                else t(lang, "listing.photos_enough"))
        text += "\n\n" + t(lang, "listing.photos_progress", n=count, max=settings.photos_per_ad, hint=hint)
    return _with_recap(data, lang, text)


def _photos_keyboard(count: int, lang: str):
    """'📸 Rasm yuborish' (mini-app gallery upload) + '✅ Tayyor (N ta rasm)' + ❌."""
    return ApartmentKeyboard.inline_photos(count, _min_photos(), settings.photos_per_ad, lang)


async def _ask_photos(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Photos prompt; it is also the status message edited in place after every photo.
    The photos already in the FSM (import) are counted in."""
    await state.update_data(lang=lang, photos_limit_msg=None)
    data = await state.get_data()
    count = len(data.get('photos') or [])
    sent = await _send_step(message, state, _photos_text(data, lang, count), _photos_keyboard(count, lang))
    await state.update_data(photos_status_msg=sent.message_id, photos_status_n=count)
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
        ApartmentKeyboard.inline_import_phone(data.get('admin_phone'), lang), lang=lang,
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
            await _say(message, state, "⚠️ Topilgan narx tanlangan tur uchun mos emas, qaytadan kiriting.")
            await state.update_data(price=None)
        await _ask_price(message, state, lang)
    elif not data.get('phone_number'):
        await _ask_import_phone(message, state, lang)
    elif len(photos) < _min_photos():
        if photos:
            await _say(message, state, t(lang, "listing.import_photos_more", k=len(photos), min=_min_photos()))
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
        await _track(state, sent.message_id)
    except Exception as e:
        # Caption too long (e.g. emoji-heavy text): send photo and text separately
        logger.warning(f"Preview caption failed, sending separately: {e}")
        if data.get('photos'):
            try:
                photo_msg = await message.answer_photo(photo=data['photos'][0])
                await _track(state, photo_msg.message_id)
            except Exception:
                pass
        sent = await _say(message, state, preview, reply_markup=keyboard)
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
        await _say(message, state, t(lang, "listing.changed"), reply_markup=ReplyKeyboardRemove())
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
        await _purge(message.bot, message.chat.id, state, final=True)
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
        await _say(message, state, t(lang, "listing.change_cancelled"), reply_markup=ReplyKeyboardRemove())
        await _show_preview(message, state, lang)
    else:
        # The whole listing is dropped: every message of the flow goes, one short note + main menu stays
        await _purge(message.bot, message.chat.id, state, final=True)
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
        await _say(message, state, t(lang, "listing.location_skipped"), reply_markup=ReplyKeyboardRemove())
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

    # A flow already running (restart): its messages go; this trigger message belongs to the new flow
    await _purge(message.bot, message.chat.id, state, keep={message.message_id}, final=True)
    await state.clear()

    await state.update_data(owner_id=user.id, phone_number=user.phone_number, lang=lang)
    await _track(state, message.message_id)

    # The form is inline from here on: hide the main-menu reply keyboard
    await _say(message, state, t(lang, "listing.new"), reply_markup=ReplyKeyboardRemove())
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
        await _say(message, state, t(lang, "listing.type_changed"))
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
        await _say(message, state, t(lang, "listing.type_invalid"))
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
        await _say(message, state, t(lang, "listing.rooms_invalid"))
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
    await _send_step(message, state, t(lang, "listing.ask_full_address"), ApartmentKeyboard.inline_cancel(lang), lang=lang)


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
        await _say(message, state, t(lang, "listing.address_invalid"))
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
            await _say(message, state, t(lang, "listing.address_detail_invalid"))
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
        await _say(message, state, t(lang, "listing.location_saved"), reply_markup=ReplyKeyboardRemove())
        await _set_location(message, state, lang, location.latitude, location.longitude)
    elif is_text(message.text, "btn.skip"):
        await _freeze_step(message, state)
        await _say(message, state, t(lang, "listing.location_skipped"), reply_markup=ReplyKeyboardRemove())
        await _set_location(message, state, lang, None, None)
    else:
        await _say(message, state, t(lang, "listing.location_invalid"))


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
        await _say(message, state, t(lang, "listing.price_saved", price=shown, note=note))
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
        await _say(message, state, t(lang, "listing.price_retry", reason=reason))
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
            await _say(message, state, t(lang, "listing.area_invalid"))
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
        await _say(message, state, t(lang, "listing.floor_invalid"))
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
            await _say(message, state, t(lang, "listing.total_floors_invalid", floor=floor))
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
    # (the chips message is the step message: already deleted by _choose / _freeze_step)
    await state.update_data(description=description, desc_tags=None, desc_chips_msg=None)

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
            await _say(message, state, t(lang, "listing.description_empty"))
            return
        description = " · ".join(tags) + ("\n" if tags else "") + extra

    if description and len(description) > settings.max_description_length:
        await _say(message, state, 
            t(lang, "listing.description_too_long", n=len(description), max=settings.max_description_length)
        )
        return

    await _freeze_step(message, state)
    await _finish_description(message, state, lang, description)


# ---------------------------------------------------------------------------
# Photos (at least settings.min_photos_per_ad, at most settings.photos_per_ad)
# ---------------------------------------------------------------------------

# One lock per user: Telegram photos (dispatcher) and mini-app uploads (web server, outside the
# dispatcher's event isolation) must not interleave while the status message is edited.
_photo_locks: Dict[int, asyncio.Lock] = {}


def _photo_lock(user_id: int) -> asyncio.Lock:
    lock = _photo_locks.get(user_id)
    if lock is None:
        if len(_photo_locks) > 5000:  # keep the dict small; idle locks are cheap to recreate
            for uid in [u for u, l in _photo_locks.items() if not l.locked()]:
                _photo_locks.pop(uid, None)
        lock = _photo_locks[user_id] = asyncio.Lock()
    return lock


async def _refresh_photos_status(bot: Bot, chat_id: int, state: FSMContext, lang: str) -> None:
    """Edit the ONE photos status message (prompt) to the current count 'N/10' + keyboard.

    If it can't be edited (deleted, too old) a new one is sent — only while the photos step is active.
    """
    data = await state.get_data()
    count = len(data.get('photos') or [])
    status_id = data.get('photos_status_msg')
    if status_id and data.get('photos_status_n') == count:
        return  # nothing changed ("message is not modified")
    text = _photos_text(data, lang, count)
    keyboard = _photos_keyboard(count, lang)
    if status_id:
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=status_id, text=text, reply_markup=keyboard)
            await state.update_data(photos_status_n=count)
            return
        except TelegramBadRequest as e:
            if "not modified" in str(e).lower():
                await state.update_data(photos_status_n=count)
                return
            # message gone / can't be edited any more -> a new status message below
        except Exception as e:
            # flood control / network: keep the old message; the next photo refreshes it
            logger.debug(f"Photos status edit failed: {e}")
            return
    if await state.get_state() != ApartmentStates.waiting_for_photos.state:
        return
    sent = await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    await _track(state, sent.message_id)
    await state.update_data(photos_status_msg=sent.message_id, lf_msg=sent.message_id, photos_status_n=count)
    if status_id:
        await _delete_ids(bot, chat_id, [status_id])


@router.message(ApartmentStates.waiting_for_photos, F.photo)
async def process_photo(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Collect photos (file_id of the largest size); the photo message itself is deleted at once
    and the progress is shown by editing the one status message."""
    async with _photo_lock(message.chat.id):
        if await state.get_state() != ApartmentStates.waiting_for_photos.state:
            return  # "✅ Tayyor" / cancel won the race
        data = await state.get_data()
        photos = list(data.get('photos') or [])
        accepted = len(photos) < settings.photos_per_ad
        if accepted:
            photos.append(message.photo[-1].file_id)
            await state.update_data(photos=photos)

        # The photo is stored (or over the limit): its message is not needed in the chat.
        # (It stays tracked: if this delete fails, e.g. flood control, the final purge retries it.)
        await _delete_ids(message.bot, message.chat.id, [message.message_id])

        if not accepted:
            if not data.get('photos_limit_msg'):
                warn = await _say(message, state, t(lang, "listing.photos_limit", max=settings.photos_per_ad))
                await state.update_data(photos_limit_msg=warn.message_id)
            return
        await _refresh_photos_status(message.bot, message.chat.id, state, lang)


async def add_uploaded_photos(bot: Bot, storage: BaseStorage, user_id: int, file_ids: list) -> dict:
    """Photos uploaded from the mini-app page (app/webapp/server.py) -> the user's listing.

    Only while the user is at the photos step (ApartmentStates.waiting_for_photos); file ids are
    appended up to settings.photos_per_ad and the status message is refreshed like process_photo does.
    Returns {"ok": True, "added", "total", "max", "min"} or {"ok": False, "error": "not_waiting"}.
    """
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    state = FSMContext(storage=storage, key=key)
    maximum, minimum = settings.photos_per_ad, _min_photos()
    async with _photo_lock(user_id):
        if await state.get_state() != ApartmentStates.waiting_for_photos.state:
            return {"ok": False, "error": "not_waiting"}
        data = await state.get_data()
        lang = data.get('lang') or DEFAULT_LANG
        photos = list(data.get('photos') or [])
        room = max(0, maximum - len(photos))
        new_ids = [f for f in (file_ids or []) if isinstance(f, str) and f][:room]
        if new_ids:
            photos.extend(new_ids)
            await state.update_data(photos=photos)
            try:
                await _refresh_photos_status(bot, user_id, state, lang)
            except Exception as e:  # the photos are stored; a failed status edit must not fail the upload
                logger.warning(f"Photos status refresh after upload failed for {user_id}: {e}")
        return {"ok": True, "added": len(new_ids), "total": len(photos), "max": maximum, "min": minimum}


async def _finish_photos(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    # (the status message is the step message: already deleted by _choose / _freeze_step)
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
    async with _photo_lock(callback.from_user.id):  # waits for a mini-app upload in progress
        data = await state.get_data()
        count = len(data.get('photos') or [])
        if await state.get_state() != ApartmentStates.waiting_for_photos.state:
            await callback.answer(t(lang, "lf.stale"))
            return
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
    async with _photo_lock(message.chat.id):
        data = await state.get_data()
        count = len(data.get('photos') or [])
        if count < _min_photos():
            await _say(message, state, t(lang, "listing.photos_required", n=_min_photos(), k=count))
            return
        await _freeze_step(message, state)
        await _finish_photos(message, state, lang)


@router.message(ApartmentStates.waiting_for_photos)
async def invalid_photo_input(message: Message, state: FSMContext, lang: str = DEFAULT_LANG):
    """Handle anything else during photo upload."""
    if await _handle_cancel(message, state, lang):
        return
    await _say(message, state, t(lang, "listing.photos_invalid"))


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

        # Clean chat: everything of the flow goes (preview, replies, photos, trigger, import post);
        # only the result message below (+ main menu) stays
        await _purge(message.bot, message.chat.id, state, final=True)
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
        try:
            await _purge(message.bot, message.chat.id, state, final=True)
        except Exception:
            pass
        await message.answer(
            t(lang, "listing.save_error"),
            reply_markup=MainKeyboard.get_main_menu(is_registered=True, lang=lang)
        )
        await state.clear()


async def _open_edit_menu(message: Message, state: FSMContext, lang: str):
    await _send_step(message, state, t(lang, "listing.edit_menu"), ApartmentKeyboard.inline_edit_fields(lang), lang=lang)
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
        await _say(message, state, t(lang, "listing.confirm_invalid"))
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
        await _say(message, state, t(lang, "listing.replace_photos"))

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
        await _say(message, state, t(lang, "listing.edit_field_invalid"))
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
