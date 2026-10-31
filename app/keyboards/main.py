"""Keyboard layouts for the bot."""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Optional


class MainKeyboard:
    """Main menu keyboards."""

    @staticmethod
    def get_main_menu(is_registered: bool = True) -> ReplyKeyboardMarkup:
        """Get main menu keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="🏠 Kvartira qidirish")

        if is_registered:
            builder.button(text="➕ E'lon qo'shish")
            builder.button(text="📋 Mening e'lonlarim")
            builder.button(text="⚙️ Sozlamalar")
            builder.adjust(2, 2)
        else:
            builder.button(text="📝 Ro'yxatdan o'tish")
            builder.adjust(2)

        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_search_menu() -> ReplyKeyboardMarkup:
        """Get search menu keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="🔑 Ijaraga")
        builder.button(text="💰 Sotib olish")
        builder.button(text="📋 Barcha e'lonlar")
        builder.button(text="🔙 Orqaga")
        builder.adjust(2, 1, 1)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Get cancel keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="❌ Bekor qilish")
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Get skip and cancel keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="⏩ O'tkazib yuborish")
        builder.button(text="❌ Bekor qilish")
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_phone_keyboard() -> ReplyKeyboardMarkup:
        """Get phone number request keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="📱 Telefon raqamni yuborish", request_contact=True)
        builder.button(text="❌ Bekor qilish")
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


class ApartmentKeyboard:
    """Apartment related keyboards."""

    @staticmethod
    def get_apartment_type() -> ReplyKeyboardMarkup:
        """Get apartment type selection keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="🔑 Ijaraga berish")
        builder.button(text="💰 Sotish")
        builder.button(text="❌ Bekor qilish")
        builder.adjust(2, 1)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def get_rooms_keyboard() -> ReplyKeyboardMarkup:
        """Get rooms selection keyboard."""
        builder = ReplyKeyboardBuilder()
        for i in range(1, 7):
            builder.button(text=str(i))
        builder.button(text="6+")
        builder.button(text="❌ Bekor qilish")
        builder.adjust(3, 3, 1, 1)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def get_confirm_keyboard() -> ReplyKeyboardMarkup:
        """Get confirmation keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="✅ Tasdiqlash")
        builder.button(text="✏️ Tahrirlash")
        builder.button(text="❌ Bekor qilish")
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def get_photos_done_keyboard() -> ReplyKeyboardMarkup:
        """Get photos done keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="✅ Tayyor")
        builder.button(text="❌ Bekor qilish")
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)


class InlineKeyboards:
    """Inline keyboards for various purposes."""

    @staticmethod
    def get_apartment_actions(
        apartment_id: int,
        show_admin: bool = False,
        is_pending: bool = False
    ) -> InlineKeyboardMarkup:
        """Get apartment action buttons."""
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
                text="📞 Bog'lanish",
                callback_data=f"contact_{apartment_id}"
            )

        return builder.as_markup()

    @staticmethod
    def get_admin_menu() -> InlineKeyboardMarkup:
        """Get admin menu."""
        builder = InlineKeyboardBuilder()
        builder.button(text="⏳ Kutilayotgan e'lonlar", callback_data="admin_pending")
        builder.button(text="✅ Aktiv e'lonlar", callback_data="admin_active")
        builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
        builder.button(text="📊 Statistika", callback_data="admin_stats")
        builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_pagination(
        current_page: int,
        total_pages: int,
        callback_prefix: str = "page"
    ) -> InlineKeyboardMarkup:
        """Get pagination keyboard."""
        builder = InlineKeyboardBuilder()

        if current_page > 1:
            builder.button(text="◀️ Orqaga", callback_data=f"{callback_prefix}_{current_page - 1}")

        builder.button(text=f"📄 {current_page}/{total_pages}", callback_data="noop")

        if current_page < total_pages:
            builder.button(text="Keyingi ▶️", callback_data=f"{callback_prefix}_{current_page + 1}")

        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def get_back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
        """Get simple back button."""
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Orqaga", callback_data=callback_data)
        return builder.as_markup()

    @staticmethod
    def get_user_actions(user_id: int, is_blocked: bool = False) -> InlineKeyboardMarkup:
        """Get user management actions."""
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
