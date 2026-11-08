"""Keyboard layouts for the bot.

Every user-facing builder takes ``lang`` ('uz' | 'ru' | 'en', default 'uz') and uses
t(lang, "btn.*") labels. The default 'uz' produces exactly the old Uzbek labels.
Admin-only builders (get_admin_menu, get_user_actions, admin branch of
get_apartment_actions) stay Uzbek on purpose.
"""
import re
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from config import settings
from app.i18n import LANGS, LANG_NAMES, DEFAULT_LANG, t, match_key


def webapp_url_for(lang: str = DEFAULT_LANG) -> str:
    """settings.webapp_url with ?lang=<lang> (or &lang=); '' when no WEBAPP_URL is set."""
    url = (settings.webapp_url or "").strip()
    if not url:
        return ""
    if lang not in LANGS:
        lang = DEFAULT_LANG
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "lang"]
    query.append(("lang", lang))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _fmt_usd(value: int) -> str:
    return "$" + f"{value:,}".replace(",", " ")


class MainKeyboard:
    """Main menu keyboards."""

    @staticmethod
    def has_webapp() -> bool:
        return (settings.webapp_url or "").strip().startswith("https://")

    @staticmethod
    def get_main_menu(is_registered: bool = True, lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Main menu (reply keyboard).

        The '📱 Ilovani ochish' button here is plain text on purpose: Telegram does NOT pass
        the user's identity (initData) to a mini app opened from a reply-keyboard button,
        so "Mening e'lonlarim" and "Bog'lanish" would not work. The text button answers
        with an inline web-app button, which does pass initData.
        """
        builder = ReplyKeyboardBuilder()
        has_webapp = MainKeyboard.has_webapp()
        if has_webapp:
            builder.button(text=t(lang, "btn.open_app"))

        if is_registered:
            builder.button(text=t(lang, "btn.add_listing"))
            builder.button(text=t(lang, "btn.settings"))
        else:
            builder.button(text=t(lang, "btn.register"))

        builder.adjust(1, 2) if has_webapp else builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_cancel_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get cancel keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.cancel"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_skip_cancel_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get skip and cancel keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_phone_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get phone number request keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.send_phone"), request_contact=True)
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


class ApartmentKeyboard:
    """Apartment related keyboards."""

    @staticmethod
    def get_apartment_type(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get apartment type selection keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.type_rent"))
        builder.button(text=t(lang, "btn.type_sale"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(2, 1)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def type_from_text(text: Optional[str]) -> Optional[str]:
        """'rent' / 'sale' for the type button label in any language, else None."""
        key = match_key(text, ("btn.type_rent", "btn.type_sale"))
        return {"btn.type_rent": "rent", "btn.type_sale": "sale"}.get(key)

    @staticmethod
    def get_rooms_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get rooms selection keyboard."""
        builder = ReplyKeyboardBuilder()
        for i in range(1, 7):
            builder.button(text=str(i))
        builder.button(text="6+")
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(3, 3, 1, 1)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_confirm_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get confirmation keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.confirm"))
        builder.button(text=t(lang, "btn.edit"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(1, 2)
        # Not one-time: buttons must stay visible until the user decides
        return builder.as_markup(resize_keyboard=True)

    # Ready-made prices so users don't have to type long numbers.
    # (kind, number): "mln" -> t(lang, "btn.price_mln", n=...), "usd" -> "$30 000"
    PRICE_PRESET_SPECS = {
        "rent": [("mln", 2), ("mln", 3), ("mln", 4), ("mln", 5), ("usd", 300), ("usd", 500)],
        "sale": [("usd", 30_000), ("usd", 40_000), ("usd", 50_000), ("usd", 70_000), ("mln", 400), ("mln", 600)],
    }
    # Uzbek labels (kept for old code)
    PRICE_PRESETS = {
        "rent": ["2 mln", "3 mln", "4 mln", "5 mln", "$300", "$500"],
        "sale": ["$30 000", "$40 000", "$50 000", "$70 000", "400 mln", "600 mln"],
    }

    @staticmethod
    def price_presets(apartment_type: str, lang: str = DEFAULT_LANG) -> List[str]:
        """Preset price labels for 'rent' / 'sale' in ``lang`` (all parseable by app.utils.price)."""
        result = []
        for kind, value in ApartmentKeyboard.PRICE_PRESET_SPECS.get(apartment_type, []):
            result.append(t(lang, "btn.price_mln", n=value) if kind == "mln" else _fmt_usd(value))
        return result

    @staticmethod
    def get_price_keyboard(apartment_type: str, lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Price presets for rent ('rent') or sale ('sale') + cancel."""
        builder = ReplyKeyboardBuilder()
        for preset in ApartmentKeyboard.price_presets(apartment_type, lang):
            builder.button(text=preset)
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(3, 3, 1)
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=t(lang, "ph.price")
        )

    # i18n label key -> field
    EDIT_FIELD_KEYS = {
        "btn.edit_type": "type",
        "btn.edit_rooms": "rooms",
        "btn.edit_address": "address",
        "btn.edit_price": "price",
        "btn.edit_area": "area",
        "btn.edit_floor": "floor",
        "btn.edit_description": "description",
        "btn.edit_photos": "photos",
    }
    # Uzbek label -> field (kept for old code)
    EDIT_FIELDS = {t("uz", key): field for key, field in EDIT_FIELD_KEYS.items()}
    EDIT_BACK = t("uz", "btn.edit_back")

    @staticmethod
    def edit_field_from_text(text: Optional[str]) -> Optional[str]:
        """Field name ('type', 'rooms', ...) for an edit button label in any language."""
        key = match_key(text, ApartmentKeyboard.EDIT_FIELD_KEYS)
        return ApartmentKeyboard.EDIT_FIELD_KEYS.get(key) if key else None

    @staticmethod
    def get_edit_fields_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Which field of the listing to change."""
        builder = ReplyKeyboardBuilder()
        for key in ApartmentKeyboard.EDIT_FIELD_KEYS:
            builder.button(text=t(lang, key))
        builder.button(text=t(lang, "btn.edit_back"))
        builder.adjust(2, 2, 2, 2, 1)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_photos_done_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Get photos done keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.done"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)

    # ---- Ready-made answers for the listing form (tap instead of typing) ----

    AREA_PRESETS = {
        1: [25, 30, 35, 40],
        2: [40, 45, 50, 55, 60],
        3: [60, 65, 70, 75, 80],
        4: [80, 90, 100, 110],
        5: [100, 120, 140, 160],
        6: [120, 150, 180, 200],
    }
    FLOOR_CHOICES = list(range(1, 13))
    TOTAL_FLOOR_CHOICES = [4, 5, 9, 10, 12, 16]
    # Uzbek labels (kept for old code); use t(lang, "btn.skip"/"btn.cancel"/"btn.done")
    SKIP_TEXT = t("uz", "btn.skip")
    CANCEL_TEXT = t("uz", "btn.cancel")
    DONE_TEXT = t("uz", "btn.done")

    @staticmethod
    def get_city_area_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Chirchiq areas (mikrorayon / mavze), two per row, + 'other' + cancel."""
        from app.utils.areas import CHIRCHIQ_AREAS, area_label
        builder = ReplyKeyboardBuilder()
        for area in CHIRCHIQ_AREAS:
            builder.button(text=area_label(area, lang))
        builder.button(text=t(lang, "btn.other_area"))
        builder.button(text=t(lang, "btn.cancel"))
        rows = [2] * (len(CHIRCHIQ_AREAS) // 2) + ([1] if len(CHIRCHIQ_AREAS) % 2 else [])
        builder.adjust(*rows, 2)
        return builder.as_markup(resize_keyboard=True, input_field_placeholder=t(lang, "ph.city_area"))

    @staticmethod
    def get_location_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Share the apartment's location (works on phones) or skip."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.send_location"), request_location=True)
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(1, 2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_address_detail_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """After the area: street / house (optional)."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True, input_field_placeholder=t(lang, "ph.address_detail"))

    @staticmethod
    def get_area_keyboard(rooms: Optional[int], lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Typical areas for the chosen number of rooms."""
        builder = ReplyKeyboardBuilder()
        presets = ApartmentKeyboard.AREA_PRESETS.get(min(max(int(rooms or 2), 1), 6), [])
        for value in presets:
            builder.button(text=t(lang, "btn.area_m2", n=value))
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(len(presets) if len(presets) <= 3 else (3 if len(presets) == 5 else 4), 2, 2, 2)
        return builder.as_markup(resize_keyboard=True, input_field_placeholder=t(lang, "ph.area"))

    @staticmethod
    def parse_area_text(text: Optional[str]) -> Optional[float]:
        """'65', '65 m²', '65 м²', '65,5 кв.м' -> float (no range check), else None."""
        s = (text or "").lower()
        for unit in ("кв.м.", "кв.м", "кв м", "kv.m", "sq m", "sqm", "m²", "м²", "m2", "м2"):
            s = s.replace(unit, "")
        s = s.replace(",", ".").strip()
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def get_floor_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Floor 1..12."""
        builder = ReplyKeyboardBuilder()
        for value in ApartmentKeyboard.FLOOR_CHOICES:
            builder.button(text=str(value))
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(4, 4, 4, 2)
        return builder.as_markup(resize_keyboard=True, input_field_placeholder=t(lang, "ph.floor"))

    @staticmethod
    def get_total_floors_keyboard(floor: Optional[int], lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """How many floors the building has (only values >= the chosen floor)."""
        builder = ReplyKeyboardBuilder()
        options = [v for v in ApartmentKeyboard.TOTAL_FLOOR_CHOICES if v >= (floor or 0)]
        if floor and floor not in options:
            options = [floor] + options
        for value in options:
            builder.button(text=t(lang, "btn.total_floors_n", n=value))
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        rows = [3] * (len(options) // 3) + ([len(options) % 3] if len(options) % 3 else [])
        builder.adjust(*rows, 2)
        return builder.as_markup(resize_keyboard=True, input_field_placeholder=t(lang, "ph.total_floors"))

    @staticmethod
    def parse_total_floors_text(text: Optional[str]) -> Optional[int]:
        """'9', '9 qavatli', '9-этажный', '9 этажей', '9 floors' -> 9 (no range check), else None."""
        m = re.fullmatch(
            r"\s*(\d{1,3})\s*-?\s*(?:qavatli|qavat|этажный|этажей|этажа|этаж|floors|floor|storeys|storey)?\s*",
            (text or "").lower(),
        )
        return int(m.group(1)) if m else None

    @staticmethod
    def get_description_keyboard(lang: str = DEFAULT_LANG) -> ReplyKeyboardMarkup:
        """Reply keyboard under the description chips."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=t(lang, "btn.done"))
        builder.button(text=t(lang, "btn.skip"))
        builder.button(text=t(lang, "btn.cancel"))
        builder.adjust(1, 2)
        return builder.as_markup(resize_keyboard=True, input_field_placeholder=t(lang, "ph.description"))



class InlineKeyboards:
    """Inline keyboards for various purposes."""

    @staticmethod
    def get_open_app(lang: str = DEFAULT_LANG, text: Optional[str] = None) -> Optional[InlineKeyboardMarkup]:
        """Inline button that opens the mini app WITH the user's identity (initData).

        Old calls passed the label as the first argument (get_open_app("📱 E'lonlarni ko'rish")):
        a first argument that is not a language code is treated as the label (Uzbek app).
        """
        if lang not in LANGS:
            text, lang = lang, DEFAULT_LANG
        url = webapp_url_for(lang)
        if not url.startswith("https://"):
            return None
        builder = InlineKeyboardBuilder()
        builder.button(text=text or t(lang, "btn.open_app"), web_app=WebAppInfo(url=url))
        return builder.as_markup()

    @staticmethod
    def get_language_picker() -> InlineKeyboardMarkup:
        """🇺🇿 / 🇷🇺 / 🇬🇧 buttons -> callback 'setlang_<code>'."""
        builder = InlineKeyboardBuilder()
        for code in LANGS:
            builder.button(text=LANG_NAMES[code], callback_data=f"setlang_{code}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_change_language(lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
        """One '🌐 Tilni o'zgartirish' button -> callback 'lang_menu' (opens the picker)."""
        builder = InlineKeyboardBuilder()
        builder.button(text=t(lang, "btn.change_language"), callback_data="lang_menu")
        return builder.as_markup()

    @staticmethod
    def get_apartment_actions(
        apartment_id: int,
        show_admin: bool = False,
        is_pending: bool = False,
        lang: str = DEFAULT_LANG,
    ) -> InlineKeyboardMarkup:
        """Get apartment action buttons (admin buttons are always Uzbek)."""
        builder = InlineKeyboardBuilder()

        if show_admin and is_pending:
            builder.button(
                text="✅ Tasdiqlash",
                callback_data=f"admin_approve_{apartment_id}"
            )
            builder.button(
                text="❌ Rad etish",
                callback_data=f"admin_reject_{apartment_id}"
            )
            builder.adjust(2)
        elif show_admin:
            builder.button(
                text="📦 Arxivlash",
                callback_data=f"admin_archive_{apartment_id}"
            )
            builder.button(
                text="🗑 O'chirish",
                callback_data=f"admin_delete_{apartment_id}"
            )
            builder.adjust(2)
        else:
            builder.button(
                text=t(lang, "btn.contact"),
                callback_data=f"contact_{apartment_id}"
            )

        return builder.as_markup()

    @staticmethod
    def get_admin_menu() -> InlineKeyboardMarkup:
        """Get admin menu (admin panel stays Uzbek)."""
        builder = InlineKeyboardBuilder()
        builder.button(text="⏳ Kutilayotgan e'lonlar", callback_data="admin_pending")
        builder.button(text="✅ Aktiv e'lonlar", callback_data="admin_active")
        builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
        builder.button(text="📊 Statistika", callback_data="admin_stats")
        builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast")
        builder.button(text="📥 E'lon import qilish", callback_data="admin_import")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_pagination(
        current_page: int,
        total_pages: int,
        callback_prefix: str = "page",
        lang: str = DEFAULT_LANG,
    ) -> InlineKeyboardMarkup:
        """Get pagination keyboard."""
        builder = InlineKeyboardBuilder()

        if current_page > 1:
            builder.button(text=t(lang, "btn.prev"), callback_data=f"{callback_prefix}_{current_page - 1}")

        builder.button(text=f"📄 {current_page}/{total_pages}", callback_data="noop")

        if current_page < total_pages:
            builder.button(text=t(lang, "btn.next"), callback_data=f"{callback_prefix}_{current_page + 1}")

        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def get_back_button(callback_data: str = "back", lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
        """Get simple back button."""
        builder = InlineKeyboardBuilder()
        builder.button(text=t(lang, "btn.back_inline"), callback_data=callback_data)
        return builder.as_markup()

    @staticmethod
    def get_user_actions(user_id: int, is_blocked: bool = False) -> InlineKeyboardMarkup:
        """Get user management actions (admin panel stays Uzbek)."""
        builder = InlineKeyboardBuilder()

        if is_blocked:
            builder.button(
                text="✅ Blokdan chiqarish",
                callback_data=f"admin_unblock_{user_id}"
            )
        else:
            builder.button(
                text="🚫 Bloklash",
                callback_data=f"admin_block_{user_id}"
            )

        builder.button(
            text="📋 E'lonlarini ko'rish",
            callback_data=f"admin_user_apartments_{user_id}"
        )
        builder.adjust(1)
        return builder.as_markup()
