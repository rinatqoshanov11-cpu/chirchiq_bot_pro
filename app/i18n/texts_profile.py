"""Bot profile texts (start-screen description, command menu) and price / listing-card texts.

Keys: ``profile.*`` (bot profile + listing card labels) and ``price.*``
(``price.per_month`` lives in texts_core.py).
"""

TEXTS = {
    # ---- Prices (app/utils/formatters.format_price) ----
    "price.negotiable": {
        "uz": "Kelishiladi",
        "ru": "Договорная",
        "en": "Negotiable",
    },
    # Name of the UZS currency after the number: "50 000 000 so'm"
    "price.som": {
        "uz": "so'm",
        "ru": "сум",
        "en": "UZS",
    },

    # ---- Listing card (app/utils/formatters.format_apartment_card) ----
    "profile.card_badge_rent": {
        "uz": "🔑 IJARAGA",
        "ru": "🔑 АРЕНДА",
        "en": "🔑 FOR RENT",
    },
    "profile.card_badge_sale": {
        "uz": "💰 SOTILADI",
        "ru": "💰 ПРОДАЖА",
        "en": "💰 FOR SALE",
    },
    # {rooms} = number of rooms
    "profile.card_rooms": {
        "uz": "{rooms} xonali kvartira",
        "ru": "{rooms}-комнатная квартира",
        "en": "{rooms}-room apartment",
    },
    # {area} = number, already HTML-safe
    "profile.card_area": {
        "uz": "📐 <b>{area}</b> m²",
        "ru": "📐 <b>{area}</b> м²",
        "en": "📐 <b>{area}</b> m²",
    },
    "profile.card_floor_of": {
        "uz": "🏢 <b>{floor} / {total}</b>-qavat",
        "ru": "🏢 Этаж: <b>{floor} / {total}</b>",
        "en": "🏢 Floor <b>{floor} / {total}</b>",
    },
    "profile.card_floor": {
        "uz": "🏢 <b>{floor}</b>-qavat",
        "ru": "🏢 Этаж: <b>{floor}</b>",
        "en": "🏢 Floor <b>{floor}</b>",
    },
    "profile.card_total_floors": {
        "uz": "🏢 {total} qavatli bino",
        "ru": "🏢 {total}-этажный дом",
        "en": "🏢 {total}-storey building",
    },
    # {name} = owner's name, already HTML-escaped
    "profile.card_owner": {
        "uz": "🙋 E'lon egasi: {name}",
        "ru": "🙋 Владелец объявления: {name}",
        "en": "🙋 Posted by: {name}",
    },

    # ---- Bot profile (app/utils/bot_profile.py) ----
    # Start screen, before the user presses START (max 512 chars).
    # {open_app} = t(lang, "btn.open_app")
    "profile.bot_description": {
        "uz": (
            "🏠 Chirchiq Kvartira — Chirchiq shahridagi kvartira e'lonlari ilovasi.\n\n"
            "📱 Qulay ilova: rasmli e'lonlar, filtr (ijara / sotuv, xonalar, narx), "
            "egasi bilan bir bosishda bog'lanish\n"
            "➕ O'z e'loningizni bepul joylang\n"
            "✅ Barcha e'lonlar admin tomonidan tekshiriladi\n"
            "🌐 Tillar: O'zbekcha, Русский, English\n\n"
            "«START» ni bosing, so'ng «{open_app}» tugmasi orqali e'lonlarni ko'ring 👇"
        ),
        "ru": (
            "🏠 Chirchiq Kvartira — приложение с объявлениями о квартирах в Чирчике.\n\n"
            "📱 Удобное приложение: объявления с фото, фильтры (аренда / продажа, комнаты, цена), "
            "связь с владельцем в одно касание\n"
            "➕ Размещайте своё объявление бесплатно\n"
            "✅ Все объявления проверяет администратор\n"
            "🌐 Языки: O'zbekcha, Русский, English\n\n"
            "Нажмите «Запустить» (START), затем кнопку «{open_app}», чтобы смотреть объявления 👇"
        ),
        "en": (
            "🏠 Chirchiq Kvartira — an app with apartment listings in Chirchiq.\n\n"
            "📱 Handy app: listings with photos, filters (rent / sale, rooms, price), "
            "contact the owner in one tap\n"
            "➕ Post your own listing for free\n"
            "✅ Every listing is checked by an admin\n"
            "🌐 Languages: O'zbekcha, Русский, English\n\n"
            "Press «START», then the «{open_app}» button to browse listings 👇"
        ),
    },
    # Bot profile page and shared links (max 120 chars).
    "profile.bot_short_description": {
        "uz": "Chirchiq kvartira e'lonlari ilovasi: ijara va sotuv, filtr, egasi bilan bog'lanish.",
        "ru": "Объявления о квартирах в Чирчике: аренда и продажа, фильтры, связь с владельцем.",
        "en": "Apartment listings in Chirchiq: rent and sale, filters, contact the owner.",
    },
    # Command menu (max 256 chars each)
    "profile.cmd_start": {
        "uz": "Botni boshlash / asosiy menyu",
        "ru": "Запустить бота / главное меню",
        "en": "Start the bot / main menu",
    },
    "profile.cmd_help": {
        "uz": "Botdan foydalanish qo'llanmasi",
        "ru": "Как пользоваться ботом",
        "en": "How to use the bot",
    },
    "profile.cmd_language": {
        "uz": "Tilni o'zgartirish",
        "ru": "Сменить язык",
        "en": "Change language",
    },
}
