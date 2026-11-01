"""Button labels used by app/keyboards/main.py and keyboard placeholders.

The "uz" text of every key is EXACTLY the label used before translations existed,
so old chats (and handlers that still compare with Uzbek strings) keep working.
"""

TEXTS = {
    # ---- Main menu (reply keyboard) ----
    "btn.open_app": {
        "uz": "📱 Ilovani ochish",
        "ru": "📱 Открыть приложение",
        "en": "📱 Open app",
    },
    "btn.add_listing": {
        "uz": "➕ E'lon qo'shish",
        "ru": "➕ Добавить объявление",
        "en": "➕ Add listing",
    },
    "btn.settings": {
        "uz": "⚙️ Sozlamalar",
        "ru": "⚙️ Настройки",
        "en": "⚙️ Settings",
    },
    "btn.register": {
        "uz": "📝 Ro'yxatdan o'tish",
        "ru": "📝 Регистрация",
        "en": "📝 Register",
    },

    # ---- Common reply buttons ----
    "btn.cancel": {
        "uz": "❌ Bekor qilish",
        "ru": "❌ Отмена",
        "en": "❌ Cancel",
    },
    "btn.skip": {
        "uz": "⏩ O'tkazib yuborish",
        "ru": "⏩ Пропустить",
        "en": "⏩ Skip",
    },
    "btn.done": {
        "uz": "✅ Tayyor",
        "ru": "✅ Готово",
        "en": "✅ Done",
    },
    "btn.send_phone": {
        "uz": "📱 Telefon raqamni yuborish",
        "ru": "📱 Отправить номер телефона",
        "en": "📱 Share phone number",
    },

    # ---- Listing form ----
    "btn.type_rent": {
        "uz": "🔑 Ijaraga berish",
        "ru": "🔑 Сдать в аренду",
        "en": "🔑 Rent out",
    },
    "btn.type_sale": {
        "uz": "💰 Sotish",
        "ru": "💰 Продать",
        "en": "💰 Sell",
    },
    "btn.confirm": {
        "uz": "✅ Tasdiqlash",
        "ru": "✅ Подтвердить",
        "en": "✅ Confirm",
    },
    "btn.edit": {
        "uz": "✏️ Tahrirlash",
        "ru": "✏️ Изменить",
        "en": "✏️ Edit",
    },
    "btn.send_location": {
        "uz": "📍 Joylashuvni yuborish",
        "ru": "📍 Отправить локацию",
        "en": "📍 Send location",
    },
    "btn.other_area": {
        "uz": "✍️ Boshqa hudud",
        "ru": "✍️ Другой район",
        "en": "✍️ Other area",
    },
    # Preset templates ({n} = number)
    "btn.price_mln": {
        "uz": "{n} mln",
        "ru": "{n} млн",
        "en": "{n} mln",
    },
    "btn.area_m2": {
        "uz": "{n} m²",
        "ru": "{n} м²",
        "en": "{n} m²",
    },
    "btn.total_floors_n": {
        "uz": "{n} qavatli",
        "ru": "{n}-этажный",
        "en": "{n} floors",
    },

    # ---- "✏️ Tahrirlash": which field to change ----
    "btn.edit_type": {
        "uz": "🏷 Turi",
        "ru": "🏷 Тип",
        "en": "🏷 Type",
    },
    "btn.edit_rooms": {
        "uz": "🚪 Xonalar",
        "ru": "🚪 Комнаты",
        "en": "🚪 Rooms",
    },
    "btn.edit_address": {
        "uz": "📍 Manzil",
        "ru": "📍 Адрес",
        "en": "📍 Address",
    },
    "btn.edit_price": {
        "uz": "💵 Narx",
        "ru": "💵 Цена",
        "en": "💵 Price",
    },
    "btn.edit_area": {
        "uz": "📐 Maydon",
        "ru": "📐 Площадь",
        "en": "📐 Area",
    },
    "btn.edit_floor": {
        "uz": "🏢 Qavat",
        "ru": "🏢 Этаж",
        "en": "🏢 Floor",
    },
    "btn.edit_description": {
        "uz": "📝 Tavsif",
        "ru": "📝 Описание",
        "en": "📝 Description",
    },
    "btn.edit_photos": {
        "uz": "📸 Rasmlar",
        "ru": "📸 Фото",
        "en": "📸 Photos",
    },
    "btn.edit_back": {
        "uz": "⬅️ Ko'rinishga qaytish",
        "ru": "⬅️ Назад к просмотру",
        "en": "⬅️ Back to preview",
    },

    # ---- Inline buttons ----
    "btn.view_listings": {
        "uz": "📱 E'lonlarni ko'rish",
        "ru": "📱 Смотреть объявления",
        "en": "📱 View listings",
    },
    "btn.contact": {
        "uz": "📞 Bog'lanish",
        "ru": "📞 Связаться",
        "en": "📞 Contact",
    },
    "btn.prev": {
        "uz": "◀️ Orqaga",
        "ru": "◀️ Назад",
        "en": "◀️ Back",
    },
    "btn.next": {
        "uz": "Keyingi ▶️",
        "ru": "Далее ▶️",
        "en": "Next ▶️",
    },
    "btn.back_inline": {
        "uz": "🔙 Orqaga",
        "ru": "🔙 Назад",
        "en": "🔙 Back",
    },
    "btn.back": {
        "uz": "⬅️ Orqaga",
        "ru": "⬅️ Назад",
        "en": "⬅️ Back",
    },
    # Settings screen -> opens the language picker (callback "lang_menu")
    "btn.change_language": {
        "uz": "🌐 Tilni o'zgartirish",
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change language",
    },

    # ---- Placeholders shown in the message field ----
    "ph.price": {
        "uz": "Masalan: 3 mln yoki $45 000",
        "ru": "Например: 3 млн или $45 000",
        "en": "e.g. 3 mln or $45 000",
    },
    "ph.city_area": {
        "uz": "Hududni tanlang",
        "ru": "Выберите район",
        "en": "Choose an area",
    },
    "ph.address_detail": {
        "uz": "Masalan: Navoiy ko'chasi, 12-uy",
        "ru": "Например: ул. Навои, дом 12",
        "en": "e.g. Navoi street, house 12",
    },
    "ph.area": {
        "uz": "Masalan: 65",
        "ru": "Например: 65",
        "en": "e.g. 65",
    },
    "ph.floor": {
        "uz": "Masalan: 5 yoki 5/9",
        "ru": "Например: 5 или 5/9",
        "en": "e.g. 5 or 5/9",
    },
    "ph.total_floors": {
        "uz": "Masalan: 9",
        "ru": "Например: 9",
        "en": "e.g. 9",
    },
    "ph.description": {
        "uz": "Yoki o'zingiz yozing...",
        "ru": "Или напишите сами...",
        "en": "Or type your own...",
    },
}
