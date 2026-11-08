"""Inline-button labels and toasts of the listing form (app/handlers/apartments.py). Keys: lf.*

The listing form is driven by inline keyboards (callback_data prefix "lf:"); the common labels
(cancel / skip / done / confirm / edit / type / edit fields) are reused from btn.*.
"""

TEXTS = {
    # Shown on a step message after a button was tapped (its buttons are removed)
    "lf.chosen": {
        "uz": "✅ Tanlandi: <b>{value}</b>",
        "ru": "✅ Выбрано: <b>{value}</b>",
        "en": "✅ Chosen: <b>{value}</b>",
    },
    # Toast for a button of a step that is already over (double tap / old message)
    "lf.stale": {
        "uz": "⌛ Bu qadam allaqachon o'tilgan.",
        "ru": "⌛ Этот шаг уже пройден.",
        "en": "⌛ This step is already done.",
    },
    # Photos step: the "done" button while there are not enough photos yet
    "lf.photos_need": {
        "uz": "📸 Yana kamida {more} ta rasm kerak",
        "ru": "📸 Нужно ещё минимум {more} фото",
        "en": "📸 At least {more} more photo(s) needed",
    },
    # Photos step: the "done" button once enough photos were sent
    "lf.photos_done": {
        "uz": "✅ Tayyor ({n} ta rasm)",
        "ru": "✅ Готово ({n} фото)",
        "en": "✅ Done ({n} photos)",
    },
    # Import: use the admin's own phone number
    "lf.phone_self": {
        "uz": "📱 O'zimning raqamim: {phone}",
        "ru": "📱 Мой номер: {phone}",
        "en": "📱 My own number: {phone}",
    },
}
