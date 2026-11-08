"""User-facing texts: /start welcome, registration, main menu, settings/profile, guide, fallback, admin contact.

Placeholders in {braces} are filled by t(lang, key, **kwargs). Button labels are passed in
(e.g. cancel=t(lang, "btn.cancel")) so the text always names the button exactly as shown.
"""

TEXTS = {
    # ------------------------------------------------------------------ /start
    "start.greet_name": {
        "uz": "👋 Assalomu alaykum, <b>{name}</b>!",
        "ru": "👋 Здравствуйте, <b>{name}</b>!",
        "en": "👋 Hello, <b>{name}</b>!",
    },
    "start.greet": {
        "uz": "👋 Assalomu alaykum!",
        "ru": "👋 Здравствуйте!",
        "en": "👋 Hello!",
    },
    "start.about": {
        "uz": "🏠 <b>{brand}</b> — Chirchiq shahridagi kvartira e'lonlari.",
        "ru": "🏠 <b>{brand}</b> — объявления о квартирах в Чирчике.",
        "en": "🏠 <b>{brand}</b> — apartment listings in Chirchiq.",
    },
    "start.listings_count": {
        "uz": "📊 Hozir botda <b>{count} ta</b> faol e'lon bor.",
        "ru": "📊 Активных объявлений в боте сейчас: <b>{count}</b>.",
        "en": "📊 Active listings in the bot right now: <b>{count}</b>.",
    },
    "start.body_registered": {
        "uz": (
            "📱 <b>Ilovani ochish</b> — e'lonlarni ko'rish, filtrlash va egasi bilan bog'lanish.\n"
            "➕ <b>E'lon qo'shish</b> — kvartirangizni ijaraga bering yoki soting.\n\n"
            "📖 Qo'llanma: /help"
        ),
        "ru": (
            "📱 <b>Открыть приложение</b> — смотреть объявления, фильтровать и связываться с владельцем.\n"
            "➕ <b>Добавить объявление</b> — сдайте квартиру в аренду или продайте её.\n\n"
            "📖 Инструкция: /help"
        ),
        "en": (
            "📱 <b>Open app</b> — browse listings, filter them and contact the owner.\n"
            "➕ <b>Add listing</b> — rent out or sell your apartment.\n\n"
            "📖 Guide: /help"
        ),
    },
    "start.body_guest": {
        "uz": (
            "📱 <b>Ilovani ochish</b> — e'lonlarni ko'ring, filtrlang va egasi bilan bog'laning. "
            "Ro'yxatdan o'tish shart emas.\n"
            "📝 <b>Ro'yxatdan o'tish</b> — o'z e'loningizni joylash uchun (1 daqiqa).\n\n"
            "📖 Qo'llanma: /help"
        ),
        "ru": (
            "📱 <b>Открыть приложение</b> — смотрите объявления, фильтруйте и связывайтесь с владельцем. "
            "Регистрация не нужна.\n"
            "📝 <b>Регистрация</b> — чтобы разместить своё объявление (1 минута).\n\n"
            "📖 Инструкция: /help"
        ),
        "en": (
            "📱 <b>Open app</b> — browse listings, filter them and contact the owner. "
            "No registration needed.\n"
            "📝 <b>Register</b> — to post your own listing (takes 1 minute).\n\n"
            "📖 Guide: /help"
        ),
    },
    "start.open_app_hint": {
        "uz": "👇 E'lonlarni ilovada ko'ring:",
        "ru": "👇 Смотрите объявления в приложении:",
        "en": "👇 Browse the listings in the app:",
    },

    # ------------------------------------------------------------ Registration
    "reg.already": {
        "uz": (
            "✅ <b>Siz allaqachon ro'yxatdan o'tgansiz!</b>\n\n"
            "➕ E'lon joylash uchun «{add}» tugmasini bosing."
        ),
        "ru": (
            "✅ <b>Вы уже зарегистрированы!</b>\n\n"
            "➕ Чтобы разместить объявление, нажмите «{add}»."
        ),
        "en": (
            "✅ <b>You are already registered!</b>\n\n"
            "➕ To post a listing, tap «{add}»."
        ),
    },
    "reg.start": {
        "uz": (
            "📝 <b>Ro'yxatdan o'tish</b>\n"
            "Atigi 2 ta qisqa qadam — ism va telefon.\n\n"
            "👤 <b>1/2-qadam: Ism-familiya</b>\n\n"
            "Ism-familiyangizni yozing.\n\n"
            "✏️ Masalan: <i>Aliyev Jasur</i>\n\n"
            "❌ To'xtatish uchun «{cancel}» tugmasini bosing."
        ),
        "ru": (
            "📝 <b>Регистрация</b>\n"
            "Всего 2 коротких шага — имя и телефон.\n\n"
            "👤 <b>Шаг 1/2: Имя и фамилия</b>\n\n"
            "Напишите ваши имя и фамилию.\n\n"
            "✏️ Например: <i>Алиев Жасур</i>\n\n"
            "❌ Чтобы прервать, нажмите «{cancel}»."
        ),
        "en": (
            "📝 <b>Registration</b>\n"
            "Just 2 short steps — name and phone.\n\n"
            "👤 <b>Step 1/2: Full name</b>\n\n"
            "Type your first and last name.\n\n"
            "✏️ Example: <i>Jasur Aliyev</i>\n\n"
            "❌ To stop, tap «{cancel}»."
        ),
    },
    "reg.name_short": {
        "uz": (
            "⚠️ Ism-familiya juda qisqa.\n\n"
            "Iltimos, to'liq yozing (kamida 3 ta harf).\n"
            "✏️ Masalan: <i>Aliyev Jasur</i>"
        ),
        "ru": (
            "⚠️ Имя слишком короткое.\n\n"
            "Пожалуйста, напишите полностью (не менее 3 букв).\n"
            "✏️ Например: <i>Алиев Жасур</i>"
        ),
        "en": (
            "⚠️ The name is too short.\n\n"
            "Please type your full name (at least 3 letters).\n"
            "✏️ Example: <i>Jasur Aliyev</i>"
        ),
    },
    "reg.phone_prompt": {
        "uz": (
            "📱 <b>2/2-qadam: Telefon raqam</b>\n\n"
            "Pastdagi «{send_phone}» tugmasini bosing "
            "yoki raqamni qo'lda yozing.\n\n"
            "✏️ Masalan: <code>+998901234567</code>"
        ),
        "ru": (
            "📱 <b>Шаг 2/2: Номер телефона</b>\n\n"
            "Нажмите кнопку «{send_phone}» внизу "
            "или введите номер вручную.\n\n"
            "✏️ Например: <code>+998901234567</code>"
        ),
        "en": (
            "📱 <b>Step 2/2: Phone number</b>\n\n"
            "Tap the «{send_phone}» button below "
            "or type the number yourself.\n\n"
            "✏️ Example: <code>+998901234567</code>"
        ),
    },
    "reg.phone_contact_invalid": {
        "uz": (
            "⚠️ Bu raqamni qabul qilib bo'lmadi.\n\n"
            "Iltimos, O'zbekiston raqamini qo'lda yozing.\n"
            "✏️ Masalan: <code>+998901234567</code>"
        ),
        "ru": (
            "⚠️ Этот номер не подходит.\n\n"
            "Пожалуйста, введите узбекский номер вручную.\n"
            "✏️ Например: <code>+998901234567</code>"
        ),
        "en": (
            "⚠️ This number could not be accepted.\n\n"
            "Please type an Uzbekistan phone number yourself.\n"
            "✏️ Example: <code>+998901234567</code>"
        ),
    },
    "reg.phone_not_text": {
        "uz": (
            "⚠️ Iltimos, telefon raqamingizni matn ko'rinishida yozing "
            "yoki «{send_phone}» tugmasini bosing."
        ),
        "ru": (
            "⚠️ Пожалуйста, напишите номер телефона текстом "
            "или нажмите «{send_phone}»."
        ),
        "en": (
            "⚠️ Please type your phone number as text "
            "or tap «{send_phone}»."
        ),
    },
    "reg.phone_invalid": {
        "uz": (
            "⚠️ Telefon raqam formati noto'g'ri.\n\n"
            "To'g'ri formatlar:\n"
            "• <code>+998901234567</code>\n"
            "• <code>998901234567</code>\n\n"
            "🔁 Qaytadan yozing yoki «{send_phone}» tugmasini bosing."
        ),
        "ru": (
            "⚠️ Неверный формат номера.\n\n"
            "Правильные форматы:\n"
            "• <code>+998901234567</code>\n"
            "• <code>998901234567</code>\n\n"
            "🔁 Введите ещё раз или нажмите «{send_phone}»."
        ),
        "en": (
            "⚠️ Wrong phone number format.\n\n"
            "Correct formats:\n"
            "• <code>+998901234567</code>\n"
            "• <code>998901234567</code>\n\n"
            "🔁 Type it again or tap «{send_phone}»."
        ),
    },
    "reg.success": {
        "uz": (
            "🎉 <b>Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!</b>\n\n"
            "👤 Ism: <b>{name}</b>\n"
            "📱 Telefon: <b>{phone}</b>\n\n"
            "Endi sizga barcha imkoniyatlar ochiq:\n"
            "• <b>E'lon qo'shish</b> — kvartirangizni ijaraga bering yoki soting\n"
            "• <b>Ilovani ochish</b> — e'lonlarni ko'ring, o'z e'lonlaringiz holatini kuzating\n\n"
            "📖 Qo'llanma: /help"
        ),
        "ru": (
            "🎉 <b>Регистрация успешно завершена!</b>\n\n"
            "👤 Имя: <b>{name}</b>\n"
            "📱 Телефон: <b>{phone}</b>\n\n"
            "Теперь вам доступны все возможности:\n"
            "• <b>Добавить объявление</b> — сдайте квартиру в аренду или продайте её\n"
            "• <b>Открыть приложение</b> — смотрите объявления и следите за статусом своих\n\n"
            "📖 Инструкция: /help"
        ),
        "en": (
            "🎉 <b>Registration complete!</b>\n\n"
            "👤 Name: <b>{name}</b>\n"
            "📱 Phone: <b>{phone}</b>\n\n"
            "Everything is open to you now:\n"
            "• <b>Add listing</b> — rent out or sell your apartment\n"
            "• <b>Open app</b> — browse listings and track the status of your own\n\n"
            "📖 Guide: /help"
        ),
    },
    "reg.cancelled": {
        "uz": (
            "❌ <b>Ro'yxatdan o'tish bekor qilindi.</b>\n\n"
            "🔄 Qaytadan boshlash uchun /start buyrug'ini yuboring."
        ),
        "ru": (
            "❌ <b>Регистрация отменена.</b>\n\n"
            "🔄 Чтобы начать заново, отправьте команду /start."
        ),
        "en": (
            "❌ <b>Registration cancelled.</b>\n\n"
            "🔄 To start again, send /start."
        ),
    },
    "reg.error": {
        "uz": (
            "😔 <b>Ro'yxatdan o'tishda xatolik yuz berdi.</b>\n\n"
            "Iltimos, birozdan so'ng qaytadan urinib ko'ring — /start buyrug'ini yuboring."
        ),
        "ru": (
            "😔 <b>При регистрации произошла ошибка.</b>\n\n"
            "Пожалуйста, попробуйте ещё раз чуть позже — отправьте команду /start."
        ),
        "en": (
            "😔 <b>Something went wrong during registration.</b>\n\n"
            "Please try again in a moment — send /start."
        ),
    },

    # --------------------------------------------------------- Main menu (app)
    "menu.app_unavailable": {
        "uz": "⏳ Ilova hozircha ishlamayapti. Birozdan so'ng urinib ko'ring.",
        "ru": "⏳ Приложение сейчас недоступно. Попробуйте чуть позже.",
        "en": "⏳ The app is not available right now. Please try again later.",
    },
    "menu.app_text": {
        "uz": (
            "📱 <b>{brand} ilovasi</b>\n\n"
            "E'lonlarni ko'rish, filtrlash, egasi bilan bog'lanish va o'z e'lonlaringiz — "
            "hammasi shu yerda 👇"
        ),
        "ru": (
            "📱 <b>Приложение {brand}</b>\n\n"
            "Просмотр объявлений, фильтры, связь с владельцем и ваши объявления — "
            "всё здесь 👇"
        ),
        "en": (
            "📱 <b>{brand} app</b>\n\n"
            "Browse and filter listings, contact owners and manage your own listings — "
            "all in one place 👇"
        ),
    },

    # ---------------------------------------------------------------- Settings
    "settings.register_first": {
        "uz": (
            "🔒 <b>Sozlamalarni ko'rish uchun avval ro'yxatdan o'ting.</b>\n\n"
            "📝 Buning uchun «{register}» tugmasini bosing — bu 1 daqiqa vaqt oladi."
        ),
        "ru": (
            "🔒 <b>Чтобы открыть настройки, сначала зарегистрируйтесь.</b>\n\n"
            "📝 Для этого нажмите «{register}» — это займёт 1 минуту."
        ),
        "en": (
            "🔒 <b>Please register first to see the settings.</b>\n\n"
            "📝 Tap «{register}» — it takes 1 minute."
        ),
    },
    "settings.edit_contact": {
        "uz": "✏️ Ma'lumotlarni o'zgartirish uchun {admin}.",
        "ru": "✏️ Чтобы изменить данные, {admin}.",
        "en": "✏️ To change your details, {admin}.",
    },
    # Profile card (app/utils/formatters.format_user_info)
    "settings.profile_title": {
        "uz": "<b>👤 Mening profilim</b>",
        "ru": "<b>👤 Мой профиль</b>",
        "en": "<b>👤 My profile</b>",
    },
    "settings.profile_name": {
        "uz": "🙍 Ism: <b>{value}</b>",
        "ru": "🙍 Имя: <b>{value}</b>",
        "en": "🙍 Name: <b>{value}</b>",
    },
    "settings.profile_username": {
        "uz": "🔗 Username: @{value}",
        "ru": "🔗 Username: @{value}",
        "en": "🔗 Username: @{value}",
    },
    "settings.profile_phone": {
        "uz": "📞 Telefon: <b>{value}</b>",
        "ru": "📞 Телефон: <b>{value}</b>",
        "en": "📞 Phone: <b>{value}</b>",
    },
    "settings.profile_address": {
        "uz": "📍 Manzil: {value}",
        "ru": "📍 Адрес: {value}",
        "en": "📍 Address: {value}",
    },
    "settings.profile_id": {
        "uz": "🆔 Telegram ID: <code>{value}</code>",
        "ru": "🆔 Telegram ID: <code>{value}</code>",
        "en": "🆔 Telegram ID: <code>{value}</code>",
    },
    "settings.profile_status": {
        "uz": "📊 Holat: <b>{value}</b>",
        "ru": "📊 Статус: <b>{value}</b>",
        "en": "📊 Status: <b>{value}</b>",
    },
    "settings.status_blocked": {
        "uz": "🚫 Bloklangan",
        "ru": "🚫 Заблокирован",
        "en": "🚫 Blocked",
    },
    "settings.status_active": {
        "uz": "✅ Faol",
        "ru": "✅ Активен",
        "en": "✅ Active",
    },
    "settings.status_inactive": {
        "uz": "⏸ Nofaol",
        "ru": "⏸ Неактивен",
        "en": "⏸ Inactive",
    },
    "settings.profile_admin": {
        "uz": "🔐 Rol: <b>Administrator</b>",
        "ru": "🔐 Роль: <b>Администратор</b>",
        "en": "🔐 Role: <b>Administrator</b>",
    },
    "settings.profile_registered": {
        "uz": "📅 Ro'yxatdan o'tgan: {value}",
        "ru": "📅 Дата регистрации: {value}",
        "en": "📅 Registered: {value}",
    },
    "settings.profile_last_activity": {
        "uz": "⏰ Oxirgi faollik: {value}",
        "ru": "⏰ Последняя активность: {value}",
        "en": "⏰ Last activity: {value}",
    },

    # ------------------------------------------------------- Admin contact phrase
    # app/utils/contact.py; {link} = '<a href="https://t.me/name">@name</a>'
    "contact.admin_word": {
        "uz": "admin",
        "ru": "администратор",
        "en": "admin",
    },
    "contact.admin": {
        "uz": "admin bilan bog'laning",
        "ru": "свяжитесь с администратором",
        "en": "contact the admin",
    },
    "contact.admin_with_link": {
        "uz": "admin bilan bog'laning: {link}",
        "ru": "свяжитесь с администратором: {link}",
        "en": "contact the admin: {link}",
    },

    # -------------------------------------------------------------------- Guide
    "guide.menu_text": {
        "uz": (
            "📖 <b>{brand} — qo'llanma</b>\n\n"
            "E'lonlarni ko'rish va egasi bilan bog'lanish — ilovada, "
            "e'lon joylash — shu yerda, botda.\n\n"
            "👇 Qaysi bo'lim haqida bilmoqchisiz? Tugmani bosing."
        ),
        "ru": (
            "📖 <b>{brand} — инструкция</b>\n\n"
            "Смотреть объявления и связываться с владельцем — в приложении, "
            "размещать объявления — здесь, в боте.\n\n"
            "👇 О каком разделе хотите узнать? Нажмите кнопку."
        ),
        "en": (
            "📖 <b>{brand} — guide</b>\n\n"
            "Browsing listings and contacting owners happens in the app; "
            "posting a listing happens here, in the bot.\n\n"
            "👇 Which section would you like to read? Tap a button."
        ),
    },
    "guide.btn_app": {
        "uz": "📱 Ilova: e'lonlarni ko'rish",
        "ru": "📱 Приложение: просмотр объявлений",
        "en": "📱 App: browsing listings",
    },
    "guide.app": {
        "uz": (
            "📱 <b>E'lonlar qayerda ko'riladi?</b>\n\n"
            "Barcha e'lonlar ilovada. Uni ochish uchun:\n"
            "• pastdagi «{open_app}» tugmasini bosing, yoki\n"
            "• yozuv maydoni yonidagi «{app_menu}» tugmasini bosing.\n\n"
            "Ilovada:\n"
            "🏠 <b>E'lonlar</b> — rasmli kartalar. Yuqorida «Hammasi / Ijaraga / Sotuv», "
            "«Filtr» orqali xonalar soni, narx va saralashni tanlaysiz.\n"
            "🖼 Kartani bossangiz — rasmlar galereyasi va to'liq ma'lumot.\n"
            "📞 <b>Bog'lanish</b> — e'lon egasining telefon raqami chiqadi, "
            "bir bosishda qo'ng'iroq qilasiz.\n"
            "📋 <b>Mening e'lonlarim</b> — o'z e'lonlaringiz va ularning holati.\n\n"
            "💡 E'lonlarni ko'rish uchun ro'yxatdan o'tish shart emas."
        ),
        "ru": (
            "📱 <b>Где смотреть объявления?</b>\n\n"
            "Все объявления — в приложении. Чтобы открыть его:\n"
            "• нажмите кнопку «{open_app}» внизу, или\n"
            "• нажмите кнопку «{app_menu}» рядом с полем ввода.\n\n"
            "В приложении:\n"
            "🏠 <b>Объявления</b> — карточки с фото. Вверху «Все / Аренда / Продажа», "
            "через «Фильтр» выбираете число комнат, цену и сортировку.\n"
            "🖼 Нажмите на карточку — откроются галерея фото и полная информация.\n"
            "📞 <b>Связаться</b> — появится номер владельца, "
            "позвонить можно одним нажатием.\n"
            "📋 <b>Мои объявления</b> — ваши объявления и их статус.\n\n"
            "💡 Чтобы смотреть объявления, регистрация не нужна."
        ),
        "en": (
            "📱 <b>Where can I see the listings?</b>\n\n"
            "All listings are in the app. To open it:\n"
            "• tap the «{open_app}» button below, or\n"
            "• tap the «{app_menu}» button next to the message field.\n\n"
            "In the app:\n"
            "🏠 <b>Listings</b> — cards with photos. At the top: «All / Rent / Sale»; "
            "use «Filter» to choose the number of rooms, price and sorting.\n"
            "🖼 Tap a card to see the photo gallery and full details.\n"
            "📞 <b>Contact</b> — shows the owner's phone number, "
            "call with one tap.\n"
            "📋 <b>My listings</b> — your own listings and their status.\n\n"
            "💡 You don't need to register to browse listings."
        ),
    },
    "guide.btn_add": {
        "uz": "➕ E'lon qo'shish",
        "ru": "➕ Добавить объявление",
        "en": "➕ Add a listing",
    },
    "guide.add": {
        "uz": (
            "➕ <b>E'lon qanday qo'shiladi?</b>\n\n"
            "📝 Avval ro'yxatdan o'ting (bir marta, 1 daqiqa).\n\n"
            "1️⃣ «➕ E'lon qo'shish» tugmasini bosing.\n"
            "2️⃣ Turini tanlang: «🔑 Ijaraga berish» yoki «💰 Sotish».\n"
            "3️⃣ Xonalar sonini tanlang (1 dan 6+ gacha).\n"
            "4️⃣ Hududni tanlang (masalan, «8-mikrorayon»), so'ng ko'cha va uy raqamini yozing, keyin joylashuvni yuboring (ixtiyoriy).\n"
            "5️⃣ Narx — tayyor tugmani bosing yoki qisqa yozing: <i>3 mln</i>, <i>800 ming</i>, <i>$45 000</i>.\n"
            "6️⃣ Maydon va qavat — tugmalardan tanlang (yoki «⏩ O'tkazib yuborish»).\n"
            "7️⃣ Qo'shimcha: «Remont qilingan», «Mebelli» kabi belgilarni bosing, "
            "xohlasangiz o'zingiz ham yozing, so'ng «✅ Tayyor».\n"
            "8️⃣ Kvartira rasmlarini yuboring (kamida 3 ta, ko'pi bilan {photos} ta), "
            "so'ng «✅ Tayyor» tugmasini bosing.\n"
            "9️⃣ E'lonni tekshiring: hammasi to'g'ri bo'lsa «✅ Tasdiqlash», "
            "o'zgartirish uchun «✏️ Tahrirlash».\n\n"
            "⏳ E'lon admin tasdiqlagandan keyin ilovada hammaga ko'rinadi.\n"
            "❌ Istalgan qadamda «❌ Bekor qilish» tugmasi bilan to'xtatishingiz mumkin."
        ),
        "ru": (
            "➕ <b>Как добавить объявление?</b>\n\n"
            "📝 Сначала зарегистрируйтесь (один раз, 1 минута).\n\n"
            "1️⃣ Нажмите «➕ Добавить объявление».\n"
            "2️⃣ Выберите тип: «🔑 Сдать в аренду» или «💰 Продать».\n"
            "3️⃣ Выберите количество комнат (от 1 до 6+).\n"
            "4️⃣ Выберите район (например, «8-микрорайон»), затем напишите улицу и номер дома, потом отправьте локацию (по желанию).\n"
            "5️⃣ Цена — нажмите готовую кнопку или напишите коротко: <i>3 млн</i>, <i>800 тыс</i>, <i>$45 000</i>.\n"
            "6️⃣ Площадь и этаж — выберите на кнопках (или «⏩ Пропустить»).\n"
            "7️⃣ Дополнительно: отметьте «С ремонтом», «С мебелью» и т. п., "
            "при желании допишите своё, затем «✅ Готово».\n"
            "8️⃣ Отправьте фото квартиры (минимум 3, максимум {photos}), "
            "затем нажмите «✅ Готово».\n"
            "9️⃣ Проверьте объявление: если всё верно — «✅ Подтвердить», "
            "чтобы исправить — «✏️ Изменить».\n\n"
            "⏳ После одобрения администратором объявление увидят все в приложении.\n"
            "❌ На любом шаге можно прервать кнопкой «❌ Отмена»."
        ),
        "en": (
            "➕ <b>How do I add a listing?</b>\n\n"
            "📝 Register first (once, takes 1 minute).\n\n"
            "1️⃣ Tap «➕ Add listing».\n"
            "2️⃣ Choose the type: «🔑 Rent out» or «💰 Sell».\n"
            "3️⃣ Choose the number of rooms (1 to 6+).\n"
            "4️⃣ Choose the area (e.g. «Microdistrict 8»), then type the street and house number, then send the location (optional).\n"
            "5️⃣ Price — tap a ready button or type it briefly: <i>3 mln</i>, <i>800k</i>, <i>$45 000</i>.\n"
            "6️⃣ Area and floor — pick from the buttons (or «⏩ Skip»).\n"
            "7️⃣ Extras: tap tags like «Renovated» or «Furnished», "
            "add your own text if you like, then «✅ Done».\n"
            "8️⃣ Send photos of the apartment (at least 3, at most {photos}), "
            "then tap «✅ Done».\n"
            "9️⃣ Check the listing: if everything is right — «✅ Confirm», "
            "to change something — «✏️ Edit».\n\n"
            "⏳ Once the admin approves it, everyone can see the listing in the app.\n"
            "❌ You can stop at any step with «❌ Cancel»."
        ),
    },
    "guide.btn_mine": {
        "uz": "📋 Mening e'lonlarim",
        "ru": "📋 Мои объявления",
        "en": "📋 My listings",
    },
    "guide.mine": {
        "uz": (
            "📋 <b>O'z e'lonlarimni qayerda ko'raman?</b>\n\n"
            "Ilovani oching va pastdagi «📋 Mening e'lonlarim» bo'limiga o'ting — "
            "siz qo'shgan barcha e'lonlar holati bilan chiqadi:\n\n"
            "🟡 <b>Tekshiruvda</b> — admin hali tekshiryapti\n"
            "🟢 <b>Faol</b> — tasdiqlangan, hamma ko'ra oladi\n"
            "🔴 <b>Rad etilgan</b> — admin tasdiqlamadi\n"
            "⚪️ <b>Arxivda</b> — arxivga olingan, endi ko'rinmaydi\n\n"
            "🗑 Keraksiz e'lonni o'sha yerda o'chirishingiz mumkin.\n"
            "💡 E'lon rad etilsa, ma'lumotlarni to'g'rilab yangi e'lon qo'shing."
        ),
        "ru": (
            "📋 <b>Где посмотреть свои объявления?</b>\n\n"
            "Откройте приложение и перейдите в раздел «📋 Мои объявления» внизу — "
            "там все ваши объявления со статусом:\n\n"
            "🟡 <b>На проверке</b> — администратор ещё проверяет\n"
            "🟢 <b>Активно</b> — одобрено, видно всем\n"
            "🔴 <b>Отклонено</b> — администратор не одобрил\n"
            "⚪️ <b>В архиве</b> — перенесено в архив, больше не показывается\n\n"
            "🗑 Ненужное объявление можно удалить там же.\n"
            "💡 Если объявление отклонено, исправьте данные и добавьте новое."
        ),
        "en": (
            "📋 <b>Where can I see my listings?</b>\n\n"
            "Open the app and go to the «📋 My listings» tab at the bottom — "
            "all the listings you added are shown with their status:\n\n"
            "🟡 <b>Under review</b> — the admin is still checking it\n"
            "🟢 <b>Active</b> — approved, everyone can see it\n"
            "🔴 <b>Rejected</b> — the admin did not approve it\n"
            "⚪️ <b>Archived</b> — moved to the archive, no longer shown\n\n"
            "🗑 You can delete a listing you no longer need right there.\n"
            "💡 If a listing is rejected, fix the details and add a new one."
        ),
    },
    "guide.btn_help": {
        "uz": "❓ Yordam",
        "ru": "❓ Помощь",
        "en": "❓ Help",
    },
    "guide.help": {
        "uz": (
            "❓ <b>Yordam</b>\n\n"
            "• Ism yoki telefonni o'zgartirish uchun {admin}.\n"
            "• Ilova ochilmasa yoki bot javob bermay qolsa, /start buyrug'ini yuboring.\n"
            "• Bu qo'llanmani istalgan payt «{settings}» tugmasi "
            "yoki /help buyrug'i orqali ochishingiz mumkin.\n"
            "• Tilni o'zgartirish: /language"
        ),
        "ru": (
            "❓ <b>Помощь</b>\n\n"
            "• Чтобы изменить имя или телефон, {admin}.\n"
            "• Если приложение не открывается или бот не отвечает, отправьте команду /start.\n"
            "• Эту инструкцию можно открыть в любое время кнопкой «{settings}» "
            "или командой /help.\n"
            "• Сменить язык: /language"
        ),
        "en": (
            "❓ <b>Help</b>\n\n"
            "• To change your name or phone, {admin}.\n"
            "• If the app does not open or the bot stops responding, send /start.\n"
            "• You can open this guide any time with the «{settings}» button "
            "or the /help command.\n"
            "• Change language: /language"
        ),
    },

    # ----------------------------------------------------------------- Fallback
    "fallback.unknown": {
        "uz": (
            "🤔 Kechirasiz, bu xabarni tushunmadim.\n\n"
            "Iltimos, pastdagi <b>tugmalardan foydalaning</b> 👇\n"
            "Qo'llanma: /help"
        ),
        "ru": (
            "🤔 Извините, я не понял это сообщение.\n\n"
            "Пожалуйста, <b>пользуйтесь кнопками</b> внизу 👇\n"
            "Инструкция: /help"
        ),
        "en": (
            "🤔 Sorry, I didn't understand that message.\n\n"
            "Please <b>use the buttons</b> below 👇\n"
            "Guide: /help"
        ),
    },
    "fallback.stale_button": {
        "uz": "Bu tugma eskirgan. E'lonlar endi ilovada — «{open_app}» tugmasini bosing.",
        "ru": "Эта кнопка устарела. Объявления теперь в приложении — нажмите «{open_app}».",
        "en": "This button is out of date. Listings are in the app now — tap «{open_app}».",
    },
}
