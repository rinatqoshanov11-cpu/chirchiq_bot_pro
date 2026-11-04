/* Chirchiq Kvartira — public landing page
   Plain JS, no dependencies. All DOM for API data is built with
   createElement/textContent — no HTML-string injection. */
(function () {
  "use strict";

  var API = "https://chirchiq-bot-pro.onrender.com";
  var BOT_URL = "https://t.me/Chirchiq_Arenda_bot?start=site";
  var LANGS = ["uz", "ru", "en"];
  var LANG_KEY = "ck_lang";
  var THEME_KEY = "ck_theme";
  var FETCH_TIMEOUT = 70000; // Render free tier can take ~60 s to wake up

  /* ------------------------------------------------------------------ */
  /* Translations                                                        */
  /* ------------------------------------------------------------------ */

  var I18N = {
    uz: {
      "meta.title": "Chirchiq Kvartira — Chirchiqda kvartira ijarasi va sotuvi | Telegram bot",
      "meta.description": "Chirchiq shahrida kvartira ijarasi va sotuvi e'lonlari — Telegram bot va mini ilova. E'lon berish bepul, har bir e'lon admin tomonidan tekshiriladi.",
      "meta.ogTitle": "Chirchiq Kvartira — Chirchiqda kvartira ijarasi va sotuvi",
      "meta.ogDescription": "Telegram bot va mini ilova: ijara va sotuv e'lonlari, bepul e'lon berish, admin tekshiruvi.",
      "skip": "Asosiy qismga o'tish",
      "home.aria": "Chirchiq Kvartira — bosh sahifa",
      "nav.label": "Asosiy menyu",
      "nav.menu": "Menyu",
      "nav.features": "Imkoniyatlar",
      "nav.how": "Qanday ishlaydi",
      "nav.listings": "E'lonlar",
      "nav.faq": "Savollar",
      "nav.openBot": "Botni ochish",
      "lang.label": "Tilni tanlash",
      "theme.toggle": "Tungi rejimni yoqish yoki o'chirish",
      "hero.eyebrow": "Telegram bot + ilova",
      "hero.h1a": "Chirchiqda kvartira —",
      "hero.h1b": "bir necha bosishda",
      "hero.sub": "Ijara va sotuv e'lonlari bir joyda. E'lon berish bepul, har bir e'lon admin tomonidan tekshiriladi.",
      "hero.cta": "Botni ochish",
      "hero.how": "Qanday ishlaydi",
      "hero.factsLabel": "Faktlar",
      "hero.fact1": "Bepul",
      "hero.fact2": "3 til",
      "hero.fact3": "Chirchiqning 18 ta hududi",
      "hero.live1": "Hozir {n} ta faol e'lon",
      "hero.live2": "Hozir {n} ta faol e'lon",
      "hero.live5": "Hozir {n} ta faol e'lon",
      "mock.aria": "Mini ilova katalogining ko'rinishi",
      "mock.title": "Chirchiq Kvartira",
      "mock.all": "Hammasi",
      "mock.rent": "Ijaraga",
      "mock.sale": "Sotuv",
      "mock.filter": "Filtr",
      "mock.tabCatalog": "E'lonlar",
      "mock.tabMy": "Mening e'lonlarim",
      "features.kicker": "Imkoniyatlar",
      "features.title": "Kerak bo'lgan hamma narsa — Telegram ichida",
      "features.sub": "Alohida ilova o'rnatish shart emas: bot ham, mini ilova ham to'g'ridan-to'g'ri Telegramda ochiladi.",
      "features.1.title": "Rasmli mini ilova",
      "features.1.text": "E'lonlar rasm va galereya bilan. Ijara yoki sotuv, xonalar soni va narx bo'yicha filtr.",
      "features.2.title": "Uy egasi bilan — bir bosishda",
      "features.2.text": "«Bog'lanish» tugmasi — telefon raqami darhol ochiladi. Vositachisiz.",
      "features.3.title": "Bepul e'lon berish",
      "features.3.text": "Hudud, narx («3 mln»), maydon, qavat, belgilar — deyarli hammasi tugma bilan, bir necha daqiqada.",
      "features.4.title": "Xaritada joylashuv",
      "features.4.text": "Har bir e'longa joylashuv nuqtasi qo'shiladi — uy qayerdaligini xaritada ko'ring.",
      "features.5.title": "Admin tekshiruvi",
      "features.5.text": "Har bir e'lon chop etilishidan oldin admin tomonidan ko'rib chiqiladi.",
      "features.6.title": "Uch til",
      "features.6.text": "O'zbek, rus va ingliz tillari — bot ham, ilova ham.",
      "how.kicker": "Qanday ishlaydi",
      "how.title": "Uch qadam — ikki yo'nalish",
      "how.sub": "Kvartira qidiryapsizmi yoki e'lon bermoqchimisiz — hammasi botda, bir necha daqiqada.",
      "how.a.title": "Kvartira qidiryapman",
      "how.a.1t": "Botni oching",
      "how.a.1d": "@Chirchiq_Arenda_bot ga kiring va «Start» tugmasini bosing.",
      "how.a.2t": "Ilovani oching",
      "how.a.2d": "«Ilovani ochish» tugmasi — rasmli katalog ochiladi.",
      "how.a.3t": "Filtrlang va bog'laning",
      "how.a.3d": "Ijara yoki sotuv, xonalar, narx. Yoqdimi — «Bog'lanish», raqam ochiladi.",
      "how.b.title": "E'lon bermoqchiman",
      "how.b.1t": "Ro'yxatdan o'ting",
      "how.b.1d": "Ism va telefon raqami — bir marta, bir daqiqa.",
      "how.b.2t": "Tugmalar bilan javob bering",
      "how.b.2d": "Hudud, narx, maydon, qavat, rasmlar — bot bosqichma-bosqich so'raydi.",
      "how.b.3t": "Admin tasdiqlaydi",
      "how.b.3d": "Tekshiruvdan so'ng e'lon katalogda paydo bo'ladi.",
      "listings.kicker": "Jonli",
      "listings.title": "So'nggi e'lonlar",
      "listings.sub": "Botdagi faol e'lonlar — to'g'ridan-to'g'ri bazadan.",
      "listings.loading": "E'lonlar yuklanmoqda…",
      "listings.loadingHint": "Serverga birinchi so'rov bir daqiqagacha cho'zilishi mumkin.",
      "listings.failTitle": "E'lonlarni hozir yuklab bo'lmadi",
      "listings.failText": "Ularni botda ko'ring — katalog har doim ochiq.",
      "listings.empty": "Hozircha faol e'lonlar yo'q — birinchi bo'lib joylashtiring!",
      "listings.openBot": "Botda ochish",
      "listings.all": "Barcha e'lonlar — botda",
      "listings.photoAlt": "E'lon rasmi",
      "unit.room1": "1 xonali",
      "unit.rooms": "{n} xonali",
      "unit.area": "{n} m²",
      "unit.floor": "{f}/{t}-qavat",
      "unit.floorOnly": "{f}-qavat",
      "areas.kicker": "Hududlar",
      "areas.title": "Chirchiqning qaysi hududlarida?",
      "areas.sub": "E'lon berishda hudud tugma bilan tanlanadi — 18 ta hudud.",
      "faq.kicker": "Savol-javob",
      "faq.title": "Ko'p so'raladigan savollar",
      "faq.1.q": "Bu bepulmi?",
      "faq.1.a": "Ha. E'lonlarni ko'rish ham, e'lon joylashtirish ham bepul.",
      "faq.2.q": "Ko'rish uchun ro'yxatdan o'tish kerakmi?",
      "faq.2.a": "Yo'q. Katalog hamma uchun ochiq. Ro'yxatdan o'tish (ism va telefon) faqat e'lon berish uchun kerak.",
      "faq.3.q": "E'lonlarni kim tekshiradi?",
      "faq.3.a": "Admin. Har bir e'lon chop etilishidan oldin ko'rib chiqiladi.",
      "faq.4.q": "Uy egasi bilan qanday bog'lanaman?",
      "faq.4.a": "Ilovada e'lonni oching va «Bog'lanish» tugmasini bosing — telefon raqami ko'rsatiladi.",
      "faq.5.q": "Tilni qanday o'zgartiraman?",
      "faq.5.a": "Botda /language buyrug'i yoki «Sozlamalar» orqali. Ilova bot tilida ochiladi.",
      "faq.6.q": "O'z e'lonimni qanday o'chiraman?",
      "faq.6.a": "Ilovada «Mening e'lonlarim» bo'limini oching va e'lonni o'chiring.",
      "cta.title": "Hoziroq boshlang",
      "cta.text": "Kvartira toping yoki e'loningizni bepul joylashtiring — hammasi Telegramda.",
      "cta.btn": "Botni ochish",
      "cta.github": "GitHub'da kod",
      "footer.logoAlt": "Chirchiq Kvartira logotipi",
      "footer.tagline": "Chirchiq shahridagi kvartira ijarasi va sotuvi uchun Telegram bot va mini ilova.",
      "footer.links": "Havolalar",
      "footer.bot": "Telegram bot",
      "footer.github": "GitHub",
      "footer.copy": "© 2026 Chirchiq Kvartira",
      "footer.open": "Ochiq kodli loyiha"
    },

    ru: {
      "meta.title": "Chirchiq Kvartira — аренда и продажа квартир в Чирчике | Telegram-бот",
      "meta.description": "Объявления об аренде и продаже квартир в Чирчике — Telegram-бот и мини-приложение. Размещение бесплатно, каждое объявление проверяет админ.",
      "meta.ogTitle": "Chirchiq Kvartira — аренда и продажа квартир в Чирчике",
      "meta.ogDescription": "Telegram-бот и мини-приложение: аренда и продажа, бесплатное размещение, проверка админом.",
      "skip": "Перейти к содержимому",
      "home.aria": "Chirchiq Kvartira — главная",
      "nav.label": "Главное меню",
      "nav.menu": "Меню",
      "nav.features": "Возможности",
      "nav.how": "Как это работает",
      "nav.listings": "Объявления",
      "nav.faq": "Вопросы",
      "nav.openBot": "Открыть бота",
      "lang.label": "Выбор языка",
      "theme.toggle": "Переключить тему",
      "hero.eyebrow": "Telegram-бот + приложение",
      "hero.h1a": "Квартира в Чирчике —",
      "hero.h1b": "в пару нажатий",
      "hero.sub": "Аренда и продажа в одном месте. Размещение бесплатно, каждое объявление проверяет админ.",
      "hero.cta": "Открыть бота",
      "hero.how": "Как это работает",
      "hero.factsLabel": "Факты",
      "hero.fact1": "Бесплатно",
      "hero.fact2": "3 языка",
      "hero.fact3": "18 районов Чирчика",
      "hero.live1": "Сейчас {n} активное объявление",
      "hero.live2": "Сейчас {n} активных объявления",
      "hero.live5": "Сейчас {n} активных объявлений",
      "mock.aria": "Так выглядит каталог мини-приложения",
      "mock.title": "Chirchiq Kvartira",
      "mock.all": "Все",
      "mock.rent": "Аренда",
      "mock.sale": "Продажа",
      "mock.filter": "Фильтр",
      "mock.tabCatalog": "Объявления",
      "mock.tabMy": "Мои объявления",
      "features.kicker": "Возможности",
      "features.title": "Всё нужное — внутри Telegram",
      "features.sub": "Ничего не нужно устанавливать: и бот, и мини-приложение открываются прямо в Telegram.",
      "features.1.title": "Мини-приложение с фото",
      "features.1.text": "Объявления с фото и галереей. Фильтр по типу (аренда / продажа), комнатам и цене.",
      "features.2.title": "Связь с хозяином в одно нажатие",
      "features.2.text": "Кнопка «Связаться» сразу показывает номер телефона. Без посредников.",
      "features.3.title": "Бесплатное размещение",
      "features.3.text": "Район, цена («3 млн»), площадь, этаж, особенности — почти всё кнопками, за несколько минут.",
      "features.4.title": "Расположение на карте",
      "features.4.text": "К каждому объявлению добавляется точка на карте — видно, где находится дом.",
      "features.5.title": "Проверка админом",
      "features.5.text": "Каждое объявление просматривается админом перед публикацией.",
      "features.6.title": "Три языка",
      "features.6.text": "Узбекский, русский и английский — и в боте, и в приложении.",
      "how.kicker": "Как это работает",
      "how.title": "Три шага — два сценария",
      "how.sub": "Ищете квартиру или хотите разместить объявление — всё в боте, за несколько минут.",
      "how.a.title": "Ищу квартиру",
      "how.a.1t": "Откройте бота",
      "how.a.1d": "Зайдите в @Chirchiq_Arenda_bot и нажмите «Start».",
      "how.a.2t": "Откройте приложение",
      "how.a.2d": "Кнопка «Открыть приложение» — откроется каталог с фото.",
      "how.a.3t": "Фильтруйте и связывайтесь",
      "how.a.3d": "Аренда или продажа, комнаты, цена. Понравилось — нажмите «Связаться», и номер на экране.",
      "how.b.title": "Хочу разместить объявление",
      "how.b.1t": "Зарегистрируйтесь",
      "how.b.1d": "Имя и номер телефона — один раз, одна минута.",
      "how.b.2t": "Отвечайте кнопками",
      "how.b.2d": "Район, цена, площадь, этаж, фото — бот спрашивает шаг за шагом.",
      "how.b.3t": "Админ подтверждает",
      "how.b.3d": "После проверки объявление появляется в каталоге.",
      "listings.kicker": "Онлайн",
      "listings.title": "Последние объявления",
      "listings.sub": "Активные объявления из бота — напрямую из базы.",
      "listings.loading": "Загружаем объявления…",
      "listings.loadingHint": "Первый запрос к серверу может занять до минуты.",
      "listings.failTitle": "Не удалось загрузить объявления",
      "listings.failText": "Посмотрите их в боте — каталог всегда открыт.",
      "listings.empty": "Активных объявлений пока нет — разместите первое!",
      "listings.openBot": "Открыть в боте",
      "listings.all": "Все объявления — в боте",
      "listings.photoAlt": "Фото объявления",
      "unit.room1": "1-комн.",
      "unit.rooms": "{n}-комн.",
      "unit.area": "{n} м²",
      "unit.floor": "{f}/{t} этаж",
      "unit.floorOnly": "{f} этаж",
      "areas.kicker": "Районы",
      "areas.title": "В каких районах Чирчика?",
      "areas.sub": "При размещении район выбирается кнопкой — 18 районов.",
      "faq.kicker": "Вопросы и ответы",
      "faq.title": "Частые вопросы",
      "faq.1.q": "Это бесплатно?",
      "faq.1.a": "Да. И просмотр, и размещение объявлений — бесплатно.",
      "faq.2.q": "Нужно ли регистрироваться, чтобы смотреть объявления?",
      "faq.2.a": "Нет. Каталог открыт для всех. Регистрация (имя и телефон) нужна только для размещения объявления.",
      "faq.3.q": "Кто проверяет объявления?",
      "faq.3.a": "Админ. Каждое объявление просматривается перед публикацией.",
      "faq.4.q": "Как связаться с хозяином?",
      "faq.4.a": "Откройте объявление в приложении и нажмите «Связаться» — появится номер телефона.",
      "faq.5.q": "Как сменить язык?",
      "faq.5.a": "Командой /language в боте или через «Настройки». Приложение использует язык бота.",
      "faq.6.q": "Как удалить своё объявление?",
      "faq.6.a": "В приложении откройте «Мои объявления» и удалите объявление.",
      "cta.title": "Начните прямо сейчас",
      "cta.text": "Найдите квартиру или разместите объявление бесплатно — всё в Telegram.",
      "cta.btn": "Открыть бота",
      "cta.github": "Код на GitHub",
      "footer.logoAlt": "Логотип Chirchiq Kvartira",
      "footer.tagline": "Telegram-бот и мини-приложение для аренды и продажи квартир в Чирчике.",
      "footer.links": "Ссылки",
      "footer.bot": "Telegram-бот",
      "footer.github": "GitHub",
      "footer.copy": "© 2026 Chirchiq Kvartira",
      "footer.open": "Проект с открытым кодом"
    },

    en: {
      "meta.title": "Chirchiq Kvartira — apartments for rent and sale in Chirchiq | Telegram bot",
      "meta.description": "Apartment rent and sale listings in Chirchiq — a Telegram bot and mini app. Posting is free, every listing is checked by an admin.",
      "meta.ogTitle": "Chirchiq Kvartira — apartments for rent and sale in Chirchiq",
      "meta.ogDescription": "Telegram bot and mini app: rent and sale listings, free posting, admin-checked.",
      "skip": "Skip to content",
      "home.aria": "Chirchiq Kvartira — home",
      "nav.label": "Main menu",
      "nav.menu": "Menu",
      "nav.features": "Features",
      "nav.how": "How it works",
      "nav.listings": "Listings",
      "nav.faq": "FAQ",
      "nav.openBot": "Open the bot",
      "lang.label": "Choose language",
      "theme.toggle": "Toggle theme",
      "hero.eyebrow": "Telegram bot + mini app",
      "hero.h1a": "An apartment in Chirchiq —",
      "hero.h1b": "in a few taps",
      "hero.sub": "Rent and sale listings in one place. Posting is free, and every listing is checked by an admin.",
      "hero.cta": "Open the bot",
      "hero.how": "How it works",
      "hero.factsLabel": "Facts",
      "hero.fact1": "Free",
      "hero.fact2": "3 languages",
      "hero.fact3": "18 areas of Chirchiq",
      "hero.live1": "{n} active listing right now",
      "hero.live2": "{n} active listings right now",
      "hero.live5": "{n} active listings right now",
      "mock.aria": "Preview of the mini app catalog",
      "mock.title": "Chirchiq Kvartira",
      "mock.all": "All",
      "mock.rent": "Rent",
      "mock.sale": "Sale",
      "mock.filter": "Filter",
      "mock.tabCatalog": "Listings",
      "mock.tabMy": "My listings",
      "features.kicker": "Features",
      "features.title": "Everything you need — inside Telegram",
      "features.sub": "Nothing to install: both the bot and the mini app open right in Telegram.",
      "features.1.title": "Mini app with photos",
      "features.1.text": "Listings with photos and a gallery. Filter by type (rent / sale), rooms and price.",
      "features.2.title": "One-tap contact",
      "features.2.text": "The “Contact” button shows the owner's phone number right away. No middlemen.",
      "features.3.title": "Free posting",
      "features.3.text": "Area, price (“3 mln”), size, floor, features — almost everything with buttons, in a few minutes.",
      "features.4.title": "Location on the map",
      "features.4.text": "Every listing gets a map pin — see where the building is.",
      "features.5.title": "Admin-checked",
      "features.5.text": "Every listing is reviewed by an admin before it goes live.",
      "features.6.title": "Three languages",
      "features.6.text": "Uzbek, Russian and English — in the bot and in the app.",
      "how.kicker": "How it works",
      "how.title": "Three steps — two paths",
      "how.sub": "Looking for an apartment or posting one — it all happens in the bot, in a few minutes.",
      "how.a.title": "I'm looking for an apartment",
      "how.a.1t": "Open the bot",
      "how.a.1d": "Go to @Chirchiq_Arenda_bot and press Start.",
      "how.a.2t": "Open the app",
      "how.a.2d": "Tap “Open app” — the photo catalog opens.",
      "how.a.3t": "Filter and get in touch",
      "how.a.3d": "Rent or sale, rooms, price. Like it? Tap “Contact” and the number appears.",
      "how.b.title": "I want to post a listing",
      "how.b.1t": "Register",
      "how.b.1d": "Name and phone number — once, one minute.",
      "how.b.2t": "Answer with buttons",
      "how.b.2d": "Area, price, size, floor, photos — the bot asks step by step.",
      "how.b.3t": "Admin approves",
      "how.b.3d": "After review, the listing appears in the catalog.",
      "listings.kicker": "Live",
      "listings.title": "Latest listings",
      "listings.sub": "Active listings from the bot — straight from the database.",
      "listings.loading": "Loading listings…",
      "listings.loadingHint": "The first request to the server can take up to a minute.",
      "listings.failTitle": "Couldn't load listings right now",
      "listings.failText": "See them in the bot — the catalog is always open.",
      "listings.empty": "No active listings yet — be the first to post!",
      "listings.openBot": "Open in the bot",
      "listings.all": "All listings — in the bot",
      "listings.photoAlt": "Listing photo",
      "unit.room1": "1 room",
      "unit.rooms": "{n} rooms",
      "unit.area": "{n} m²",
      "unit.floor": "floor {f}/{t}",
      "unit.floorOnly": "floor {f}",
      "areas.kicker": "Areas",
      "areas.title": "Which areas of Chirchiq?",
      "areas.sub": "When posting, the area is picked with a button — 18 areas.",
      "faq.kicker": "FAQ",
      "faq.title": "Frequently asked questions",
      "faq.1.q": "Is it free?",
      "faq.1.a": "Yes. Browsing and posting listings are both free.",
      "faq.2.q": "Do I need to register to browse?",
      "faq.2.a": "No. The catalog is open to everyone. Registration (name and phone) is only needed to post a listing.",
      "faq.3.q": "Who checks the listings?",
      "faq.3.a": "An admin. Every listing is reviewed before it is published.",
      "faq.4.q": "How do I contact the owner?",
      "faq.4.a": "Open the listing in the app and tap “Contact” — the phone number appears.",
      "faq.5.q": "How do I change the language?",
      "faq.5.a": "Use the /language command in the bot or “Settings”. The app follows the bot's language.",
      "faq.6.q": "How do I delete my listing?",
      "faq.6.a": "In the app, open “My listings” and delete the listing.",
      "cta.title": "Start right now",
      "cta.text": "Find an apartment or post your listing for free — all in Telegram.",
      "cta.btn": "Open the bot",
      "cta.github": "Code on GitHub",
      "footer.logoAlt": "Chirchiq Kvartira logo",
      "footer.tagline": "A Telegram bot and mini app for apartment rent and sale in Chirchiq.",
      "footer.links": "Links",
      "footer.bot": "Telegram bot",
      "footer.github": "GitHub",
      "footer.copy": "© 2026 Chirchiq Kvartira",
      "footer.open": "Open-source project"
    }
  };

  /* The 18 areas of Chirchiq, same order and wording as in the bot. */
  var AREAS = [
    { uz: "1-mikrorayon (Oktyabr)", ru: "1-микрорайон (Октябрь)", en: "Microdistrict 1 (Oktyabr)" },
    { uz: "2-mikrorayon", ru: "2-микрорайон", en: "Microdistrict 2" },
    { uz: "3-mikrorayon", ru: "3-микрорайон", en: "Microdistrict 3" },
    { uz: "4-mikrorayon", ru: "4-микрорайон", en: "Microdistrict 4" },
    { uz: "8-mikrorayon", ru: "8-микрорайон", en: "Microdistrict 8" },
    { uz: "9-mikrorayon", ru: "9-микрорайон", en: "Microdistrict 9" },
    { uz: "10-mikrorayon", ru: "10-микрорайон", en: "Microdistrict 10" },
    { uz: "Markaz (Navoiy)", ru: "Центр (Навои)", en: "Center (Navoi)" },
    { uz: "Troitsk", ru: "Троицк", en: "Troitsk" },
    { uz: "Oqqovoq", ru: "Аккавак", en: "Akkavak" },
    { uz: "Arancha", ru: "Аранча", en: "Arancha" },
    { uz: "500-ka (Gorpark)", ru: "500-ка (Горпарк)", en: "500-ka (Gorpark)" },
    { uz: "Roshcha", ru: "Роща", en: "Roshcha" },
    { uz: "Yangi O'zbekiston massivi", ru: "Массив Янги Узбекистан", en: "Yangi Uzbekistan area" },
    { uz: "Konstruktorlar mavzesi", ru: "Квартал Конструкторов", en: "Konstruktorlar quarter" },
    { uz: "Ximposyolok", ru: "Химпосёлок", en: "Khimposyolok" },
    { uz: "Jaloyir", ru: "Джалаир", en: "Jaloyir" },
    { uz: "Nijniy Komsomolsk", ru: "Нижний Комсомольск", en: "Nizhny Komsomolsk" }
  ];

  /* ------------------------------------------------------------------ */
  /* State and helpers                                                   */
  /* ------------------------------------------------------------------ */

  var state = {
    lang: "uz",
    total: null,            // number of active listings (from the API)
    listings: null,         // items of the last successful load, for the current language
    cache: {},              // lang -> items
    status: "loading",      // loading | ok | empty | fail
    controller: null        // AbortController of the in-flight listings request
  };

  var doc = document;
  var root = doc.documentElement;

  function $(id) { return doc.getElementById(id); }

  function t(key) {
    var table = I18N[state.lang] || I18N.uz;
    if (Object.prototype.hasOwnProperty.call(table, key)) return table[key];
    if (Object.prototype.hasOwnProperty.call(I18N.uz, key)) return I18N.uz[key];
    return key;
  }

  function fmt(str, vars) {
    return String(str).replace(/\{(\w+)\}/g, function (m, name) {
      return Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : m;
    });
  }

  function el(tag, className, text) {
    var node = doc.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  /* A small inline SVG built with the DOM API (no markup strings). */
  function svgIcon(paths, className) {
    var NS = "http://www.w3.org/2000/svg";
    var svg = doc.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    if (className) svg.setAttribute("class", className);
    for (var i = 0; i < paths.length; i++) {
      var p = doc.createElementNS(NS, "path");
      p.setAttribute("d", paths[i]);
      svg.appendChild(p);
    }
    return svg;
  }

  var ICON_SEND = ["M21 3 3 10.5l7 2.5 2.5 7L21 3z", "M10 13l11-10"];
  var ICON_PIN = ["M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z", "M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z"];
  var ICON_CLOUD_OFF = ["M3 3l18 18", "M7.5 19H17a4 4 0 0 0 1.2-7.8A7 7 0 0 0 8.1 7.1", "M5.4 9.6A4 4 0 0 0 7.5 19"];

  function botLink(className, labelKey) {
    var a = el("a", className);
    a.href = BOT_URL;
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(svgIcon(ICON_SEND));
    a.appendChild(el("span", null, t(labelKey)));
    return a;
  }

  function storageGet(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  function storageSet(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* private mode etc. */ }
  }

  /* ------------------------------------------------------------------ */
  /* Language                                                            */
  /* ------------------------------------------------------------------ */

  function initialLang() {
    var saved = storageGet(LANG_KEY);
    if (LANGS.indexOf(saved) !== -1) return saved;
    var nav = (navigator.language || "").toLowerCase();
    if (nav.indexOf("ru") === 0) return "ru";
    if (nav.indexOf("en") === 0) return "en";
    return "uz";
  }

  function applyTranslations() {
    var i, nodes;

    nodes = doc.querySelectorAll("[data-i18n]");
    for (i = 0; i < nodes.length; i++) {
      nodes[i].textContent = t(nodes[i].getAttribute("data-i18n"));
    }
    nodes = doc.querySelectorAll("[data-i18n-aria]");
    for (i = 0; i < nodes.length; i++) {
      nodes[i].setAttribute("aria-label", t(nodes[i].getAttribute("data-i18n-aria")));
    }
    nodes = doc.querySelectorAll("[data-i18n-content]");
    for (i = 0; i < nodes.length; i++) {
      nodes[i].setAttribute("content", t(nodes[i].getAttribute("data-i18n-content")));
    }
    nodes = doc.querySelectorAll("[data-i18n-alt]");
    for (i = 0; i < nodes.length; i++) {
      nodes[i].setAttribute("alt", t(nodes[i].getAttribute("data-i18n-alt")));
    }

    var ogLocale = doc.querySelector('meta[property="og:locale"]');
    if (ogLocale) ogLocale.setAttribute("content", { uz: "uz_UZ", ru: "ru_RU", en: "en_US" }[state.lang] || "uz_UZ");

    nodes = doc.querySelectorAll("#areas-list [data-area]");
    for (i = 0; i < nodes.length; i++) {
      var area = AREAS[parseInt(nodes[i].getAttribute("data-area"), 10)];
      if (area) nodes[i].textContent = area[state.lang] || area.uz;
    }
  }

  function setLang(lang, userChoice) {
    if (LANGS.indexOf(lang) === -1) lang = "uz";
    var changed = lang !== state.lang;
    state.lang = lang;
    root.setAttribute("lang", lang);
    if (userChoice) storageSet(LANG_KEY, lang);

    var buttons = doc.querySelectorAll(".lang button[data-lang]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("aria-pressed", buttons[i].getAttribute("data-lang") === lang ? "true" : "false");
    }

    applyTranslations();
    renderLiveBadge();
    renderStatus();

    if (changed) {
      if (state.cache[lang]) {
        // Serve from cache and drop any in-flight request for another language,
        // so a late response cannot overwrite the grid with the wrong language.
        if (state.controller) { state.controller.abort(); state.controller = null; }
        state.listings = state.cache[lang];
        state.status = state.listings.length ? "ok" : "empty";
        renderListings(state.listings);
        renderMockup(state.listings);
        renderStatus();
      } else {
        loadListings();
      }
    }
  }

  /* ------------------------------------------------------------------ */
  /* Theme                                                               */
  /* ------------------------------------------------------------------ */

  var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function currentTheme() {
    var attr = root.getAttribute("data-theme");
    if (attr === "light" || attr === "dark") return attr;
    return media && media.matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var meta = doc.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "dark" ? "#0B1220" : "#1E3A8A");
  }

  function initTheme() {
    var saved = storageGet(THEME_KEY);
    applyTheme(saved === "light" || saved === "dark" ? saved : currentTheme());

    var toggle = $("theme-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        var next = currentTheme() === "dark" ? "light" : "dark";
        applyTheme(next);
        storageSet(THEME_KEY, next);
      });
    }

    if (media) {
      var onChange = function (e) {
        var pref = storageGet(THEME_KEY);
        if (pref !== "light" && pref !== "dark") applyTheme(e.matches ? "dark" : "light");
      };
      if (media.addEventListener) media.addEventListener("change", onChange);
      else if (media.addListener) media.addListener(onChange);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Mobile menu                                                         */
  /* ------------------------------------------------------------------ */

  function initMenu() {
    var toggle = $("menu-toggle");
    var nav = $("nav");
    if (!toggle || !nav) return;

    function setOpen(open) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    }

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    nav.addEventListener("click", function (e) {
      if (e.target && e.target.closest && e.target.closest("a")) setOpen(false);
    });
    doc.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Entrance animations                                                 */
  /* ------------------------------------------------------------------ */

  function initReveal() {
    var items = doc.querySelectorAll(".reveal");
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var i;

    if (reduce || !("IntersectionObserver" in window)) {
      for (i = 0; i < items.length; i++) items[i].classList.add("is-in");
      return;
    }

    // Stagger siblings inside a grid.
    var grids = doc.querySelectorAll(".features-grid, .how-grid, .faq-list");
    for (i = 0; i < grids.length; i++) {
      var kids = grids[i].children;
      for (var k = 0; k < kids.length; k++) kids[k].style.setProperty("--i", String(k % 6));
    }

    var io = new IntersectionObserver(function (entries) {
      for (var j = 0; j < entries.length; j++) {
        if (entries[j].isIntersecting) {
          entries[j].target.classList.add("is-in");
          io.unobserve(entries[j].target);
        }
      }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    for (i = 0; i < items.length; i++) io.observe(items[i]);
  }

  /* ------------------------------------------------------------------ */
  /* API                                                                 */
  /* ------------------------------------------------------------------ */

  function fetchJSON(url, controller) {
    var timer = setTimeout(function () { controller.abort(); }, FETCH_TIMEOUT);
    return fetch(url, { signal: controller.signal, headers: { "Accept": "application/json" } })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) { clearTimeout(timer); return data; }, function (err) { clearTimeout(timer); throw err; });
  }

  function photoUrl(path) {
    if (typeof path !== "string" || !path) return null;
    if (/^https?:\/\//i.test(path)) return path;
    return API + (path.charAt(0) === "/" ? path : "/" + path);
  }

  function fmtArea(area) {
    var n = Number(area);
    if (!isFinite(n) || n <= 0) return null;
    return Number.isInteger(n) ? String(n) : String(Math.round(n * 10) / 10);
  }

  function listingTitle(item) {
    var parts = [];
    var rooms = parseInt(item.rooms, 10);
    var area = fmtArea(item.area);
    var floor = parseInt(item.floor, 10);
    var total = parseInt(item.total_floors, 10);

    if (rooms > 0) parts.push(rooms === 1 ? t("unit.room1") : fmt(t("unit.rooms"), { n: rooms }));
    if (area) parts.push(fmt(t("unit.area"), { n: area }));
    if (floor > 0) {
      parts.push(total > 0 ? fmt(t("unit.floor"), { f: floor, t: total }) : fmt(t("unit.floorOnly"), { f: floor }));
    }
    return parts.join(" · ");
  }

  function pluralKey(n) {
    if (state.lang === "ru") {
      var m10 = n % 10, m100 = n % 100;
      if (m10 === 1 && m100 !== 11) return "hero.live1";
      if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return "hero.live2";
      return "hero.live5";
    }
    if (state.lang === "en") return n === 1 ? "hero.live1" : "hero.live5";
    return "hero.live5";
  }

  /* ------------------------------------------------------------------ */
  /* Rendering                                                           */
  /* ------------------------------------------------------------------ */

  function renderLiveBadge() {
    var badge = $("live-badge");
    var text = $("live-text");
    if (!badge || !text) return;
    if (typeof state.total !== "number" || state.total < 0) {
      badge.hidden = true;
      return;
    }
    text.textContent = fmt(t(pluralKey(state.total)), { n: state.total });
    badge.hidden = false;
  }

  function renderStatus() {
    var box = $("listings-status");
    var spinner = $("listings-spinner");
    var text = $("listings-status-text");
    var hint = $("listings-status-hint");
    if (!box || !text) return;

    if (state.status === "loading") {
      box.hidden = false;
      if (spinner) spinner.hidden = false;
      text.textContent = t("listings.loading");
      if (hint) hint.textContent = t("listings.loadingHint");
    } else if (state.status === "empty") {
      box.hidden = false;
      if (spinner) spinner.hidden = true;
      text.textContent = t("listings.empty");
      if (hint) hint.textContent = "";
    } else {
      box.hidden = true;
    }
  }

  function clearChildren(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function renderSkeletons(grid) {
    clearChildren(grid);
    for (var i = 0; i < 6; i++) {
      var card = el("div", "card listing skeleton");
      card.setAttribute("aria-hidden", "true");
      card.appendChild(el("div", "listing-photo"));
      var body = el("div", "listing-body");
      body.appendChild(el("span", "sk sk-price"));
      body.appendChild(el("span", "sk sk-title"));
      body.appendChild(el("span", "sk sk-addr"));
      card.appendChild(body);
      grid.appendChild(card);
    }
  }

  function listingCard(item) {
    var card = el("article", "card listing reveal is-in");
    var title = listingTitle(item);
    var address = typeof item.address === "string" ? item.address : "";

    var photoBox = el("div", "listing-photo");
    var url = Array.isArray(item.photos) && item.photos.length ? photoUrl(item.photos[0]) : null;
    if (url) {
      var img = el("img");
      img.src = url;
      img.loading = "lazy";
      img.decoding = "async";
      img.alt = t("listings.photoAlt") + (title ? ": " + title : "") + (address ? ", " + address : "");
      img.addEventListener("error", function () { if (img.parentNode) img.parentNode.removeChild(img); });
      photoBox.appendChild(img);
    }
    if (typeof item.type_text === "string" && item.type_text) {
      photoBox.appendChild(el("span", "badge listing-badge", item.type_text));
    }
    card.appendChild(photoBox);

    var body = el("div", "listing-body");
    if (typeof item.price_text === "string" && item.price_text) {
      body.appendChild(el("p", "listing-price", item.price_text));
    }
    if (title) body.appendChild(el("h3", "listing-title", title));
    if (address) {
      var addr = el("p", "listing-addr");
      addr.appendChild(svgIcon(ICON_PIN));
      addr.appendChild(el("span", null, address));
      body.appendChild(addr);
    }
    var actions = el("div", "listing-actions");
    actions.appendChild(botLink("btn btn-secondary btn-sm", "listings.openBot"));
    body.appendChild(actions);
    card.appendChild(body);
    return card;
  }

  function renderListings(items) {
    var grid = $("listings-grid");
    if (!grid) return;
    clearChildren(grid);
    for (var i = 0; i < items.length && i < 6; i++) {
      grid.appendChild(listingCard(items[i]));
    }
  }

  function renderFailure() {
    var grid = $("listings-grid");
    if (!grid) return;
    clearChildren(grid);

    var card = el("div", "card fail-card");
    card.setAttribute("role", "status");
    var icon = el("div", "feature-icon");
    icon.setAttribute("aria-hidden", "true");
    icon.appendChild(svgIcon(ICON_CLOUD_OFF));
    card.appendChild(icon);
    card.appendChild(el("h3", null, t("listings.failTitle")));
    card.appendChild(el("p", null, t("listings.failText")));
    card.appendChild(botLink("btn btn-primary", "listings.openBot"));
    grid.appendChild(card);
  }

  function renderMockup(items) {
    var cards = doc.querySelectorAll("#mock-list .m-card");
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      var item = items && items[i];
      var photo = card.querySelector(".m-photo");
      var badge = card.querySelector(".m-badge");
      var price = card.querySelector(".m-price");
      var meta = card.querySelector(".m-meta");
      var addr = card.querySelector(".m-addr");
      var oldImg = photo ? photo.querySelector("img") : null;

      if (!item) {
        card.classList.add("is-ph");
        if (oldImg) oldImg.parentNode.removeChild(oldImg);
        if (badge) { badge.hidden = true; badge.textContent = ""; }
        if (price) price.textContent = "";
        if (meta) meta.textContent = "";
        if (addr) addr.textContent = "";
        continue;
      }

      card.classList.remove("is-ph");
      var url = Array.isArray(item.photos) && item.photos.length ? photoUrl(item.photos[0]) : null;
      if (photo) {
        if (oldImg && oldImg.getAttribute("src") !== url) { oldImg.parentNode.removeChild(oldImg); oldImg = null; }
        if (url && !oldImg) {
          var img = el("img");
          img.src = url;
          img.alt = "";
          img.loading = "lazy";
          img.decoding = "async";
          img.addEventListener("error", function () { if (this.parentNode) this.parentNode.removeChild(this); });
          photo.insertBefore(img, photo.firstChild);
        } else if (!url && oldImg) {
          oldImg.parentNode.removeChild(oldImg);
        }
      }
      if (badge) {
        var type = typeof item.type_text === "string" ? item.type_text : "";
        badge.textContent = type;
        badge.hidden = !type;
      }
      if (price) price.textContent = typeof item.price_text === "string" && item.price_text ? item.price_text : "—";

      var metaParts = [];
      var rooms = parseInt(item.rooms, 10);
      var area = fmtArea(item.area);
      if (rooms > 0) metaParts.push(rooms === 1 ? t("unit.room1") : fmt(t("unit.rooms"), { n: rooms }));
      if (area) metaParts.push(fmt(t("unit.area"), { n: area }));
      if (meta) meta.textContent = metaParts.length ? metaParts.join(" · ") : "—";
      if (addr) addr.textContent = typeof item.address === "string" && item.address ? item.address : "—";
    }
  }

  /* ------------------------------------------------------------------ */
  /* Loading                                                             */
  /* ------------------------------------------------------------------ */

  function loadTotal() {
    if (!window.fetch || !window.AbortController) return;
    var controller = new AbortController();
    fetchJSON(API + "/api/listings?limit=1", controller)
      .then(function (data) {
        var total = data && typeof data.total === "number" ? data.total : null;
        if (total !== null && total >= 0) {
          state.total = total;
          renderLiveBadge();
        }
      })
      .catch(function () { /* keep the badge hidden */ });
  }

  function loadListings() {
    var grid = $("listings-grid");
    if (!grid) return;

    if (!window.fetch || !window.AbortController) {
      state.status = "fail";
      renderStatus();
      renderFailure();
      return;
    }

    if (state.controller) state.controller.abort();
    var controller = new AbortController();
    state.controller = controller;
    var lang = state.lang;
    var keep = state.listings; // last rendered items: keeps the mockup filled (units re-localized) while loading

    state.status = "loading";
    state.listings = null;
    renderStatus();
    renderSkeletons(grid);
    renderMockup(keep);

    fetchJSON(API + "/api/listings?limit=6&lang=" + encodeURIComponent(lang), controller)
      .then(function (data) {
        if (controller !== state.controller) return; // superseded by a newer request
        var items = data && Array.isArray(data.items) ? data.items : [];
        state.cache[lang] = items;
        if (lang !== state.lang) return; // language changed meanwhile; cached for later
        state.controller = null;
        state.listings = items;
        if (typeof data.total === "number" && data.total >= 0) {
          state.total = data.total;
          renderLiveBadge();
        }
        state.status = items.length ? "ok" : "empty";
        renderListings(items);
        renderMockup(items);
        renderStatus();
      })
      .catch(function () {
        if (controller !== state.controller) return;
        state.controller = null;
        state.status = "fail";
        renderStatus();
        renderFailure();
        renderMockup(keep); // placeholders on first load, previous items after a failed refetch
      });
  }

  /* ------------------------------------------------------------------ */
  /* Boot                                                                */
  /* ------------------------------------------------------------------ */

  function init() {
    initTheme();
    initMenu();

    var buttons = doc.querySelectorAll(".lang button[data-lang]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        setLang(this.getAttribute("data-lang"), true);
      });
    }

    state.lang = null; // force setLang to treat the first call as a change
    setLang(initialLang(), false);
    initReveal();
    loadTotal();
  }

  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", init);
  else init();
})();
