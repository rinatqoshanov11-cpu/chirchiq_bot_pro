"""Core texts: language picker, city name, price suffix, chat menu button."""

TEXTS = {
    # Shown before a language is chosen, so it is the same in every language
    "lang.picker": {
        "uz": "🌐 Tilni tanlang / Выберите язык / Choose language",
        "ru": "🌐 Tilni tanlang / Выберите язык / Choose language",
        "en": "🌐 Tilni tanlang / Выберите язык / Choose language",
    },
    "lang.confirm": {
        "uz": "✅ Til: O'zbekcha",
        "ru": "✅ Язык: Русский",
        "en": "✅ Language: English",
    },
    # Line for the settings screen; {name} = LANG_NAMES[lang]
    "lang.current": {
        "uz": "🌐 Til: {name}",
        "ru": "🌐 Язык: {name}",
        "en": "🌐 Language: {name}",
    },
    "lang.save_error": {
        "uz": "⚠️ Tilni saqlab bo'lmadi. Birozdan so'ng qayta urinib ko'ring.",
        "ru": "⚠️ Не удалось сохранить язык. Попробуйте ещё раз чуть позже.",
        "en": "⚠️ Could not save the language. Please try again in a moment.",
    },
    # Only used if registration.send_welcome is missing
    "lang.menu_hint": {
        "uz": "👇 Asosiy menyu",
        "ru": "👇 Главное меню",
        "en": "👇 Main menu",
    },
    "city": {
        "uz": "Chirchiq",
        "ru": "Чирчик",
        "en": "Chirchiq",
    },
    "price.per_month": {
        "uz": " / oy",
        "ru": " / мес",
        "en": " / month",
    },
    # Chat menu button (next to the message field) that opens the mini app
    "btn.app_menu": {
        "uz": "Ilova",
        "ru": "Приложение",
        "en": "App",
    },
}
