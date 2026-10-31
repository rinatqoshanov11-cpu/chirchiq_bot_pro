"""Utility functions for the bot."""
import re
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException


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


def format_price(price: int, currency: str = "UZS") -> str:
    """Format price with thousand separators."""
    return f"{price:,} {currency}".replace(',', ' ')


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


def format_apartment_card(apartment, show_contact: bool = False) -> str:
    """
    Format apartment information as text card.

    Args:
        apartment: Apartment model instance
        show_contact: Whether to show contact information

    Returns:
        Formatted text
    """
    type_text = "🔑 Ijaraga" if apartment.type.value == "rent" else "💰 Sotiladi"

    text = f"{type_text}\n\n"
    text += f"🚪 {apartment.rooms}-xonali kvartira\n"

    if apartment.area:
        text += f"📐 Maydon: {apartment.area} m²\n"

    if apartment.floor and apartment.total_floors:
        text += f"🏢 Qavat: {apartment.floor}/{apartment.total_floors}\n"

    text += f"📍 Manzil: {apartment.address}\n"
    text += f"💵 Narx: {format_price(apartment.price)}\n"

    if show_contact:
        text += f"📱 Telefon: {apartment.phone_number}\n"
        if apartment.contact_name:
            text += f"👤 Ism: {apartment.contact_name}\n"

    if apartment.description:
        text += f"\n📝 {truncate_text(apartment.description, 200)}\n"

    text += f"\n👁 Ko'rishlar: {apartment.view_count}"

    if hasattr(apartment, 'owner') and apartment.owner:
        text += f"\n👤 E'lon egasi: {apartment.owner.full_name}"

    return text


def format_user_info(user) -> str:
    """Format user information."""
    text = f"👤 Foydalanuvchi ma'lumotlari\n\n"
    text += f"🆔 ID: {user.id}\n"
    text += f"📱 Telegram ID: {user.telegram_id}\n"

    if user.username:
        text += f"🔗 Username: @{user.username}\n"

    text += f"👤 Ism: {user.full_name}\n"
    text += f"📞 Telefon: {user.phone_number}\n"
    text += f"📍 Manzil: {user.address}\n"

    status = "✅ Faol" if user.is_active else "❌ Nofaol"
    if user.is_blocked:
        status = "🚫 Bloklangan"

    text += f"📊 Status: {status}\n"

    if user.is_admin:
        text += f"🔐 Admin: Ha\n"

    text += f"📅 Ro'yxatdan o'tgan: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n"

    if user.last_activity:
        text += f"⏰ Oxirgi faollik: {user.last_activity.strftime('%Y-%m-%d %H:%M')}\n"

    return text
