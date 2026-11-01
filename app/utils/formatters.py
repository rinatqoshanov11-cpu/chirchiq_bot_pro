"""Utility functions for the bot."""
import html
import re
from typing import Optional

import phonenumbers
from phonenumbers import NumberParseException
from sqlalchemy import inspect as sa_inspect

from app.i18n import t


# Telegram limit for photo captions (characters).
CAPTION_LIMIT = 1024
# How much of the description is shown on a listing card.
CARD_DESCRIPTION_LIMIT = 300

_SOM_ALIASES = {"UZS", "SUM", "SO'M", "SOM", "СУМ", "СЎМ"}
_DIVIDER = "──────────────"


def validate_phone_number(phone: str) -> Optional[str]:
    """
    Validate and format phone number.

    Args:
        phone: Phone number string

    Returns:
        Formatted phone number or None if invalid
    """
    # Clean phone number
    cleaned = re.sub(r'[^0-9+]', '', phone)

    try:
        # Parse phone number (assuming Uzbekistan by default)
        parsed = phonenumbers.parse(cleaned, "UZ")

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
    except NumberParseException:
        pass

    # Fallback: if it looks like Uzbek number
    if cleaned.startswith('+998') and len(cleaned) == 13:
        return cleaned
    elif cleaned.startswith('998') and len(cleaned) == 12:
        return '+' + cleaned
    elif len(cleaned) == 9:
        return '+998' + cleaned

    return None


def format_price(price, currency: str = "UZS", lang: str = "uz") -> str:
    """
    Format price with space thousand separators, in the given language.

    "UZS" (and its aliases) is shown as t(lang, "price.som"):
        50000000 -> "50 000 000 so'm" / "50 000 000 сум" / "50 000 000 UZS".
    "USD" is "$45 000" in every language.
    Any other currency is shown as-is: 1200, "EUR" -> "1 200 EUR".
    None -> t(lang, "price.negotiable") ("Kelishiladi" / "Договорная" / "Negotiable").
    """
    if price is None:
        return t(lang, "price.negotiable")

    try:
        value = float(price)
    except (TypeError, ValueError):
        return f"{price} {currency or ''}".strip()

    if value.is_integer():
        number = f"{int(value):,}"
    else:
        number = f"{value:,.2f}".rstrip("0").rstrip(".")
    number = number.replace(",", " ")

    code = (currency or "UZS").strip()
    if code.upper() in _SOM_ALIASES:
        code = t(lang, "price.som")
    elif code.upper() in ("USD", "$"):
        return f"${number}"
    return f"{number} {code}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text


# ---------------------------------------------------------------------------
# HTML helpers (the bot uses ParseMode.HTML by default)
# ---------------------------------------------------------------------------

def _esc(value) -> str:
    """HTML-escape any user-supplied value (None -> empty string)."""
    if value is None:
        return ""
    return html.escape(str(value), quote=False)


def _esc_short(value, max_length: int) -> str:
    """Truncate raw text to ``max_length`` characters (with "…"), then escape it."""
    text = " ".join(str(value or "").split())  # collapse whitespace / newlines
    if len(text) > max_length:
        text = text[:max_length - 1].rstrip() + "…"
    return _esc(text)


def _esc_paragraph(value, max_length: int, max_escaped: Optional[int] = None) -> str:
    """
    Escape a multi-line text, keeping line breaks (max 2 in a row).

    Shows at most ``max_length`` characters of the original text and makes sure
    the escaped result is at most ``max_escaped`` characters long (adds "…").
    """
    text = str(value or "").replace("\r\n", "\n").strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if max_escaped is None:
        max_escaped = len(text) * 5 + 1

    escaped = _esc(text)
    if len(text) <= max_length and len(escaped) <= max_escaped:
        return escaped

    parts, size = [], 0
    for char in text[:max_length - 1]:
        piece = _esc(char)
        if size + len(piece) > max_escaped - 1:
            break
        parts.append(piece)
        size += len(piece)
    result = "".join(parts).rstrip()
    return result + "…" if result else ""


_TAG_RE = re.compile(r"<(/?)([a-zA-Z0-9-]+)[^>]*>")


def _safe_html_truncate(text: str, limit: int = CAPTION_LIMIT) -> str:
    """
    Cut HTML text to ``limit`` characters without breaking markup.

    Never cuts inside a tag or an HTML entity, and closes any tags left open.
    """
    if len(text) <= limit:
        return text

    ellipsis = "…"
    # Reserve room for the ellipsis and for closing tags.
    cut = text[:max(0, limit - len(ellipsis) - 20)]

    # Do not end inside a tag: "<b" / "</i"
    lt, gt = cut.rfind("<"), cut.rfind(">")
    if lt > gt:
        cut = cut[:lt]
    # Do not end inside an entity: "&amp" / "&lt"
    amp, semi = cut.rfind("&"), cut.rfind(";")
    if amp > semi and amp >= len(cut) - 10:
        cut = cut[:amp]

    # Close tags that are still open.
    stack = []
    for closing, name in _TAG_RE.findall(cut):
        name = name.lower()
        if closing:
            if name in stack:
                while stack and stack.pop() != name:
                    pass
        else:
            stack.append(name)
    closing_tags = "".join(f"</{name}>" for name in reversed(stack))

    return cut.rstrip() + ellipsis + closing_tags


def _format_number(value) -> str:
    """65.0 -> "65", 65.5 -> "65.5"."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _esc(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".rstrip("0").rstrip(".")


def _loaded_owner(apartment):
    """Return apartment.owner only if it is already loaded (never lazy-loads)."""
    try:
        state = sa_inspect(apartment, raiseerr=False)
    except Exception:
        state = None
    if state is not None:
        if "owner" in state.unloaded:
            return None
        return state.dict.get("owner")
    # Not an SQLAlchemy instance (e.g. a plain object) — use the attribute.
    return getattr(apartment, "owner", None)


def _enum_value(value) -> str:
    return str(getattr(value, "value", value) or "")


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def format_apartment_card(apartment, show_contact: bool = False, lang: str = "uz") -> str:
    """
    Format apartment information as an HTML card (used as a photo caption).

    The result is always shorter than Telegram's 1024-character caption limit.

    Args:
        apartment: Apartment model instance
        show_contact: Whether to show contact information
        lang: Card language ("uz" / "ru" / "en"); the admin panel uses the default "uz"

    Returns:
        Formatted HTML text
    """
    is_rent = _enum_value(apartment.type) == "rent"
    badge = t(lang, "profile.card_badge_rent" if is_rent else "profile.card_badge_sale")
    rooms = t(lang, "profile.card_rooms", rooms=_esc(apartment.rooms))

    lines = [f"<b>{badge} · {rooms}</b>", ""]

    # Price
    price = format_price(
        apartment.price, getattr(apartment, "currency", None) or "UZS", lang=lang
    )
    price_line = f"💵 <b>{_esc(price)}</b>"
    if is_rent:
        price_line += _esc(t(lang, "price.per_month"))
    lines.append(price_line)
    lines.append("")

    # Details
    address = _esc_short(apartment.address, 150)
    district = getattr(apartment, "district", None)
    if district:
        address += f" ({_esc_short(district, 50)})"
    lines.append(f"📍 {address}")

    if apartment.area:
        lines.append(t(lang, "profile.card_area", area=_format_number(apartment.area)))

    floor = apartment.floor
    total_floors = apartment.total_floors
    if floor and total_floors:
        lines.append(t(lang, "profile.card_floor_of", floor=_esc(floor), total=_esc(total_floors)))
    elif floor:
        lines.append(t(lang, "profile.card_floor", floor=_esc(floor)))
    elif total_floors:
        lines.append(t(lang, "profile.card_total_floors", total=_esc(total_floors)))

    # Contact
    if show_contact:
        lines.append("")
        if apartment.phone_number:
            lines.append(f"📱 <b>{_esc_short(apartment.phone_number, 30)}</b>")
        if apartment.contact_name:
            lines.append(f"👤 {_esc_short(apartment.contact_name, 60)}")

    # Footer
    footer = [_DIVIDER, f"👁 {_esc(apartment.view_count or 0)} · 🆔 #{_esc(apartment.id)}"]
    owner = _loaded_owner(apartment)
    if owner is not None and getattr(owner, "full_name", None):
        footer.append(t(lang, "profile.card_owner", name=_esc_short(owner.full_name, 60)))

    head = "\n".join(lines)
    tail = "\n".join(footer)

    # Description: as much as fits (max CARD_DESCRIPTION_LIMIT chars).
    if apartment.description:
        reserve = len(head) + len(tail) + len("\n\n📝 <i></i>\n\n") + 16
        room = CAPTION_LIMIT - reserve
        description = ""
        if room > 20:
            description = _esc_paragraph(
                apartment.description, CARD_DESCRIPTION_LIMIT, room
            )
        if description:
            head += f"\n\n📝 <i>{description}</i>"

    text = f"{head}\n\n{tail}"
    return _safe_html_truncate(text, CAPTION_LIMIT - 4)


def format_user_info(user, lang: str = "uz") -> str:
    """Format user information as an HTML profile card (lang: 'uz' | 'ru' | 'en'; admin panel uses 'uz')."""
    from app.i18n import t as _t

    lines = [_t(lang, "settings.profile_title"), ""]

    lines.append(_t(lang, "settings.profile_name", value=_esc_short(user.full_name, 100)))
    if user.username:
        lines.append(_t(lang, "settings.profile_username", value=_esc_short(user.username, 64)))
    lines.append(_t(lang, "settings.profile_phone", value=_esc_short(user.phone_number, 30)))
    lines.append(_t(lang, "settings.profile_address", value=_esc_short(user.address, 200)))

    lines.append("")
    lines.append(_t(lang, "settings.profile_id", value=_esc(user.telegram_id)))

    if user.is_blocked:
        status = _t(lang, "settings.status_blocked")
    elif user.is_active:
        status = _t(lang, "settings.status_active")
    else:
        status = _t(lang, "settings.status_inactive")
    lines.append(_t(lang, "settings.profile_status", value=status))

    if user.is_admin:
        lines.append(_t(lang, "settings.profile_admin"))

    if getattr(user, "created_at", None):
        lines.append(_t(lang, "settings.profile_registered", value=user.created_at.strftime('%d.%m.%Y')))

    if getattr(user, "last_activity", None):
        lines.append(_t(lang, "settings.profile_last_activity",
                        value=user.last_activity.strftime('%d.%m.%Y %H:%M')))

    return "\n".join(lines)
