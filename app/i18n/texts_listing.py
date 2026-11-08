"""Listing-creation flow texts (app/handlers/apartments.py). Keys: listing.*

Button labels quoted in «...» must match the btn.* labels of the same language.
"""

# Description chips (index i is the same feature in every language)
_TAGS = {
    "rent": {
        "uz": ["Remont qilingan", "Mebelli", "Konditsioner", "Kir yuvish mashinasi",
               "Internet (Wi-Fi)", "Oilaga", "Talabalarga", "Kommunal to'lovlar ichida"],
        "ru": ["Ремонт", "С мебелью", "Кондиционер", "Стиральная машина",
               "Интернет (Wi-Fi)", "Для семьи", "Для студентов", "Коммунальные включены"],
        "en": ["Renovated", "Furnished", "Air conditioner", "Washing machine",
               "Internet (Wi-Fi)", "For a family", "For students", "Utilities included"],
    },
    "sale": {
        "uz": ["Remont qilingan", "Mebeli bilan", "Hujjatlari tayyor", "Ipoteka mumkin",
               "Yangi bino", "Avtoturargoh bor", "Narxi kelishiladi", "Ayirboshlash mumkin"],
        "ru": ["Ремонт", "С мебелью", "Документы готовы", "Ипотека возможна",
               "Новостройка", "Есть парковка", "Торг уместен", "Возможен обмен"],
        "en": ["Renovated", "Furnished", "Documents ready", "Mortgage possible",
               "New building", "Parking available", "Price negotiable", "Exchange possible"],
    },
}
# Number of chips per type (the same in every language)
TAG_COUNT = {kind: len(by_lang["uz"]) for kind, by_lang in _TAGS.items()}

TEXTS = {
    # ---- start ----
    "listing.need_register": {
        "uz": "📝 E'lon qo'shish uchun avval ro'yxatdan o'ting.\n\n"
              "«📝 Ro'yxatdan o'tish» tugmasini bosing — bor-yo'g'i 3 qadam.",
        "ru": "📝 Чтобы добавить объявление, сначала зарегистрируйтесь.\n\n"
              "Нажмите «📝 Регистрация» — всего 3 шага.",
        "en": "📝 Please register first to add a listing.\n\n"
              "Tap «📝 Register» — it takes just 3 steps.",
    },
    "listing.blocked": {
        "uz": "🚫 Siz bloklangansiz. Savollar bo'lsa, {contact}.",
        "ru": "🚫 Вы заблокированы. Если есть вопросы, {contact}.",
        "en": "🚫 You are blocked. If you have questions, {contact}.",
    },
    "listing.contact_admin": {
        "uz": "admin bilan bog'laning",
        "ru": "свяжитесь с администратором",
        "en": "contact the admin",
    },
    "listing.contact_admin_link": {
        "uz": "admin bilan bog'laning: {link}",
        "ru": "свяжитесь с администратором: {link}",
        "en": "contact the admin: {link}",
    },
    "listing.new": {
        "uz": "🏠 <b>Yangi e'lon</b>\n\nBir necha savolga javob bering — 1-2 daqiqa vaqt oladi.",
        "ru": "🏠 <b>Новое объявление</b>\n\nОтветьте на несколько вопросов — это займёт 1–2 минуты.",
        "en": "🏠 <b>New listing</b>\n\nAnswer a few questions — it takes 1–2 minutes.",
    },

    # ---- type ----
    "listing.ask_type": {
        "uz": "🏷 <b>E'lon turi</b>\n\nKvartirani ijaraga berasizmi yoki sotasizmi?",
        "ru": "🏷 <b>Тип объявления</b>\n\nВы сдаёте квартиру в аренду или продаёте?",
        "en": "🏷 <b>Listing type</b>\n\nAre you renting the apartment out or selling it?",
    },
    "listing.type_invalid": {
        "uz": "👇 Iltimos, pastdagi tugmalardan birini tanlang.",
        "ru": "👇 Пожалуйста, выберите один из вариантов кнопкой ниже.",
        "en": "👇 Please choose one of the buttons below.",
    },
    "listing.type_changed": {
        "uz": "ℹ️ Tur o'zgardi — narxni ham yangilang.",
        "ru": "ℹ️ Тип изменился — укажите и новую цену.",
        "en": "ℹ️ The type has changed — please update the price too.",
    },

    # ---- rooms ----
    "listing.ask_rooms": {
        "uz": "🚪 <b>Necha xonali kvartira?</b>",
        "ru": "🚪 <b>Сколько комнат в квартире?</b>",
        "en": "🚪 <b>How many rooms does the apartment have?</b>",
    },
    "listing.rooms_invalid": {
        "uz": "⚠️ Xonalar sonini tugma orqali tanlang (1 dan 6+ gacha).",
        "ru": "⚠️ Выберите количество комнат кнопкой (от 1 до 6+).",
        "en": "⚠️ Choose the number of rooms with a button (1 to 6+).",
    },

    # ---- address ----
    "listing.ask_address": {
        "uz": "📍 <b>Kvartira Chirchiqning qaysi hududida?</b>\n\n"
              "Pastdagi tugmadan hududni tanlang 👇",
        "ru": "📍 <b>В каком районе Чирчика находится квартира?</b>\n\n"
              "Выберите район кнопкой ниже 👇",
        "en": "📍 <b>Which area of Chirchiq is the apartment in?</b>\n\n"
              "Choose the area with a button below 👇",
    },
    "listing.ask_address_detail": {
        "uz": "📍 <b>{area}</b>\n\n"
              "Ko'cha va uy raqamini yozing (masalan: <i>Navoiy ko'chasi, 12-uy</i>)\n"
              "yoki «⏩ O'tkazib yuborish» ni bosing.",
        "ru": "📍 <b>{area}</b>\n\n"
              "Напишите улицу и номер дома (например: <i>ул. Навои, дом 12</i>)\n"
              "или нажмите «⏩ Пропустить».",
        "en": "📍 <b>{area}</b>\n\n"
              "Type the street and house number (for example: <i>Navoi street, house 12</i>)\n"
              "or tap «⏩ Skip».",
    },
    "listing.ask_full_address": {
        "uz": "✍️ Manzilni to'liq yozing.\nMasalan: <i>Chirchiq, Bo'zsuv, Navoiy ko'chasi 7-uy</i>",
        "ru": "✍️ Напишите полный адрес.\nНапример: <i>Чирчик, Бозсу, ул. Навои, дом 7</i>",
        "en": "✍️ Type the full address.\nFor example: <i>Chirchiq, Bozsuv, Navoi street, house 7</i>",
    },
    "listing.address_invalid": {
        "uz": "⚠️ Hududni tugmadan tanlang yoki manzilni to'liq yozing.",
        "ru": "⚠️ Выберите район кнопкой или напишите полный адрес.",
        "en": "⚠️ Choose an area with a button or type the full address.",
    },
    "listing.address_detail_invalid": {
        "uz": "⚠️ Ko'cha va uy raqamini yozing yoki «⏩ O'tkazib yuborish» ni bosing.",
        "ru": "⚠️ Напишите улицу и номер дома или нажмите «⏩ Пропустить».",
        "en": "⚠️ Type the street and house number or tap «⏩ Skip».",
    },

    # ---- location ----
    "listing.ask_location": {
        "uz": "🗺 <b>Kvartira joylashuvini yuboring</b>\n\n"
              "Kvartira yonida turgan bo'lsangiz — pastdagi «📍 Joylashuvni yuborish» ni bosing.\n"
              "Boshqa joyda bo'lsangiz: 📎 → <b>Joylashuv</b> → xaritada kvartirani belgilang.\n\n"
              "Xaridorlar uni xaritada ko'radi. Xohlamasangiz — «⏩ O'tkazib yuborish».",
        "ru": "🗺 <b>Отправьте местоположение квартиры</b>\n\n"
              "Если вы сейчас рядом с квартирой — нажмите внизу «📍 Отправить локацию».\n"
              "Если нет: 📎 → <b>Геопозиция</b> → отметьте квартиру на карте.\n\n"
              "Клиенты увидят её на карте. Если не хотите — «⏩ Пропустить».",
        "en": "🗺 <b>Send the apartment's location</b>\n\n"
              "If you are at the apartment now, tap «📍 Send location» below.\n"
              "If not: 📎 → <b>Location</b> → mark the apartment on the map.\n\n"
              "People will see it on the map. If you'd rather not, tap «⏩ Skip».",
    },
    "listing.location_saved": {
        "uz": "✅ Joylashuv saqlandi.",
        "ru": "✅ Местоположение сохранено.",
        "en": "✅ Location saved.",
    },
    "listing.location_or_skip": {
        "uz": "Joylashuvni yubormasangiz ham bo'ladi 👇",
        "ru": "Местоположение можно и не отправлять 👇",
        "en": "You can also skip the location 👇",
    },
    "listing.location_skipped": {
        "uz": "⏩ Joylashuv o'tkazib yuborildi.",
        "ru": "⏩ Местоположение пропущено.",
        "en": "⏩ Location skipped.",
    },
    "listing.location_invalid": {
        "uz": "📍 «📍 Joylashuvni yuborish» tugmasini bosing yoki «⏩ O'tkazib yuborish».",
        "ru": "📍 Нажмите «📍 Отправить локацию» или «⏩ Пропустить».",
        "en": "📍 Tap «📍 Send location» or «⏩ Skip».",
    },

    # ---- price ----
    "listing.ask_price_rent": {
        "uz": "💵 <b>Oylik ijara narxi qancha?</b>\n\n"
              "Qisqa yozishingiz mumkin:\n"
              "• <code>3 mln</code> → 3 000 000 so'm\n"
              "• <code>2,5 mln</code> → 2 500 000 so'm\n"
              "• <code>800 ming</code> → 800 000 so'm\n"
              "• <code>$400</code> → 400 dollar\n\n"
              "Yoki pastdagi tayyor narxlardan birini tanlang 👇",
        "ru": "💵 <b>Какая цена аренды в месяц?</b>\n\n"
              "Можно писать коротко:\n"
              "• <code>3 млн</code> → 3 000 000 сум\n"
              "• <code>2,5 млн</code> → 2 500 000 сум\n"
              "• <code>800 тыс</code> → 800 000 сум\n"
              "• <code>$400</code> → 400 долларов\n\n"
              "Или выберите готовую цену ниже 👇",
        "en": "💵 <b>What is the monthly rent?</b>\n\n"
              "You can write it short:\n"
              "• <code>3 mln</code> → 3 000 000 UZS\n"
              "• <code>2.5 mln</code> → 2 500 000 UZS\n"
              "• <code>800k</code> → 800 000 UZS\n"
              "• <code>$400</code> → 400 dollars\n\n"
              "Or choose one of the ready prices below 👇",
    },
    "listing.ask_price_sale": {
        "uz": "💵 <b>Sotish narxi qancha?</b>\n\n"
              "Qisqa yozishingiz mumkin:\n"
              "• <code>$45 000</code> → 45 000 dollar\n"
              "• <code>500 mln</code> → 500 000 000 so'm\n"
              "• <code>1,2 mlrd</code> → 1 200 000 000 so'm\n\n"
              "Yoki pastdagi tayyor narxlardan birini tanlang 👇",
        "ru": "💵 <b>Какая цена продажи?</b>\n\n"
              "Можно писать коротко:\n"
              "• <code>$45 000</code> → 45 000 долларов\n"
              "• <code>500 млн</code> → 500 000 000 сум\n"
              "• <code>1,2 млрд</code> → 1 200 000 000 сум\n\n"
              "Или выберите готовую цену ниже 👇",
        "en": "💵 <b>What is the sale price?</b>\n\n"
              "You can write it short:\n"
              "• <code>$45 000</code> → 45 000 dollars\n"
              "• <code>500 mln</code> → 500 000 000 UZS\n"
              "• <code>1200 mln</code> → 1 200 000 000 UZS\n\n"
              "Or choose one of the ready prices below 👇",
    },
    "listing.price_not_a_number": {
        "uz": "Narxni tushunmadim.",
        "ru": "Не удалось распознать цену.",
        "en": "I couldn't understand the price.",
    },
    "listing.price_too_low_rent": {
        "uz": "<b>{amount}</b> — oylik ijara uchun juda kichik narx.\nOdatda {low} dan {high} gacha bo'ladi.",
        "ru": "<b>{amount}</b> — слишком низкая цена для аренды в месяц.\nОбычно от {low} до {high}.",
        "en": "<b>{amount}</b> is too low for monthly rent.\nUsually it is between {low} and {high}.",
    },
    "listing.price_too_high_rent": {
        "uz": "<b>{amount}</b> — oylik ijara uchun juda katta narx.\nOdatda {low} dan {high} gacha bo'ladi.",
        "ru": "<b>{amount}</b> — слишком высокая цена для аренды в месяц.\nОбычно от {low} до {high}.",
        "en": "<b>{amount}</b> is too high for monthly rent.\nUsually it is between {low} and {high}.",
    },
    "listing.price_too_low_sale": {
        "uz": "<b>{amount}</b> — sotuv uchun juda kichik narx.\nOdatda {low} dan {high} gacha bo'ladi.",
        "ru": "<b>{amount}</b> — слишком низкая цена для продажи.\nОбычно от {low} до {high}.",
        "en": "<b>{amount}</b> is too low for a sale price.\nUsually it is between {low} and {high}.",
    },
    "listing.price_too_high_sale": {
        "uz": "<b>{amount}</b> — sotuv uchun juda katta narx.\nOdatda {low} dan {high} gacha bo'ladi.",
        "ru": "<b>{amount}</b> — слишком высокая цена для продажи.\nОбычно от {low} до {high}.",
        "en": "<b>{amount}</b> is too high for a sale price.\nUsually it is between {low} and {high}.",
    },
    "listing.price_retry": {
        "uz": "⚠️ {reason}\n\n"
              "Qaytadan yozing, masalan: <code>3 mln</code>, <code>800 ming</code> yoki <code>$45 000</code>",
        "ru": "⚠️ {reason}\n\n"
              "Напишите ещё раз, например: <code>3 млн</code>, <code>800 тыс</code> или <code>$45 000</code>",
        "en": "⚠️ {reason}\n\n"
              "Please type it again, for example: <code>3 mln</code>, <code>800k</code> or <code>$45 000</code>",
    },
    "listing.price_saved": {
        "uz": "✅ Narx: <b>{price}</b>{note}",
        "ru": "✅ Цена: <b>{price}</b>{note}",
        "en": "✅ Price: <b>{price}</b>{note}",
    },
    "listing.price_guessed_usd": {
        "uz": "\n<i>Valyuta yozilmagani uchun dollar deb tushundim. "
              "So'mda bo'lsa, «✏️ Tahrirlash» orqali o'zgartiring.</i>",
        "ru": "\n<i>Валюта не указана, поэтому я понял это как доллары. "
              "Если цена в сумах — измените её через «✏️ Изменить».</i>",
        "en": "\n<i>No currency was given, so I took it as dollars. "
              "If it is in so'm, change it with «✏️ Edit».</i>",
    },

    # ---- area ----
    "listing.ask_area": {
        "uz": "📐 <b>Kvartira maydoni qancha?</b>\n\n"
              "Pastdagi tugmadan tanlang yoki raqam bilan yozing, masalan <i>65</i>.",
        "ru": "📐 <b>Какая площадь квартиры?</b>\n\n"
              "Выберите кнопкой ниже или напишите числом, например <i>65</i>.",
        "en": "📐 <b>What is the apartment's area (m²)?</b>\n\n"
              "Choose a button below or type a number, for example <i>65</i>.",
    },
    "listing.area_invalid": {
        "uz": "⚠️ Maydonni tugmadan tanlang yoki raqam bilan yozing, masalan <i>65</i>.",
        "ru": "⚠️ Выберите площадь кнопкой или напишите числом, например <i>65</i>.",
        "en": "⚠️ Choose the area with a button or type a number, for example <i>65</i>.",
    },

    # ---- floor ----
    "listing.ask_floor": {
        "uz": "🏢 <b>Kvartira nechanchi qavatda?</b>\n\n"
              "Pastdagi tugmadan tanlang (yoki <i>5/9</i> deb yozing).",
        "ru": "🏢 <b>На каком этаже квартира?</b>\n\n"
              "Выберите кнопкой ниже (или напишите <i>5/9</i>).",
        "en": "🏢 <b>Which floor is the apartment on?</b>\n\n"
              "Choose a button below (or type <i>5/9</i>).",
    },
    "listing.floor_invalid": {
        "uz": "⚠️ Qavatni tugmadan tanlang yoki <i>5/9</i> deb yozing.",
        "ru": "⚠️ Выберите этаж кнопкой или напишите <i>5/9</i>.",
        "en": "⚠️ Choose the floor with a button or type <i>5/9</i>.",
    },
    "listing.ask_total_floors": {
        "uz": "🏢 <b>Bino necha qavatli?</b>",
        "ru": "🏢 <b>Сколько этажей в доме?</b>",
        "en": "🏢 <b>How many floors does the building have?</b>",
    },
    "listing.total_floors_invalid": {
        "uz": "⚠️ Bino qavatlari sonini tugmadan tanlang ({floor}-qavatdan kam bo'lmasin).",
        "ru": "⚠️ Выберите этажность дома кнопкой (не меньше {floor}).",
        "en": "⚠️ Choose the number of floors with a button (at least {floor}).",
    },

    # ---- description ----
    "listing.ask_description": {
        "uz": "📝 <b>Kvartira haqida qo'shimcha</b>\n\n"
              "Mos keladiganlarini belgilang, so'ng «✅ Tayyor» ni bosing.\n"
              "Xohlasangiz, o'zingiz ham yozib yuborishingiz mumkin.",
        "ru": "📝 <b>Дополнительно о квартире</b>\n\n"
              "Отметьте подходящее, затем нажмите «✅ Готово».\n"
              "При желании можете написать и свой текст.",
        "en": "📝 <b>More about the apartment</b>\n\n"
              "Tick what applies, then tap «✅ Done».\n"
              "You can also type your own text if you like.",
    },
    "listing.chips_hint": {
        "uz": "👇 Belgilang:",
        "ru": "👇 Отметьте:",
        "en": "👇 Tick:",
    },
    "listing.description_empty": {
        "uz": "⚠️ Belgilang va «✅ Tayyor» ni bosing, yoki matn yozing.",
        "ru": "⚠️ Отметьте варианты и нажмите «✅ Готово» или напишите текст.",
        "en": "⚠️ Tick the options and tap «✅ Done», or type some text.",
    },
    "listing.description_too_long": {
        "uz": "⚠️ Matn juda uzun ({n} belgi). Ko'pi bilan {max} ta belgi yozing.",
        "ru": "⚠️ Текст слишком длинный ({n} симв.). Напишите не более {max} символов.",
        "en": "⚠️ The text is too long ({n} characters). Please use at most {max} characters.",
    },

    # ---- photos ----
    "listing.ask_photos": {
        "uz": "📸 <b>Kvartira rasmlarini yuboring</b>\n\n"
              "Kamida <b>{min} ta</b>, ko'pi bilan {max} ta rasm. Bir nechtasini birdaniga yuborsangiz ham bo'ladi.\n"
              "Yuborib bo'lgach «✅ Tayyor» tugmasini bosing.",
        "ru": "📸 <b>Отправьте фото квартиры</b>\n\n"
              "Минимум <b>{min}</b>, максимум {max} фото. Можно отправить несколько сразу.\n"
              "Когда отправите, нажмите «✅ Готово».",
        "en": "📸 <b>Send photos of the apartment</b>\n\n"
              "At least <b>{min}</b>, at most {max} photos. You can send several at once.\n"
              "When you're done, tap «✅ Done».",
    },
    "listing.photos_have": {
        "uz": "Hozir: <b>{n} ta</b> rasm bor.",
        "ru": "Сейчас: <b>{n}</b> фото.",
        "en": "Currently: <b>{n}</b> photo(s).",
    },
    "listing.photos_progress": {
        "uz": "📸 <b>{n}/{max}</b> ta rasm qabul qilindi.\n{hint}",
        "ru": "📸 Принято фото: <b>{n}/{max}</b>.\n{hint}",
        "en": "📸 <b>{n}/{max}</b> photos received.\n{hint}",
    },
    "listing.photos_need_more": {
        "uz": "Yana kamida {more} ta rasm yuboring.",
        "ru": "Отправьте ещё минимум {more} фото.",
        "en": "Please send at least {more} more.",
    },
    "listing.photos_enough": {
        "uz": "Yana yuborishingiz yoki «✅ Tayyor» ni bosishingiz mumkin.",
        "ru": "Можете отправить ещё или нажать «✅ Готово».",
        "en": "You can send more or tap «✅ Done».",
    },
    "listing.import_photos_more": {
        "uz": "📸 Postda {k} ta rasm bor, kamida {min} ta kerak — yana rasm yuboring.",
        "ru": "📸 В посте {k} фото, нужно минимум {min} — отправьте ещё.",
        "en": "📸 The post has {k} photo(s), at least {min} are needed — send more.",
    },
    "listing.replace_photos": {
        "uz": "📸 Eski rasmlar o'rniga yangilarini yuboring.",
        "ru": "📸 Отправьте новые фото вместо старых.",
        "en": "📸 Send new photos to replace the old ones.",
    },
    "listing.photos_limit": {
        "uz": "⚠️ Ko'pi bilan {max} ta rasm. «✅ Tayyor» ni bosing.",
        "ru": "⚠️ Не более {max} фото. Нажмите «✅ Готово».",
        "en": "⚠️ Up to {max} photos. Tap «✅ Done».",
    },
    "listing.photo_added": {
        "uz": "✅ Rasm qo'shildi ({n}/{max})",
        "ru": "✅ Фото добавлено ({n}/{max})",
        "en": "✅ Photo added ({n}/{max})",
    },
    "listing.photos_required": {
        "uz": "⚠️ Kamida {n} ta rasm yuboring. Hozir: {k} ta",
        "ru": "⚠️ Отправьте минимум {n} фото. Сейчас: {k}",
        "en": "⚠️ Please send at least {n} photos. Now: {k}",
    },
    "listing.photos_invalid": {
        "uz": "📸 Rasm yuboring yoki «✅ Tayyor» tugmasini bosing.",
        "ru": "📸 Отправьте фото или нажмите «✅ Готово».",
        "en": "📸 Send a photo or tap «✅ Done».",
    },

    # ---- preview ----
    "listing.preview_title": {
        "uz": "👀 <b>E'loningiz shunday ko'rinadi:</b>",
        "ru": "👀 <b>Так будет выглядеть ваше объявление:</b>",
        "en": "👀 <b>This is how your listing will look:</b>",
    },
    "listing.badge_rent": {
        "uz": "🔑 Ijaraga beriladi",
        "ru": "🔑 Сдаётся в аренду",
        "en": "🔑 For rent",
    },
    "listing.badge_sale": {
        "uz": "💰 Sotiladi",
        "ru": "💰 Продаётся",
        "en": "💰 For sale",
    },
    "listing.rooms_n": {
        "uz": "{n} xonali",
        "ru": "{n}-комнатная",
        "en": "{n}-room",
    },
    "listing.on_map": {
        "uz": "🗺 Xaritada belgilangan ✅",
        "ru": "🗺 Отмечено на карте ✅",
        "en": "🗺 Marked on the map ✅",
    },
    "listing.area_value": {
        "uz": "📐 {area} m²",
        "ru": "📐 {area} м²",
        "en": "📐 {area} m²",
    },
    "listing.floor_value": {
        "uz": "🏢 {floor}-qavat",
        "ru": "🏢 {floor} этаж",
        "en": "🏢 Floor {floor}",
    },
    "listing.photos_count": {
        "uz": "📸 Rasmlar: <b>{n} ta</b>",
        "ru": "📸 Фото: <b>{n} шт.</b>",
        "en": "📸 Photos: <b>{n}</b>",
    },
    "listing.preview_hint": {
        "uz": "✅ Hammasi to'g'ri bo'lsa — <b>Tasdiqlash</b>\n✏️ Biror narsani o'zgartirish — <b>Tahrirlash</b>",
        "ru": "✅ Если всё верно — <b>Подтвердить</b>\n✏️ Чтобы что-то поменять — <b>Изменить</b>",
        "en": "✅ If everything is correct — <b>Confirm</b>\n✏️ To change something — <b>Edit</b>",
    },

    # ---- edit / cancel ----
    "listing.changed": {
        "uz": "✅ O'zgartirildi.",
        "ru": "✅ Изменено.",
        "en": "✅ Updated.",
    },
    "listing.change_cancelled": {
        "uz": "↩️ O'zgartirish bekor qilindi.",
        "ru": "↩️ Изменение отменено.",
        "en": "↩️ Change cancelled.",
    },
    "listing.cancelled": {
        "uz": "❌ E'lon qo'shish bekor qilindi.",
        "ru": "❌ Добавление объявления отменено.",
        "en": "❌ Adding the listing was cancelled.",
    },
    "listing.edit_menu": {
        "uz": "✏️ <b>Nimani o'zgartirmoqchisiz?</b>\n\nPastdagi tugmalardan birini tanlang 👇",
        "ru": "✏️ <b>Что вы хотите изменить?</b>\n\nВыберите кнопкой ниже 👇",
        "en": "✏️ <b>What would you like to change?</b>\n\nChoose one of the buttons below 👇",
    },
    "listing.edit_field_invalid": {
        "uz": "👇 O'zgartirmoqchi bo'lgan qismni tugmadan tanlang.",
        "ru": "👇 Выберите кнопкой, что хотите изменить.",
        "en": "👇 Choose what you want to change with a button.",
    },
    "listing.confirm_invalid": {
        "uz": "👇 Iltimos, tugmalardan birini tanlang: «✅ Tasdiqlash», «✏️ Tahrirlash» yoki «❌ Bekor qilish».",
        "ru": "👇 Пожалуйста, выберите кнопку: «✅ Подтвердить», «✏️ Изменить» или «❌ Отмена».",
        "en": "👇 Please choose a button: «✅ Confirm», «✏️ Edit» or «❌ Cancel».",
    },

    # ---- result ----
    "listing.success_type_rent": {
        "uz": "Ijaraga",
        "ru": "Аренда",
        "en": "For rent",
    },
    "listing.success_type_sale": {
        "uz": "Sotuvga",
        "ru": "Продажа",
        "en": "For sale",
    },
    "listing.success": {
        "uz": "🎉 <b>E'loningiz qabul qilindi!</b>\n\n"
              "🆔 E'lon raqami: <b>#{id}</b>\n"
              "🏠 {type} · {rooms}\n"
              "💵 {price}\n\n"
              "⏳ Admin tekshirgach, e'lon hammaga ko'rinadi.\n"
              "Holatini ilovadagi «📋 Mening e'lonlarim» bo'limida kuzating.",
        "ru": "🎉 <b>Ваше объявление принято!</b>\n\n"
              "🆔 Номер объявления: <b>#{id}</b>\n"
              "🏠 {type} · {rooms}\n"
              "💵 {price}\n\n"
              "⏳ После проверки администратором объявление увидят все.\n"
              "Следите за статусом в приложении, в разделе «📋 Мои объявления».",
        "en": "🎉 <b>Your listing has been received!</b>\n\n"
              "🆔 Listing number: <b>#{id}</b>\n"
              "🏠 {type} · {rooms}\n"
              "💵 {price}\n\n"
              "⏳ Once the admin checks it, everyone will see the listing.\n"
              "Track its status in the app under «📋 My listings».",
    },
    "listing.save_error": {
        "uz": "❌ E'lonni saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "ru": "❌ Не удалось сохранить объявление. Пожалуйста, попробуйте ещё раз.",
        "en": "❌ Something went wrong while saving the listing. Please try again.",
    },

    # ---- admin import: phone step ----
    "listing.import_ask_phone": {
        "uz": "📞 <b>Telefon raqami topilmadi.</b>\n\n"
              "E'lon uchun aloqa raqamini yozing (masalan, <code>+998901234567</code>) "
              "yoki pastdagi tugma bilan o'z raqamingizni tanlang:",
        "ru": "📞 <b>Номер телефона не найден.</b>\n\n"
              "Напишите контактный номер для объявления (например, <code>+998901234567</code>) "
              "или выберите свой номер кнопкой ниже:",
        "en": "📞 <b>No phone number found.</b>\n\n"
              "Type the contact number for the listing (for example <code>+998901234567</code>) "
              "or pick your own number with the button below:",
    },
    "listing.import_phone_invalid": {
        "uz": "⚠️ Raqam noto'g'ri. Masalan: +998901234567",
        "ru": "⚠️ Неверный номер. Например: +998901234567",
        "en": "⚠️ Invalid number. For example: +998901234567",
    },

    # ---- contact alert (plain text, show_alert) ----
    "listing.not_found": {
        "uz": "❌ E'lon topilmadi.",
        "ru": "❌ Объявление не найдено.",
        "en": "❌ Listing not found.",
    },
    "listing.contact_title": {
        "uz": "📞 Bog'lanish ma'lumotlari:",
        "ru": "📞 Контакты:",
        "en": "📞 Contact details:",
    },
    "listing.contact_phone": {
        "uz": "📱 Telefon: {phone}",
        "ru": "📱 Телефон: {phone}",
        "en": "📱 Phone: {phone}",
    },
    "listing.contact_name": {
        "uz": "👤 Ism: {name}",
        "ru": "👤 Имя: {name}",
        "en": "👤 Name: {name}",
    },
}

# Chip labels: listing.tag_rent_0 .. listing.tag_sale_7
for _kind, _by_lang in _TAGS.items():
    for _i in range(TAG_COUNT[_kind]):
        TEXTS[f"listing.tag_{_kind}_{_i}"] = {lang: labels[_i] for lang, labels in _by_lang.items()}
