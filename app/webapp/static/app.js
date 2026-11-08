/* Chirchiq Kvartira — Telegram Mini App (frontend)
 * Plain JS, no build step. All server data is inserted via textContent.
 */
(function () {
  'use strict';

  var BOT_USERNAME = 'Chirchiq_Arenda_bot';
  var BOT_URL = 'https://t.me/' + BOT_USERNAME;
  var BOT_ADD_URL = BOT_URL + '?start=add';

  // =====================================================================
  // Telegram SDK
  // =====================================================================
  var tg = (window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;

  // Telegram passes launch data in the URL hash (#tgWebAppData=...). The official SDK
  // reads it, but if the SDK script fails to load — common on some networks — we read
  // it ourselves so auth still works.
  function hashParam(name) {
    try {
      var raw = location.hash.charAt(0) === '#' ? location.hash.slice(1) : location.hash;
      var m = new RegExp('(?:^|&)' + name + '=([^&]*)').exec(raw);
      return m && m[1] ? decodeURIComponent(m[1]) : '';
    } catch (e) { return ''; }
  }
  function fallbackInitData() {
    var v = hashParam('tgWebAppData');
    try {
      if (v) sessionStorage.setItem('ck_initData', v);
      else v = sessionStorage.getItem('ck_initData') || '';
    } catch (e) { /* storage unavailable */ }
    return v;
  }
  function fallbackTheme() {
    // Without the SDK, apply Telegram's theme colors from the hash ourselves
    if (tg) return;
    try {
      var params = JSON.parse(hashParam('tgWebAppThemeParams') || '{}');
      var root = document.documentElement.style;
      Object.keys(params).forEach(function (k) {
        root.setProperty('--tg-theme-' + k.replace(/_/g, '-'), params[k]);
      });
      if (params.bg_color) {
        var hex = params.bg_color.replace('#', '');
        var r = parseInt(hex.substr(0, 2), 16), g = parseInt(hex.substr(2, 2), 16), b = parseInt(hex.substr(4, 2), 16);
        document.documentElement.setAttribute('data-theme', (r * 299 + g * 587 + b * 114) / 1000 < 128 ? 'dark' : 'light');
      }
    } catch (e) { /* ignore */ }
  }

  var initData = (tg && typeof tg.initData === 'string' && tg.initData) ? tg.initData : fallbackInitData();
  var inTelegram = initData.length > 0;
  // Opened inside a Telegram client but without the user's identity (e.g. from a reply-keyboard button)
  var tgPlatform = (tg && tg.platform) || hashParam('tgWebAppPlatform') || 'unknown';
  var inTelegramNoUser = !inTelegram && tgPlatform !== 'unknown';
  fallbackTheme();

  // The Telegram user (id, first_name, last_name, username, language_code) — from the SDK,
  // or parsed from the raw initData when the SDK is missing. Display only; the server
  // validates initData itself.
  function telegramUser() {
    try {
      var u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
      if (u && typeof u === 'object') return u;
    } catch (e) { /* ignore */ }
    try {
      var m = /(?:^|&)user=([^&]*)/.exec(initData || '');
      if (m) {
        var user = JSON.parse(decodeURIComponent(m[1]));
        if (user && typeof user === 'object') return user;
      }
    } catch (e) { /* ignore */ }
    return null;
  }
  var TG_USER = telegramUser();

  // API base: same origin in production. Only when the page itself is served from
  // localhost (UI testing with a static server) may ?api=https://host point the app at
  // a remote API, so a crafted production link can never redirect initData elsewhere.
  var API_BASE = '';
  try {
    var hn = location.hostname;
    if (hn === 'localhost' || hn === '127.0.0.1' || hn === '[::1]') {
      var apiParam = new URLSearchParams(location.search).get('api') || '';
      if (/^https?:\/\/[^\s/?#]+$/i.test(apiParam)) API_BASE = apiParam;
    }
  } catch (e) { API_BASE = ''; }

  // =====================================================================
  // i18n — uz (default) / ru / en
  // Order: ?lang= in the URL (the bot opens the app with it) -> remembered value
  // -> Telegram user's language_code -> 'uz'.
  // A value may be an array of plural forms (ru: [one, few, many], en: [one, other]).
  // =====================================================================
  var LANGS = ['uz', 'ru', 'en'];
  var LANG_KEY = 'ck_lang';

  var I18N = {
    uz: {
      'search.placeholder': 'Qidirish: mavze, xona, narx...',
      'search.label': 'Qidirish',
      'search.clear': 'Tozalash',
      'filter.button': 'Filtr',
      'filter.title': 'Filtr',
      'filter.type': "E'lon turi",
      'filter.rooms': 'Xonalar soni',
      'filter.currency': 'Valyuta',
      'filter.price': 'Narx',
      'filter.apply': "Qo'llash",
      'filter.clear': 'Tozalash',
      'filter.reset': 'Filtrni tozalash',
      'seg.all': 'Hammasi',
      'seg.rent': 'Ijaraga',
      'seg.sale': 'Sotuv',
      'chip.all': 'Hammasi',
      'chip.r1': '1 xona',
      'chip.r2': '2 xona',
      'chip.r3': '3 xona',
      'chip.r4': '4+ xona',
      'price.from': 'Dan',
      'price.to': 'Gacha',
      'price.need_currency': "Narx bo'yicha filtr uchun valyutani tanlang",
      'sort.title': 'Saralash',
      'sort.new': 'Eng yangi',
      'sort.cheap': 'Arzon',
      'sort.expensive': 'Qimmat',
      'cur.som': "so'm",
      'catalog.more': "Yana ko'rsatish",
      'catalog.count': "{n} ta e'lon",
      'catalog.empty_title': "E'lonlar topilmadi",
      'catalog.empty_text': "Qidiruv yoki filtrni o'zgartirib ko'ring",
      'common.loading': 'Yuklanmoqda…',
      'common.retry': 'Qayta urinish',
      'common.close': 'Yopish',
      'common.load_failed': "Yuklab bo'lmadi",
      'toast.retry': 'Qayta',
      'tabs.label': "Bo'limlar",
      'tabs.catalog': 'Uylar',
      'tabs.favs': 'Sevimlilar',
      'tabs.add': "E'lon berish",
      'tabs.profile': 'Profil',
      'type.rent': 'Ijaraga',
      'type.sale': 'Sotiladi',
      'status.pending': 'Tekshiruvda',
      'status.approved': 'Faol',
      'status.rejected': 'Rad etilgan',
      'status.archived': 'Arxivda',
      'title.rooms': '{n} xonali',
      'title.apartment': '{n} xonali kvartira',
      'title.area': '{n} m²',
      'title.floor_of': '{floor}/{total} qavat',
      'title.floor': '{floor}-qavat',
      'title.total_floors': '{n} qavatli',
      'meta.rooms': '{n} xona',
      'city': 'Chirchiq',
      'date.today': 'bugun',
      'date.yesterday': 'kecha',
      'date.days': '{n} kun oldin',
      'date.weeks': '{n} hafta oldin',
      'date.months': '{n} oy oldin',
      'date.years': '{n} yil oldin',
      'err.status': 'Xatolik: {n}',
      'err.generic': 'Xatolik',
      'err.401': 'Avtorizatsiya talab qilinadi',
      'err.404': "E'lon topilmadi",
      'err.500': "Server xatosi, keyinroq urinib ko'ring",
      'err.network': 'Tarmoq xatosi. Internetni tekshiring',
      'detail.label': "E'lon",
      'detail.map': "Xaritada ko'rish",
      'tag.rent': 'Ijara',
      'tag.sale': 'Sotuv',
      'tag.new': 'Yangi',
      'spec.rooms': 'xona',
      'spec.area': 'm²',
      'spec.floor': 'qavat',
      'photos.count': '{n} ta rasm',
      'detail.info': "Ma'lumotlar",
      'detail.description': 'Tavsif',
      'detail.rooms': 'Xonalar',
      'detail.area': 'Maydon',
      'detail.floor': 'Qavat',
      'detail.total_floors': 'Bino qavatlari',
      'detail.district': 'Tuman',
      'detail.address': 'Manzil',
      'detail.number': "E'lon raqami",
      'detail.date': 'Sana',
      'detail.owner': "E'lon egasi",
      'detail.views': "{n} ko'rishlar",
      'detail.contacts': '{n} ta murojaat',
      'gallery.prev': 'Oldingi rasm',
      'gallery.next': 'Keyingi rasm',
      'fav.add': "Sevimlilarga qo'shish",
      'fav.remove': 'Sevimlilardan olib tashlash',
      'favs.title': 'Sevimlilar',
      'favs.count': '{n} ta',
      'favs.empty_title': "Sevimlilar bo'sh",
      'favs.empty_text': "E'lon kartasidagi ♡ belgisini bosib saqlab qo'ying",
      'favs.go_catalog': "E'lonlarga o'tish",
      'action.delete': "O'chirish",
      'action.contact': "Bog'lanish",
      'contact.title': "Bog'lanish",
      'contact.call': "Qo'ng'iroq qilish",
      'contact.copy': 'Nusxalash',
      'contact.copied': 'Raqam nusxalandi',
      'contact.copy_failed': "Nusxalab bo'lmadi",
      'contact.outside': "Telefon raqamini ko'rish uchun ilovani Telegram ichida oching",
      'contact.outside_no_user': "Telefon raqamini ko'rish uchun ilovani yozuv maydoni yonidagi «{app}» tugmasi orqali qayta oching",
      'delete.confirm': "E'lon #{id} o'chirilsinmi? Bu amalni qaytarib bo'lmaydi.",
      'delete.done': "E'lon o'chirildi",
      'delete.forbidden': "Bu e'lon sizga tegishli emas",
      'app.only_in_telegram': 'Bu tugma faqat Telegram ichida ishlaydi',
      'add.title': "E'lon berish",
      'add.lead': "E'loningiz 3 qadamda joylanadi",
      'add.note': "Faqat Chirchiq shahri bo'yicha e'lonlar qabul qilinadi",
      'add.step1_title': 'Botni oching',
      'add.step1_text': "Pastdagi tugma sizni @" + BOT_USERNAME + " ga olib o'tadi",
      'add.step2_title': "Ma'lumotlarni kiriting",
      'add.step2_text': 'Tur, xonalar, narx, manzil va rasmlar',
      'add.step3_title': 'Tekshiruvni kuting',
      'add.step3_text': "Tasdiqlangach e'lon katalogda paydo bo'ladi",
      'add.button': "E'lon berish",
      'add.foot': "Tugma botdagi e'lon qo'shish bo'limini ochadi",
      'profile.title': 'Profil',
      'profile.registered': "Ro'yxatdan o'tgan",
      'profile.not_registered': "Ro'yxatdan o'tmagan",
      'profile.no_phone': "Telefon ko'rsatilmagan",
      'profile.guest': 'Foydalanuvchi',
      'profile.language': 'Til',
      'profile.open_bot': 'Botni ochish',
      'my.title': "Mening e'lonlarim",
      'my.refresh': 'Yangilash',
      'my.reopen_title': 'Ilovani qayta oching',
      'my.reopen_text': "Bu bo'lim uchun ilovani botdagi «{view}» tugmasi yoki yozuv maydoni yonidagi «{app}» tugmasi orqali oching",
      'my.only_tg_title': "Bu bo'lim faqat Telegram ichida ishlaydi",
      'my.only_tg_text': "Profilingiz va e'lonlaringizni ko'rish uchun ilovani Telegram botidan oching",
      'my.to_bot': "Botga o'tish",
      'my.not_registered_title': "Ro'yxatdan o'tmagansiz",
      'my.not_registered_text': "E'lon qo'shish uchun botda «{register}» tugmasini bosing",
      'my.empty_title': "Hali e'lonlaringiz yo'q",
      'my.empty_text': "Birinchi e'loningizni bot orqali qo'shing",
      'my.add_title': "Yangi e'lon qo'shish",
      'my.add_text': "Botdagi «{add}» tugmasi orqali yangi e'lon joylashtiring",
      // Bot button labels (must match app/i18n texts: btn.view_listings, btn.app_menu, btn.register, btn.add_listing)
      'bot.view_listings': "📱 E'lonlarni ko'rish",
      'bot.app_menu': 'Ilova',
      'bot.register': "📝 Ro'yxatdan o'tish",
      'bot.add_listing': "➕ E'lon qo'shish"
    },
    ru: {
      'search.placeholder': 'Поиск: район, комнаты, цена...',
      'search.label': 'Поиск',
      'search.clear': 'Очистить',
      'filter.button': 'Фильтр',
      'filter.title': 'Фильтр',
      'filter.type': 'Тип объявления',
      'filter.rooms': 'Количество комнат',
      'filter.currency': 'Валюта',
      'filter.price': 'Цена',
      'filter.apply': 'Применить',
      'filter.clear': 'Сбросить',
      'filter.reset': 'Сбросить фильтр',
      'seg.all': 'Все',
      'seg.rent': 'Аренда',
      'seg.sale': 'Продажа',
      'chip.all': 'Все',
      'chip.r1': '1 комн',
      'chip.r2': '2 комн',
      'chip.r3': '3 комн',
      'chip.r4': '4+ комн',
      'price.from': 'От',
      'price.to': 'До',
      'price.need_currency': 'Чтобы фильтровать по цене, выберите валюту',
      'sort.title': 'Сортировка',
      'sort.new': 'Сначала новые',
      'sort.cheap': 'Дешевле',
      'sort.expensive': 'Дороже',
      'cur.som': 'сум',
      'catalog.more': 'Показать ещё',
      'catalog.count': ['{n} объявление', '{n} объявления', '{n} объявлений'],
      'catalog.empty_title': 'Объявления не найдены',
      'catalog.empty_text': 'Измените запрос или фильтр',
      'common.loading': 'Загрузка…',
      'common.retry': 'Повторить',
      'common.close': 'Закрыть',
      'common.load_failed': 'Не удалось загрузить',
      'toast.retry': 'Повторить',
      'tabs.label': 'Разделы',
      'tabs.catalog': 'Квартиры',
      'tabs.favs': 'Избранное',
      'tabs.add': 'Подать',
      'tabs.profile': 'Профиль',
      'type.rent': 'Аренда',
      'type.sale': 'Продажа',
      'status.pending': 'На проверке',
      'status.approved': 'Активно',
      'status.rejected': 'Отклонено',
      'status.archived': 'В архиве',
      'title.rooms': '{n}-комн.',
      'title.apartment': '{n}-комн. квартира',
      'title.area': '{n} м²',
      'title.floor_of': '{floor}/{total} этаж',
      'title.floor': '{floor} этаж',
      'title.total_floors': '{n}-этажный',
      'meta.rooms': '{n} комн.',
      'city': 'Чирчик',
      'date.today': 'сегодня',
      'date.yesterday': 'вчера',
      'date.days': ['{n} день назад', '{n} дня назад', '{n} дней назад'],
      'date.weeks': ['{n} неделю назад', '{n} недели назад', '{n} недель назад'],
      'date.months': ['{n} месяц назад', '{n} месяца назад', '{n} месяцев назад'],
      'date.years': ['{n} год назад', '{n} года назад', '{n} лет назад'],
      'err.status': 'Ошибка: {n}',
      'err.generic': 'Ошибка',
      'err.401': 'Требуется авторизация',
      'err.404': 'Объявление не найдено',
      'err.500': 'Ошибка сервера, попробуйте позже',
      'err.network': 'Ошибка сети. Проверьте интернет',
      'detail.label': 'Объявление',
      'detail.map': 'Показать на карте',
      'tag.rent': 'Аренда',
      'tag.sale': 'Продажа',
      'tag.new': 'Новое',
      'spec.rooms': 'комн.',
      'spec.area': 'м²',
      'spec.floor': 'этаж',
      'photos.count': ['{n} фото', '{n} фото', '{n} фото'],
      'detail.info': 'Характеристики',
      'detail.description': 'Описание',
      'detail.rooms': 'Комнаты',
      'detail.area': 'Площадь',
      'detail.floor': 'Этаж',
      'detail.total_floors': 'Этажность',
      'detail.district': 'Район',
      'detail.address': 'Адрес',
      'detail.number': 'Номер объявления',
      'detail.date': 'Дата',
      'detail.owner': 'Автор объявления',
      'detail.views': ['{n} просмотр', '{n} просмотра', '{n} просмотров'],
      'detail.contacts': ['{n} обращение', '{n} обращения', '{n} обращений'],
      'gallery.prev': 'Предыдущее фото',
      'gallery.next': 'Следующее фото',
      'fav.add': 'В избранное',
      'fav.remove': 'Убрать из избранного',
      'favs.title': 'Избранное',
      'favs.count': '{n}',
      'favs.empty_title': 'В избранном пусто',
      'favs.empty_text': 'Нажмите ♡ на карточке объявления, чтобы сохранить его',
      'favs.go_catalog': 'К объявлениям',
      'action.delete': 'Удалить',
      'action.contact': 'Связаться',
      'contact.title': 'Связаться',
      'contact.call': 'Позвонить',
      'contact.copy': 'Скопировать',
      'contact.copied': 'Номер скопирован',
      'contact.copy_failed': 'Не удалось скопировать',
      'contact.outside': 'Чтобы увидеть номер телефона, откройте приложение в Telegram',
      'contact.outside_no_user': 'Чтобы увидеть номер телефона, откройте приложение заново кнопкой «{app}» рядом с полем ввода',
      'delete.confirm': 'Удалить объявление #{id}? Это действие нельзя отменить.',
      'delete.done': 'Объявление удалено',
      'delete.forbidden': 'Это объявление вам не принадлежит',
      'app.only_in_telegram': 'Эта кнопка работает только в Telegram',
      'add.title': 'Подать объявление',
      'add.lead': 'Объявление размещается в 3 шага',
      'add.note': 'Принимаются только объявления по городу Чирчик',
      'add.step1_title': 'Откройте бот',
      'add.step1_text': 'Кнопка ниже откроет @' + BOT_USERNAME,
      'add.step2_title': 'Заполните данные',
      'add.step2_text': 'Тип, комнаты, цена, адрес и фото',
      'add.step3_title': 'Дождитесь проверки',
      'add.step3_text': 'После одобрения объявление появится в каталоге',
      'add.button': 'Подать объявление',
      'add.foot': 'Кнопка открывает раздел добавления объявления в боте',
      'profile.title': 'Профиль',
      'profile.registered': 'Зарегистрирован',
      'profile.not_registered': 'Не зарегистрирован',
      'profile.no_phone': 'Телефон не указан',
      'profile.guest': 'Пользователь',
      'profile.language': 'Язык',
      'profile.open_bot': 'Открыть бот',
      'my.title': 'Мои объявления',
      'my.refresh': 'Обновить',
      'my.reopen_title': 'Откройте приложение заново',
      'my.reopen_text': 'Для этого раздела откройте приложение кнопкой «{view}» в боте или кнопкой «{app}» рядом с полем ввода',
      'my.only_tg_title': 'Этот раздел работает только в Telegram',
      'my.only_tg_text': 'Чтобы увидеть профиль и свои объявления, откройте приложение из Telegram-бота',
      'my.to_bot': 'Перейти в бот',
      'my.not_registered_title': 'Вы не зарегистрированы',
      'my.not_registered_text': 'Чтобы добавить объявление, нажмите в боте кнопку «{register}»',
      'my.empty_title': 'У вас пока нет объявлений',
      'my.empty_text': 'Добавьте первое объявление через бота',
      'my.add_title': 'Новое объявление',
      'my.add_text': 'Разместите новое объявление кнопкой «{add}» в боте',
      'bot.view_listings': '📱 Смотреть объявления',
      'bot.app_menu': 'Приложение',
      'bot.register': '📝 Регистрация',
      'bot.add_listing': '➕ Добавить объявление'
    },
    en: {
      'search.placeholder': 'Search: area, rooms, price...',
      'search.label': 'Search',
      'search.clear': 'Clear',
      'filter.button': 'Filter',
      'filter.title': 'Filter',
      'filter.type': 'Listing type',
      'filter.rooms': 'Rooms',
      'filter.currency': 'Currency',
      'filter.price': 'Price',
      'filter.apply': 'Apply',
      'filter.clear': 'Clear',
      'filter.reset': 'Clear filters',
      'seg.all': 'All',
      'seg.rent': 'Rent',
      'seg.sale': 'Sale',
      'chip.all': 'All',
      'chip.r1': '1 room',
      'chip.r2': '2 rooms',
      'chip.r3': '3 rooms',
      'chip.r4': '4+ rooms',
      'price.from': 'From',
      'price.to': 'To',
      'price.need_currency': 'Choose a currency to filter by price',
      'sort.title': 'Sort by',
      'sort.new': 'Newest',
      'sort.cheap': 'Cheapest',
      'sort.expensive': 'Most expensive',
      'cur.som': 'UZS',
      'catalog.more': 'Show more',
      'catalog.count': ['{n} listing', '{n} listings'],
      'catalog.empty_title': 'No listings found',
      'catalog.empty_text': 'Try another search or change the filters',
      'common.loading': 'Loading…',
      'common.retry': 'Try again',
      'common.close': 'Close',
      'common.load_failed': "Couldn't load",
      'toast.retry': 'Retry',
      'tabs.label': 'Sections',
      'tabs.catalog': 'Homes',
      'tabs.favs': 'Favorites',
      'tabs.add': 'Post',
      'tabs.profile': 'Profile',
      'type.rent': 'For rent',
      'type.sale': 'For sale',
      'status.pending': 'Under review',
      'status.approved': 'Active',
      'status.rejected': 'Rejected',
      'status.archived': 'Archived',
      'title.rooms': '{n}-room',
      'title.apartment': '{n}-room apartment',
      'title.area': '{n} m²',
      'title.floor_of': 'floor {floor}/{total}',
      'title.floor': 'floor {floor}',
      'title.total_floors': '{n} floors',
      'meta.rooms': ['{n} room', '{n} rooms'],
      'city': 'Chirchiq',
      'date.today': 'today',
      'date.yesterday': 'yesterday',
      'date.days': ['{n} day ago', '{n} days ago'],
      'date.weeks': ['{n} week ago', '{n} weeks ago'],
      'date.months': ['{n} month ago', '{n} months ago'],
      'date.years': ['{n} year ago', '{n} years ago'],
      'err.status': 'Error: {n}',
      'err.generic': 'Error',
      'err.401': 'Authorization required',
      'err.404': 'Listing not found',
      'err.500': 'Server error, please try again later',
      'err.network': 'Network error. Check your internet connection',
      'detail.label': 'Listing',
      'detail.map': 'View on map',
      'tag.rent': 'Rent',
      'tag.sale': 'Sale',
      'tag.new': 'New',
      'spec.rooms': 'rooms',
      'spec.area': 'm²',
      'spec.floor': 'floor',
      'photos.count': ['{n} photo', '{n} photos'],
      'detail.info': 'Details',
      'detail.description': 'Description',
      'detail.rooms': 'Rooms',
      'detail.area': 'Area',
      'detail.floor': 'Floor',
      'detail.total_floors': 'Building floors',
      'detail.district': 'District',
      'detail.address': 'Address',
      'detail.number': 'Listing number',
      'detail.date': 'Date',
      'detail.owner': 'Posted by',
      'detail.views': ['{n} view', '{n} views'],
      'detail.contacts': ['{n} inquiry', '{n} inquiries'],
      'gallery.prev': 'Previous photo',
      'gallery.next': 'Next photo',
      'fav.add': 'Add to favorites',
      'fav.remove': 'Remove from favorites',
      'favs.title': 'Favorites',
      'favs.count': '{n}',
      'favs.empty_title': 'No favorites yet',
      'favs.empty_text': 'Tap ♡ on a listing card to save it here',
      'favs.go_catalog': 'Browse listings',
      'action.delete': 'Delete',
      'action.contact': 'Contact',
      'contact.title': 'Contact',
      'contact.call': 'Call',
      'contact.copy': 'Copy',
      'contact.copied': 'Number copied',
      'contact.copy_failed': "Couldn't copy",
      'contact.outside': 'Open the app inside Telegram to see the phone number',
      'contact.outside_no_user': 'To see the phone number, reopen the app with the “{app}” button next to the message field',
      'delete.confirm': 'Delete listing #{id}? This cannot be undone.',
      'delete.done': 'Listing deleted',
      'delete.forbidden': "This listing doesn't belong to you",
      'app.only_in_telegram': 'This button works only inside Telegram',
      'add.title': 'Post a listing',
      'add.lead': 'Your listing goes live in 3 steps',
      'add.note': 'Only listings in Chirchiq city are accepted',
      'add.step1_title': 'Open the bot',
      'add.step1_text': 'The button below opens @' + BOT_USERNAME,
      'add.step2_title': 'Fill in the details',
      'add.step2_text': 'Type, rooms, price, address and photos',
      'add.step3_title': 'Wait for review',
      'add.step3_text': 'Once approved, the listing appears in the catalog',
      'add.button': 'Post a listing',
      'add.foot': 'The button opens the add-listing flow in the bot',
      'profile.title': 'Profile',
      'profile.registered': 'Registered',
      'profile.not_registered': 'Not registered',
      'profile.no_phone': 'No phone number',
      'profile.guest': 'User',
      'profile.language': 'Language',
      'profile.open_bot': 'Open the bot',
      'my.title': 'My listings',
      'my.refresh': 'Refresh',
      'my.reopen_title': 'Reopen the app',
      'my.reopen_text': 'To use this section, open the app with the “{view}” button in the bot or the “{app}” button next to the message field',
      'my.only_tg_title': 'This section works only inside Telegram',
      'my.only_tg_text': 'Open the app from the Telegram bot to see your profile and listings',
      'my.to_bot': 'Go to the bot',
      'my.not_registered_title': "You're not registered",
      'my.not_registered_text': 'To add a listing, tap “{register}” in the bot',
      'my.empty_title': 'You have no listings yet',
      'my.empty_text': 'Add your first listing via the bot',
      'my.add_title': 'Add a new listing',
      'my.add_text': 'Post a new listing with the “{add}” button in the bot',
      'bot.view_listings': '📱 View listings',
      'bot.app_menu': 'App',
      'bot.register': '📝 Register',
      'bot.add_listing': '➕ Add listing'
    }
  };

  function normalizeLang(code) {
    code = String(code || '').trim().toLowerCase();
    if (code.indexOf('ru') === 0) return 'ru';
    if (code.indexOf('en') === 0) return 'en';
    return 'uz';
  }
  function exactLang(code) {
    code = String(code || '').trim().toLowerCase().slice(0, 2);
    return LANGS.indexOf(code) >= 0 ? code : '';
  }
  function storageGet(store) {
    try { return window[store].getItem(LANG_KEY) || ''; } catch (e) { return ''; }
  }
  function storageSet(store, value) {
    try { window[store].setItem(LANG_KEY, value); } catch (e) { /* storage unavailable */ }
  }
  function telegramLanguageCode() {
    return (TG_USER && TG_USER.language_code) ? String(TG_USER.language_code) : '';
  }
  function detectLang() {
    var fromUrl = '';
    try { fromUrl = exactLang(new URLSearchParams(location.search).get('lang')); } catch (e) { fromUrl = ''; }
    if (fromUrl) {
      storageSet('sessionStorage', fromUrl);
      storageSet('localStorage', fromUrl);
      return fromUrl;
    }
    var remembered = exactLang(storageGet('sessionStorage')) || exactLang(storageGet('localStorage'));
    if (remembered) return remembered;
    var code = telegramLanguageCode();
    return code ? normalizeLang(code) : 'uz';
  }

  var LANG = detectLang();

  function pluralForm(forms, n) {
    if (!Array.isArray(forms)) return forms;
    n = Math.abs(Math.floor(Number(n) || 0));
    if (LANG === 'ru' && forms.length >= 3) {
      var m10 = n % 10, m100 = n % 100;
      if (m10 === 1 && m100 !== 11) return forms[0];
      if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return forms[1];
      return forms[2];
    }
    return n === 1 ? forms[0] : forms[forms.length - 1];
  }

  // T('catalog.count', { n: 5 }) -> "5 ta e'lon"
  function T(key, vars) {
    var dict = I18N[LANG] || I18N.uz;
    var val = Object.prototype.hasOwnProperty.call(dict, key) ? dict[key] : I18N.uz[key];
    if (val === undefined || val === null) val = key;
    val = pluralForm(val, vars && vars.n);
    if (vars) {
      val = String(val).replace(/\{(\w+)\}/g, function (all, name) {
        return Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : all;
      });
    }
    return String(val);
  }

  function applyStaticI18n() {
    try { document.documentElement.setAttribute('lang', LANG); } catch (e) { /* ignore */ }
    var each = function (attr, fn) {
      Array.prototype.forEach.call(document.querySelectorAll('[' + attr + ']'), function (el) {
        fn(el, T(el.getAttribute(attr)));
      });
    };
    each('data-i18n', function (el, text) { el.textContent = text; });
    each('data-i18n-aria', function (el, text) { el.setAttribute('aria-label', text); });
    each('data-i18n-title', function (el, text) { el.setAttribute('title', text); });
    each('data-i18n-placeholder', function (el, text) { el.setAttribute('placeholder', text); });
  }

  function msgOutside() {
    return inTelegramNoUser
      ? T('contact.outside_no_user', { app: T('bot.app_menu') })
      : T('contact.outside');
  }

  function haptic(kind, style) {
    try {
      if (!tg || !tg.HapticFeedback) return;
      if (kind === 'impact') tg.HapticFeedback.impactOccurred(style || 'light');
      else if (kind === 'notification') tg.HapticFeedback.notificationOccurred(style || 'success');
      else tg.HapticFeedback.selectionChanged();
    } catch (e) { /* older clients */ }
  }

  function applyColorScheme() {
    var scheme = tg && tg.colorScheme;
    if (scheme === 'dark' || scheme === 'light') {
      document.documentElement.setAttribute('data-theme', scheme);
    }
  }

  function setupTelegram() {
    if (!tg) return;
    try { tg.ready(); } catch (e) { /* ignore */ }
    try { tg.expand(); } catch (e) { /* ignore */ }
    try { tg.setHeaderColor('bg_color'); } catch (e) { /* ignore */ }
    try { tg.setBackgroundColor('bg_color'); } catch (e) { /* ignore */ }
    applyColorScheme();
    try { tg.onEvent('themeChanged', applyColorScheme); } catch (e) { /* ignore */ }
    try { tg.BackButton.onClick(closeTopLayer); } catch (e) { /* ignore */ }
  }

  function closeApp() {
    if (tg && typeof tg.close === 'function') {
      try { tg.close(); return; } catch (e) { /* ignore */ }
    }
    showToast(T('app.only_in_telegram'));
  }

  // Opens a t.me link: inside Telegram through the client (and closes the mini app),
  // outside Telegram as a normal navigation. `ev` is the click event of an <a>.
  function openBotLink(url, ev) {
    if (tg && typeof tg.openTelegramLink === 'function') {
      if (ev) ev.preventDefault();
      haptic('impact', 'medium');
      try { tg.openTelegramLink(url); } catch (e) { /* fall through to close */ }
      try { tg.close(); } catch (e) { /* ignore */ }
      return;
    }
    if (ev) return; // let the <a> navigate
    try { window.open(url, '_blank', 'noopener'); } catch (e) { location.href = url; }
  }

  function confirmDialog(message, cb) {
    if (tg && typeof tg.showConfirm === 'function') {
      try { tg.showConfirm(message, cb); return; } catch (e) { /* unsupported version */ }
    }
    cb(window.confirm(message));
  }

  // =====================================================================
  // State
  // =====================================================================
  var DEFAULT_FILTERS = { type: 'all', rooms: null, currency: null, min_price: null, max_price: null, sort: 'new', q: '' };
  var TABS = ['catalog', 'favs', 'add', 'profile'];

  var state = {
    tab: 'catalog',
    filters: Object.assign({}, DEFAULT_FILTERS),
    catalog: { items: [], total: 0, offset: 0, limit: 12, loading: false, loaded: false, error: null, rendered: 0, requestId: 0, controller: null },
    favs: { items: [], loading: false, loaded: false, error: null, dirty: true, requestId: 0 },
    my: { items: [], registered: null, loading: false, loaded: false, error: null },
    me: { data: null, loading: false, loaded: false, error: null },
    detail: null, // { listing, source: 'catalog' | 'favs' | 'my' }
    scroll: { catalog: 0, favs: 0, add: 0, profile: 0 }
  };

  // =====================================================================
  // DOM helpers
  // =====================================================================
  function $(id) { return document.getElementById(id); }

  function h(tag, props) {
    var el = document.createElement(tag);
    if (props) {
      Object.keys(props).forEach(function (key) {
        var val = props[key];
        if (val === null || val === undefined || val === false) return;
        if (key === 'class') el.className = val;
        else if (key === 'text') el.textContent = String(val);
        else if (key === 'style' && typeof val === 'object') Object.assign(el.style, val);
        else if (key.indexOf('on') === 0 && typeof val === 'function') el.addEventListener(key.slice(2).toLowerCase(), val);
        else if (val === true) el.setAttribute(key, '');
        else el.setAttribute(key, String(val));
      });
    }
    for (var i = 2; i < arguments.length; i++) appendChild(el, arguments[i]);
    return el;
  }

  function appendChild(el, child) {
    if (child === null || child === undefined || child === false) return;
    if (Array.isArray(child)) { child.forEach(function (c) { appendChild(el, c); }); return; }
    if (child instanceof Node) el.appendChild(child);
    else el.appendChild(document.createTextNode(String(child)));
  }

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  function svgIcon(path, size) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('width', String(size || 22));
    svg.setAttribute('height', String(size || 22));
    svg.setAttribute('aria-hidden', 'true');
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('fill', 'currentColor');
    p.setAttribute('d', path);
    svg.appendChild(p);
    return svg;
  }
  var ICON_HEART = 'M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z';
  var ICON_CHECK = 'M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z';

  // Stroke ("line") icons: one or more path `d` strings in a 24x24 box.
  function lineIcon(paths, size, width) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('width', String(size || 20));
    svg.setAttribute('height', String(size || 20));
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', String(width || 2));
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    (Array.isArray(paths) ? paths : [paths]).forEach(function (d) {
      var p = document.createElementNS(ns, 'path');
      p.setAttribute('d', d);
      svg.appendChild(p);
    });
    return svg;
  }
  var LI = {
    prev: 'm15 18-6-6 6-6',
    next: 'm9 18 6-6-6-6',
    eye: ['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
    phone: 'M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z',
    clock: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z', 'M12 7v5l3 2'],
    image: ['M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z', 'M8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z', 'm21 15-5-5L5 21'],
    pin: ['M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z', 'M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
    map: ['m1 6 7-4 8 4 7-4v16l-7 4-8-4-7 4z', 'M8 2v16', 'M16 6v16'],
    trash: ['M3 6h18', 'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2', 'm19 6-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6', 'M10 11v6', 'M14 11v6'],
    copy: ['M20 9h-9a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2z', 'M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'],
    house: ['M3 10.5 12 3l9 7.5', 'M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5'],
    door: ['M3 21h18', 'M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16', 'M14 12h.01'],
    area: ['M8 3H5a2 2 0 0 0-2 2v3', 'M21 8V5a2 2 0 0 0-2-2h-3', 'M3 16v3a2 2 0 0 0 2 2h3', 'M16 21h3a2 2 0 0 0 2-2v-3'],
    layers: ['m12 2 10 5-10 5L2 7l10-5z', 'm2 17 10 5 10-5', 'm2 12 10 5 10-5'],
    send: ['m22 2-11 13', 'm22 2-7 20-4-9-9-4z'],
    plus: 'M12 5v14M5 12h14',
    hash: ['M4 9h16', 'M4 15h16', 'M10 3 8 21', 'M16 3l-2 18'],
    calendar: ['M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z', 'M16 2v4', 'M8 2v4', 'M3 10h18'],
    user: ['M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z']
  };

  // Small inline illustrations for empty / error / info states (no emoji).
  var ILLUS = {
    search: ['M27 44a16 16 0 1 0 0-32 16 16 0 0 0 0 32z', 'm38.5 39.5 13 13', 'M20 30v-6l7-5 7 5v6h-4v-5h-6v5z'],
    heart: ['M32 52s-18-10.5-18-23A9.5 9.5 0 0 1 32 23a9.5 9.5 0 0 1 18 6c0 12.5-18 23-18 23z'],
    error: ['M32 54a22 22 0 1 0 0-44 22 22 0 0 0 0 44z', 'M24 40c2-3 5-4 8-4s6 1 8 4', 'M24 26h.5', 'M39.5 26h.5'],
    phone: ['M22 8h20a3 3 0 0 1 3 3v42a3 3 0 0 1-3 3H22a3 3 0 0 1-3-3V11a3 3 0 0 1 3-3z', 'M28 13h8', 'M32 50h.5'],
    refresh: ['M52 32a20 20 0 1 1-6-14.3', 'M52 12v10h-10'],
    doc: ['M20 10h18l10 10v34a2 2 0 0 1-2 2H20a2 2 0 0 1-2-2V12a2 2 0 0 1 2-2z', 'M38 10v10h10', 'M26 32h12', 'M26 40h12'],
    folder: ['M10 20a3 3 0 0 1 3-3h12l5 5h21a3 3 0 0 1 3 3v22a3 3 0 0 1-3 3H13a3 3 0 0 1-3-3z', 'M10 30h44']
  };
  function illustration(kind) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'illus');
    svg.setAttribute('viewBox', '0 0 64 64');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('aria-hidden', 'true');
    var bg = document.createElementNS(ns, 'circle');
    bg.setAttribute('class', 'soft');
    bg.setAttribute('cx', '32'); bg.setAttribute('cy', '32'); bg.setAttribute('r', '32');
    svg.appendChild(bg);
    (ILLUS[kind] || ILLUS.folder).forEach(function (d) {
      var p = document.createElementNS(ns, 'path');
      p.setAttribute('d', d);
      p.setAttribute('stroke', 'currentColor');
      p.setAttribute('stroke-width', '2.4');
      p.setAttribute('stroke-linecap', 'round');
      p.setAttribute('stroke-linejoin', 'round');
      svg.appendChild(p);
    });
    return svg;
  }

  // =====================================================================
  // Formatting helpers
  // =====================================================================
  function digitsOnly(s) { return String(s || '').replace(/\D+/g, ''); }
  function groupNumber(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function formatNum(x) {
    var n = Number(x);
    if (!isFinite(n)) return String(x);
    return String(Math.round(n * 10) / 10);
  }
  function priceLabel(digits, currency) {
    if (!digits) return '';
    var g = groupNumber(digits.replace(/^0+(?=\d)/, ''));
    return currency === 'USD' ? '$' + g : g + ' ' + T('cur.som');
  }
  // Client dictionary first (same language as the UI), the API's localized text as a fallback
  function knownText(key, fallback) { var v = T(key); return v !== key ? v : (fallback || ''); }
  function typeText(l) { return knownText('type.' + l.type, l.type_text); }
  function statusText(l) { return knownText('status.' + l.status, l.status_text); }

  // "2 xonali · 55 m² · 3/9 qavat"
  function listingTitle(l) {
    var parts = [T('title.rooms', { n: l.rooms })];
    if (l.area) parts.push(T('title.area', { n: formatNum(l.area) }));
    if (l.floor && l.total_floors) parts.push(T('title.floor_of', { floor: l.floor, total: l.total_floors }));
    else if (l.floor) parts.push(T('title.floor', { floor: l.floor }));
    else if (l.total_floors) parts.push(T('title.total_floors', { n: l.total_floors }));
    return parts.join(' · ');
  }

  // The API sends `title` (first line of the description); older responses may not,
  // so the same rule is applied here as a fallback.
  var LEADING_SYMBOLS;
  try { LEADING_SYMBOLS = new RegExp('^[^\\p{L}\\p{N}]+', 'u'); }
  catch (e) { LEADING_SYMBOLS = /^[^A-Za-z0-9Ѐ-ӿ]+/; }
  function cardTitle(l) {
    if (typeof l.title === 'string' && l.title.trim()) return l.title.trim();
    var first = String(l.description || '').split(/\r?\n/)[0] || '';
    first = first.replace(LEADING_SYMBOLS, '').replace(/\s+/g, ' ').trim();
    if (first.length > 70) {
      var cut = first.slice(0, 70), sp = cut.lastIndexOf(' ');
      first = (sp > 30 ? cut.slice(0, sp) : cut).replace(/[\s,.;:–-]+$/, '') + '…';
    }
    return first || T('title.apartment', { n: l.rooms });
  }

  // "Chirchiq, 8-mikrorayon, 12-uy" -> "8-mikrorayon" (fallback when the API has no area_name)
  function areaFromAddress(addr) {
    var m = /^\s*(?:chirchiq|чирчик)\s*,\s*([^,]+)/i.exec(String(addr || ''));
    return m ? m[1].trim() : '';
  }
  // "2 xona · 55 m² · Chirchiq, 8-mikrorayon"
  function metaLine(l) {
    var parts = [T('meta.rooms', { n: l.rooms })];
    if (l.area) parts.push(T('title.area', { n: formatNum(l.area) }));
    var loc = (typeof l.city === 'string' && l.city) ? l.city : T('city');
    var area = l.area_name || areaFromAddress(l.address) || l.district || '';
    if (area) loc += ', ' + area;
    parts.push(loc);
    return parts.join(' · ');
  }

  function parseDate(iso) {
    if (!iso) return null;
    var s = String(iso);
    if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(s)) s += 'Z'; // naive timestamps are UTC
    var d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }
  function startOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime(); }
  function relativeDate(iso) {
    var d = parseDate(iso);
    if (!d) return '';
    var days = Math.round((startOfDay(new Date()) - startOfDay(d)) / 86400000);
    if (days <= 0) return T('date.today');
    if (days === 1) return T('date.yesterday');
    if (days < 7) return T('date.days', { n: days });
    if (days < 30) return T('date.weeks', { n: Math.floor(days / 7) });
    if (days < 365) return T('date.months', { n: Math.floor(days / 30) });
    return T('date.years', { n: Math.floor(days / 365) });
  }
  function fullDate(iso) {
    var d = parseDate(iso);
    if (!d) return '';
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + d.getFullYear();
  }

  // Price text comes from the API; split the per-month suffix (" / oy", " / мес", " / month")
  // for lighter styling.
  function priceNode(l, cls) {
    var text = l.price_text || '';
    var m = /^(.*?)\s*\/\s*(oy|мес|month)$/.exec(text);
    var el = h('div', { class: cls });
    if (m) {
      el.appendChild(document.createTextNode(m[1] + ' '));
      el.appendChild(h('span', { class: 'per', text: '/ ' + m[2] }));
    } else {
      el.textContent = text;
    }
    return el;
  }

  function photoUrl(url, priv) {
    url = String(url || '');
    if (API_BASE && url.charAt(0) === '/') url = API_BASE + url;
    if (priv && initData) {
      return url + (url.indexOf('?') >= 0 ? '&' : '?') + 'init_data=' + encodeURIComponent(initData);
    }
    return url;
  }

  // =====================================================================
  // API
  // =====================================================================
  function ApiError(status, message) {
    this.status = status; // -1 = aborted, 0 = network
    this.message = message;
  }
  ApiError.prototype = Object.create(Error.prototype);

  function withLang(path) {
    return path + (path.indexOf('?') >= 0 ? '&' : '?') + 'lang=' + encodeURIComponent(LANG);
  }

  function api(path, options) {
    options = options || {};
    var headers = Object.assign({ 'Accept': 'application/json', 'X-Lang': LANG }, options.headers || {});
    if (initData) headers['X-Telegram-Init-Data'] = initData;
    var opts = Object.assign({}, options, { headers: headers });
    return fetch(API_BASE + withLang(path), opts).then(function (res) {
      return res.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = null; }
        if (!res.ok) {
          var msg = (data && typeof data.error === 'string') ? data.error : T('err.status', { n: res.status });
          if (res.status === 401) msg = T('err.401');
          else if (res.status === 404) msg = T('err.404');
          else if (res.status >= 500) msg = T('err.500');
          throw new ApiError(res.status, msg);
        }
        return data;
      });
    }).catch(function (err) {
      if (err instanceof ApiError) throw err;
      if (err && err.name === 'AbortError') throw new ApiError(-1, '');
      throw new ApiError(0, T('err.network'));
    });
  }

  function newController() {
    try { return ('AbortController' in window) ? new AbortController() : null; } catch (e) { return null; }
  }

  // =====================================================================
  // Toast
  // =====================================================================
  var toastTimer = null;
  function showToast(text, opts) {
    opts = opts || {};
    var toast = $('toast');
    var action = $('toast-action');
    $('toast-text').textContent = text;
    action.hidden = !opts.retry;
    action.onclick = opts.retry ? function () { hideToast(); opts.retry(); } : null;
    toast.classList.toggle('is-high', !!state.detail || isSheetOpen());
    toast.hidden = false;
    // force reflow so the transition runs
    void toast.offsetWidth;
    toast.classList.add('is-visible');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(hideToast, opts.retry ? 6000 : 3200);
  }
  function hideToast() {
    var toast = $('toast');
    toast.classList.remove('is-visible');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.hidden = true; }, 220);
  }

  // =====================================================================
  // Layers (detail overlay / bottom sheet) + BackButton + history
  // =====================================================================
  var layers = []; // [{ name, close }]

  function updateChrome() {
    document.body.classList.toggle('is-locked', layers.length > 0);
    if (!tg || !tg.BackButton) return;
    try {
      if (layers.length) tg.BackButton.show(); else tg.BackButton.hide();
    } catch (e) { /* ignore */ }
  }

  function openLayer(name, closeFn) {
    layers.push({ name: name, close: closeFn });
    try { history.pushState({ layer: name, depth: layers.length }, ''); } catch (e) { /* ignore */ }
    updateChrome();
  }

  function popLayer() {
    var top = layers.pop();
    if (top) top.close();
    updateChrome();
  }

  function historyDepth() {
    var st = history.state;
    return (st && typeof st.depth === 'number') ? st.depth : 0;
  }

  // User-initiated close of the `count` topmost layers.
  function closeLayers(count) {
    count = Math.min(count, layers.length);
    if (count <= 0) return;
    if (historyDepth() === layers.length) {
      history.go(-count); // popstate handler pops the layers
    } else {
      for (var i = 0; i < count; i++) popLayer();
    }
  }

  function closeTopLayer() { closeLayers(1); }

  window.addEventListener('popstate', function () {
    var depth = historyDepth();
    while (layers.length > depth) popLayer();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && layers.length) closeTopLayer();
  });

  // =====================================================================
  // Bottom sheet (generic)
  // =====================================================================
  function isSheetOpen() { return !$('sheet').hidden; }

  function openSheet(title, bodyEl) {
    var sheet = $('sheet');
    $('sheet-title').textContent = title;
    var body = $('sheet-body');
    clear(body);
    body.appendChild(bodyEl);
    sheet.hidden = false;
    void sheet.offsetWidth;
    sheet.classList.add('is-open');
    openLayer('sheet', function () {
      sheet.classList.remove('is-open');
      setTimeout(function () { if (!sheet.classList.contains('is-open')) sheet.hidden = true; }, 260);
    });
  }

  function closeSheet() {
    if (layers.length && layers[layers.length - 1].name === 'sheet') closeTopLayer();
  }

  // =====================================================================
  // Favorites (client-side, localStorage)
  //   ck_favs       = [{ id, savedAt }]   newest first
  //   ck_favs_cache = { id: listing }      shown until the fresh data arrives
  // =====================================================================
  var FAV_KEY = 'ck_favs';
  var FAV_CACHE_KEY = 'ck_favs_cache';
  var FAV_MAX = 200;

  function readJSON(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) { return fallback; }
  }
  function writeJSON(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* quota / private mode */ }
  }

  var favList = (function () {
    var raw = readJSON(FAV_KEY, []);
    var seen = {}, out = [];
    if (Array.isArray(raw)) {
      raw.forEach(function (f) {
        var id = f && typeof f === 'object' ? Number(f.id) : Number(f);
        if (!isFinite(id) || id <= 0 || seen[id]) return;
        seen[id] = true;
        out.push({ id: id, savedAt: (f && typeof f.savedAt === 'number') ? f.savedAt : Date.now() });
      });
    }
    return out.slice(0, FAV_MAX);
  })();
  var favCache = (function () {
    var raw = readJSON(FAV_CACHE_KEY, {});
    return (raw && typeof raw === 'object' && !Array.isArray(raw)) ? raw : {};
  })();

  function favIds() { return favList.map(function (f) { return f.id; }); }
  function isFav(id) {
    id = Number(id);
    for (var i = 0; i < favList.length; i++) if (favList[i].id === id) return true;
    return false;
  }
  function slimListing(l) {
    var copy = {};
    Object.keys(l).forEach(function (k) {
      if (k === 'description' || k === 'phone_number' || k === 'contact_name') return;
      copy[k] = l[k];
    });
    return copy;
  }
  function persistFavs() {
    favList = favList.slice(0, FAV_MAX);
    var keep = {};
    favList.forEach(function (f) { keep[f.id] = true; });
    Object.keys(favCache).forEach(function (k) { if (!keep[k]) delete favCache[k]; });
    writeJSON(FAV_KEY, favList);
    writeJSON(FAV_CACHE_KEY, favCache);
  }

  function toggleFav(l) {
    var id = Number(l.id);
    var on = !isFav(id);
    if (on) {
      favList.unshift({ id: id, savedAt: Date.now() });
      favCache[id] = slimListing(l);
    } else {
      favList = favList.filter(function (f) { return f.id !== id; });
      delete favCache[id];
    }
    persistFavs();
    haptic('impact', on ? 'medium' : 'light');
    updateFavButtons(id, on);
    state.favs.dirty = true;
    if (state.tab === 'favs') syncFavsFromStore();
    renderFavsCount();
  }

  function updateFavButtons(id, on) {
    Array.prototype.forEach.call(document.querySelectorAll('[data-fav-id="' + id + '"]'), function (btn) {
      btn.classList.toggle('is-on', on);
      btn.setAttribute('aria-pressed', String(on));
      btn.setAttribute('aria-label', T(on ? 'fav.remove' : 'fav.add'));
      btn.classList.remove('is-pop');
      void btn.offsetWidth;
      if (on) btn.classList.add('is-pop');
    });
  }

  function favButton(l) {
    var on = isFav(l.id);
    var btn = h('button', {
      type: 'button',
      class: 'fav-btn' + (on ? ' is-on' : ''),
      'data-fav-id': String(l.id),
      'aria-pressed': String(on),
      'aria-label': T(on ? 'fav.remove' : 'fav.add')
    }, svgIcon(ICON_HEART, 22));
    btn.addEventListener('click', function (e) { e.stopPropagation(); e.preventDefault(); toggleFav(l); });
    btn.addEventListener('keydown', function (e) { e.stopPropagation(); });
    return btn;
  }

  // =====================================================================
  // Cards
  // =====================================================================
  function placeholderMedia(media) {
    media.classList.add('is-placeholder');
    media.appendChild(h('div', { class: 'media-placeholder' }, lineIcon(LI.house, 36, 1.8)));
  }

  // Photo (or placeholder) for a card / row; `media` gets the img and the error fallback.
  function fillMedia(media, l, priv, imgClass) {
    if (l.photos && l.photos.length) {
      var img = h('img', { class: imgClass, src: photoUrl(l.photos[0], priv), alt: '', loading: 'lazy', decoding: 'async' });
      img.addEventListener('error', function () { if (!media.classList.contains('is-placeholder')) placeholderMedia(media); });
      media.appendChild(img);
    } else {
      placeholderMedia(media);
    }
  }

  function isNewListing(l) {
    var d = parseDate(l.created_at);
    return !!d && (Date.now() - d.getTime()) < 48 * 3600 * 1000;
  }

  function statNode(icon, text, cls) {
    return h('span', { class: cls || 'card-stat' }, lineIcon(icon, 14), h('span', { text: String(text) }));
  }

  function buildCard(l, source) {
    var priv = source === 'my';
    var media = h('div', { class: 'card-media' });
    fillMedia(media, l, priv, 'card-img');
    if (l.photos && l.photos.length > 1) {
      media.appendChild(h('span', { class: 'card-count', 'aria-label': T('photos.count', { n: l.photos.length }) },
        lineIcon(LI.image, 12), h('span', { text: String(l.photos.length) })));
    }
    var tags = h('div', { class: 'card-tags' }, h('span', { class: 'tag tag-' + l.type, text: knownText('tag.' + l.type, typeText(l)) }));
    if (priv) tags.appendChild(h('span', { class: 'tag tag-status tag-' + l.status, text: statusText(l) }));
    else if (isNewListing(l)) tags.appendChild(h('span', { class: 'tag tag-new', text: T('tag.new') }));
    media.appendChild(tags);
    if (!priv) media.appendChild(favButton(l));

    var footer = h('div', { class: 'card-footer' }, statNode(LI.eye, l.view_count || 0));
    if (priv) footer.appendChild(statNode(LI.phone, l.contact_count || 0));
    footer.appendChild(h('span', { class: 'card-date', text: relativeDate(l.created_at) }));

    var body = h('div', { class: 'card-body' },
      priceNode(l, 'card-price'),
      h('div', { class: 'card-title', text: cardTitle(l) }),
      h('div', { class: 'card-meta', text: metaLine(l) }),
      footer);

    var card = h('article', { class: 'card card-link', role: 'button', tabindex: '0', 'data-id': String(l.id) }, media, body);

    var open = function () { haptic('impact', 'light'); openDetail(l, source); };
    card.addEventListener('click', open);
    card.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
    });
    return card;
  }

  // "Mening e'lonlarim": compact list row with thumb, price, status pill and a trash button.
  function buildMyRow(l) {
    var thumb = h('div', { class: 'row-thumb' });
    fillMedia(thumb, l, true, 'row-img');

    var meta = h('div', { class: 'row-meta' },
      h('span', { text: relativeDate(l.created_at) }),
      statNode(LI.eye, l.view_count || 0),
      statNode(LI.phone, l.contact_count || 0));
    var main = h('div', { class: 'row-main' },
      priceNode(l, 'row-price'),
      h('div', { class: 'row-title', text: cardTitle(l) }),
      meta);

    var del = h('button', { type: 'button', class: 'icon-btn row-del', 'aria-label': T('action.delete'), title: T('action.delete') }, lineIcon(LI.trash, 20));
    del.addEventListener('click', function (e) { e.stopPropagation(); deleteListing(l, del); });
    del.addEventListener('keydown', function (e) { e.stopPropagation(); });
    var side = h('div', { class: 'row-side' },
      h('span', { class: 'badge badge-' + l.status, text: statusText(l) }),
      del);

    var row = h('article', { class: 'row row-link', role: 'button', tabindex: '0', 'data-id': String(l.id) }, thumb, main, side);
    var open = function () { haptic('impact', 'light'); openDetail(l, 'my'); };
    row.addEventListener('click', open);
    row.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
    });
    return row;
  }

  function skeletonCard() {
    return h('div', { class: 'card skeleton', 'aria-hidden': 'true' },
      h('div', { class: 'sk sk-media' }),
      h('div', { class: 'card-body' },
        h('div', { class: 'sk sk-line tall' }),
        h('div', { class: 'sk sk-line w80' }),
        h('div', { class: 'sk sk-line w60' }),
        h('div', { class: 'sk sk-line w40' })));
  }
  function skeletonRow() {
    return h('div', { class: 'row skeleton', 'aria-hidden': 'true' },
      h('div', { class: 'sk sk-thumb' }),
      h('div', { class: 'row-main' },
        h('div', { class: 'sk sk-line tall' }),
        h('div', { class: 'sk sk-line w80' }),
        h('div', { class: 'sk sk-line w40' })));
  }

  // kind: search | heart | error | phone | refresh | doc | folder
  function stateCard(kind, title, text, button) {
    return h('div', { class: 'state' },
      illustration(kind),
      h('div', { class: 'state-title', text: title }),
      text ? h('div', { class: 'state-text', text: text }) : null,
      button || null);
  }

  // =====================================================================
  // Catalog
  // =====================================================================
  function buildQuery(f, offset, limit) {
    var p = new URLSearchParams();
    p.set('type', f.type || 'all');
    if (f.rooms) p.set('rooms', String(f.rooms)); // 1..6 or "4plus"
    if (f.currency) {
      p.set('currency', f.currency);
      if (f.min_price !== null && f.min_price !== undefined) p.set('min_price', String(f.min_price));
      if (f.max_price !== null && f.max_price !== undefined) p.set('max_price', String(f.max_price));
    }
    if (f.q) p.set('q', f.q);
    p.set('sort', f.sort || 'new');
    p.set('offset', String(offset));
    p.set('limit', String(limit));
    return p.toString();
  }

  function loadCatalog(reset) {
    var c = state.catalog;
    if (c.loading && !reset) return;
    if (reset) {
      if (c.controller) { try { c.controller.abort(); } catch (e) { /* ignore */ } }
      c.items = []; c.offset = 0; c.total = 0; c.loaded = false; c.rendered = 0;
    }
    c.error = null;
    c.loading = true;
    var reqId = ++c.requestId;
    var controller = newController();
    c.controller = controller;
    renderCatalog();
    api('/api/listings?' + buildQuery(state.filters, c.offset, c.limit), controller ? { signal: controller.signal } : {}).then(function (data) {
      if (reqId !== c.requestId) return;
      var items = (data && Array.isArray(data.items)) ? data.items : [];
      c.items = c.items.concat(items);
      c.total = (data && typeof data.total === 'number') ? data.total : c.items.length;
      c.offset = c.items.length;
      c.loaded = true;
      c.loading = false;
      c.controller = null;
      renderCatalog();
    }, function (err) {
      if (reqId !== c.requestId || err.status === -1) return;
      c.error = err.message || T('err.generic');
      c.loading = false;
      c.controller = null;
      renderCatalog();
      showToast(c.error, { retry: function () { loadCatalog(c.items.length === 0); } });
    });
  }

  function hasActiveQuery(f) {
    return !!(f.q || f.rooms || (f.type && f.type !== 'all') || f.currency);
  }

  function resetFilters() {
    state.filters = Object.assign({}, DEFAULT_FILTERS, { sort: state.filters.sort });
    var input = $('search-input');
    input.value = '';
    $('search-clear').hidden = true;
    renderChips();
    renderFilterBadge();
    window.scrollTo(0, 0);
    loadCatalog(true);
  }

  function renderCatalog() {
    var c = state.catalog;
    var list = $('catalog-list');
    var more = $('catalog-more');
    var moreBtn = $('catalog-more-btn');

    $('result-count').textContent = c.loaded ? T('catalog.count', { n: c.total }) : (c.loading ? T('common.loading') : '');
    renderFilterBadge();

    if (c.items.length === 0) {
      clear(list);
      c.rendered = 0;
      if (c.loading) {
        for (var i = 0; i < 4; i++) list.appendChild(skeletonCard());
      } else if (c.error) {
        var retry = h('button', { type: 'button', class: 'btn btn-secondary', text: T('common.retry') });
        retry.addEventListener('click', function () { loadCatalog(true); });
        list.appendChild(stateCard('error', T('common.load_failed'), c.error, retry));
      } else if (c.loaded) {
        var resetBtn = null;
        if (hasActiveQuery(state.filters)) {
          resetBtn = h('button', { type: 'button', class: 'btn btn-secondary', text: T('filter.reset') });
          resetBtn.addEventListener('click', resetFilters);
        }
        list.appendChild(stateCard('search', T('catalog.empty_title'), T('catalog.empty_text'), resetBtn));
      }
    } else {
      if (c.rendered > c.items.length) { clear(list); c.rendered = 0; }
      // drop skeletons / state cards if any
      if (c.rendered === 0) clear(list);
      for (var j = c.rendered; j < c.items.length; j++) list.appendChild(buildCard(c.items[j], 'catalog'));
      c.rendered = c.items.length;
    }

    var hasMore = c.items.length > 0 && c.items.length < c.total;
    more.hidden = !hasMore && !(c.loading && c.items.length > 0);
    clear(moreBtn);
    if (c.loading && c.items.length > 0) {
      moreBtn.disabled = true;
      moreBtn.appendChild(h('span', { class: 'spinner' }));
      moreBtn.appendChild(document.createTextNode(T('common.loading')));
    } else {
      moreBtn.disabled = false;
      moreBtn.textContent = T('catalog.more');
    }
  }

  // Filters that live only in the filter sheet (rooms have chips, sort has its own control)
  function activeFilterCount(f) {
    var n = 0;
    if (f.type && f.type !== 'all') n++;
    if (f.currency) n++;
    if (f.currency && f.min_price !== null) n++;
    if (f.currency && f.max_price !== null) n++;
    return n;
  }
  function renderFilterBadge() {
    var n = activeFilterCount(state.filters);
    $('filter-count').hidden = n === 0;
    $('filter-count').textContent = String(n);
    $('filter-btn').classList.toggle('is-active', n > 0);
  }

  function renderChips() {
    var current = state.filters.rooms === null || state.filters.rooms === undefined ? '' : String(state.filters.rooms);
    var row = $('rooms-chips');
    var activeChip = null;
    Array.prototype.forEach.call(row.querySelectorAll('.chip'), function (b) {
      var active = b.getAttribute('data-rooms') === current;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-pressed', active ? 'true' : 'false');
      if (active) activeChip = b;
    });
    // keep the active chip visible in the horizontally scrolling row
    if (activeChip) {
      try {
        var rr = row.getBoundingClientRect(), ar = activeChip.getBoundingClientRect();
        var delta = 0;
        if (ar.left < rr.left + 16) delta = ar.left - (rr.left + 16);
        else if (ar.right > rr.right - 28) delta = ar.right - (rr.right - 28);
        if (delta) row.scrollLeft += delta;
      } catch (e) { /* ignore */ }
    }
  }

  function renderSortLabel() {
    $('sort-label').textContent = T('sort.' + (state.filters.sort || 'new'));
  }

  var searchTimer = null;
  function applySearch() {
    if (searchTimer) { clearTimeout(searchTimer); searchTimer = null; }
    var q = $('search-input').value.replace(/\s+/g, ' ').trim().slice(0, 120);
    if (q === (state.filters.q || '')) return;
    state.filters.q = q;
    loadCatalog(true);
  }

  function setupSearch() {
    var input = $('search-input');
    var clearBtn = $('search-clear');
    input.addEventListener('input', function () {
      clearBtn.hidden = !input.value;
      if (searchTimer) clearTimeout(searchTimer);
      searchTimer = setTimeout(applySearch, 400);
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); applySearch(); input.blur(); }
      else if (e.key === 'Escape' && input.value) { input.value = ''; clearBtn.hidden = true; applySearch(); }
    });
    input.addEventListener('search', applySearch); // native clear / submit
    clearBtn.addEventListener('click', function () {
      input.value = '';
      clearBtn.hidden = true;
      haptic('impact', 'light');
      applySearch();
      input.focus();
    });
  }

  function setupCatalog() {
    $('rooms-chips').addEventListener('click', function (e) {
      var btn = e.target.closest('.chip');
      if (!btn) return;
      var raw = btn.getAttribute('data-rooms') || '';
      var next = raw === '' ? null : (raw === '4plus' ? '4plus' : parseInt(raw, 10));
      var cur = state.filters.rooms === null || state.filters.rooms === undefined ? null : state.filters.rooms;
      if (String(next) === String(cur)) return;
      state.filters.rooms = next;
      haptic('selection');
      renderChips();
      window.scrollTo(0, 0);
      loadCatalog(true);
    });
    $('filter-btn').addEventListener('click', openFilterSheet);
    $('sort-btn').addEventListener('click', openSortSheet);
    $('catalog-more-btn').addEventListener('click', function () { loadCatalog(false); });

    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var c = state.catalog;
          if (state.tab !== 'catalog' || c.loading || !c.loaded) return;
          if (c.items.length < c.total) loadCatalog(false);
        });
      }, { rootMargin: '400px 0px' });
      io.observe($('catalog-sentinel'));
    }
  }

  // =====================================================================
  // Sort sheet
  // =====================================================================
  function openSortSheet() {
    haptic('impact', 'light');
    var body = h('div', { class: 'options', role: 'menu' });
    ['new', 'cheap', 'expensive'].forEach(function (v) {
      var on = (state.filters.sort || 'new') === v;
      var btn = h('button', { type: 'button', class: 'option' + (on ? ' is-active' : ''), role: 'menuitemradio', 'aria-checked': String(on) },
        h('span', { text: T('sort.' + v) }), on ? svgIcon(ICON_CHECK, 20) : h('span', { class: 'option-radio', 'aria-hidden': 'true' }));
      btn.addEventListener('click', function () {
        haptic('selection');
        closeSheet();
        if (state.filters.sort === v) return;
        state.filters.sort = v;
        renderSortLabel();
        window.scrollTo(0, 0);
        loadCatalog(true);
      });
      body.appendChild(btn);
    });
    openSheet(T('sort.title'), body);
  }

  // =====================================================================
  // Filter sheet
  // =====================================================================
  function openFilterSheet() {
    haptic('impact', 'light');
    var draft = Object.assign({}, state.filters);

    // segmented = true renders a segmented control instead of a pill row (same behaviour)
    function chipGroup(options, getVal, setVal, allowNone, segmented) {
      var wrap = h('div', { class: segmented ? 'seg' : 'chips', role: 'group' });
      options.forEach(function (o) {
        var btn = h('button', { type: 'button', class: segmented ? 'seg-opt' : 'chip-opt', text: o.label, 'aria-pressed': String(getVal() === o.value) });
        btn.addEventListener('click', function () {
          var next = (allowNone && getVal() === o.value) ? null : o.value;
          setVal(next);
          haptic('selection');
          Array.prototype.forEach.call(wrap.children, function (ch, idx) {
            var on = options[idx].value === getVal();
            ch.classList.toggle('is-active', on);
            ch.setAttribute('aria-pressed', String(on));
          });
          if (wrap === currencyGroup) updatePriceHints();
        });
        if (getVal() === o.value) btn.classList.add('is-active');
        wrap.appendChild(btn);
      });
      return wrap;
    }

    var typeGroup = chipGroup(
      [{ value: 'all', label: T('seg.all') }, { value: 'rent', label: T('seg.rent') }, { value: 'sale', label: T('seg.sale') }],
      function () { return draft.type || 'all'; }, function (v) { draft.type = v || 'all'; }, false, true);

    var roomsGroup = chipGroup(
      [{ value: 1, label: '1' }, { value: 2, label: '2' }, { value: 3, label: '3' }, { value: '4plus', label: '4+' }],
      function () { return draft.rooms; }, function (v) { draft.rooms = v; }, true);

    var currencyGroup = chipGroup(
      [{ value: 'UZS', label: T('cur.som') }, { value: 'USD', label: '$' }],
      function () { return draft.currency; }, function (v) { draft.currency = v; }, true, true);

    function priceInput(placeholder, initial) {
      var input = h('input', { class: 'input', type: 'text', inputmode: 'numeric', autocomplete: 'off', placeholder: placeholder });
      var hint = h('div', { class: 'input-hint' });
      if (initial !== null && initial !== undefined) input.value = groupNumber(String(initial));
      input.addEventListener('input', function () {
        var d = digitsOnly(input.value).slice(0, 15);
        input.value = d ? groupNumber(d) : '';
        updateHint();
      });
      function updateHint() {
        var d = digitsOnly(input.value);
        hint.textContent = d ? priceLabel(d, draft.currency || 'UZS') : '';
      }
      updateHint();
      return { el: h('div', { class: 'input-wrap' }, input, hint), input: input, update: updateHint };
    }
    var minField = priceInput(T('price.from'), draft.min_price);
    var maxField = priceInput(T('price.to'), draft.max_price);
    var priceNote = h('div', { class: 'field-note' });
    function updatePriceHints() {
      minField.update(); maxField.update();
      priceNote.textContent = draft.currency ? '' : T('price.need_currency');
    }
    updatePriceHints();

    var body = h('div', null,
      h('div', { class: 'field' }, h('span', { class: 'field-label', text: T('filter.type') }), typeGroup),
      h('div', { class: 'field' }, h('span', { class: 'field-label', text: T('filter.rooms') }), roomsGroup),
      h('div', { class: 'field' }, h('span', { class: 'field-label', text: T('filter.currency') }), currencyGroup),
      h('div', { class: 'field' },
        h('span', { class: 'field-label', text: T('filter.price') }),
        h('div', { class: 'price-row' }, minField.el, maxField.el),
        priceNote));

    var applyBtn = h('button', { type: 'button', class: 'btn', text: T('filter.apply') });
    var clearBtn = h('button', { type: 'button', class: 'btn btn-secondary', text: T('filter.clear') });
    body.appendChild(h('div', { class: 'sheet-actions' }, clearBtn, applyBtn));

    function readPrice(field) {
      var d = digitsOnly(field.input.value);
      if (!d) return null;
      var n = parseInt(d, 10);
      return isFinite(n) && n > 0 ? n : null;
    }

    applyBtn.addEventListener('click', function () {
      var min = readPrice(minField), max = readPrice(maxField);
      if (min !== null && max !== null && min > max) { var t = min; min = max; max = t; }
      state.filters = Object.assign({}, state.filters, {
        type: draft.type || 'all',
        rooms: draft.rooms,
        currency: draft.currency,
        min_price: draft.currency ? min : null,
        max_price: draft.currency ? max : null
      });
      haptic('impact', 'medium');
      closeSheet();
      renderChips();
      window.scrollTo(0, 0);
      loadCatalog(true);
    });
    clearBtn.addEventListener('click', function () {
      state.filters = Object.assign({}, DEFAULT_FILTERS, { sort: state.filters.sort, q: state.filters.q });
      haptic('impact', 'light');
      closeSheet();
      renderChips();
      window.scrollTo(0, 0);
      loadCatalog(true);
    });

    openSheet(T('filter.title'), body);
  }

  // =====================================================================
  // Favorites view
  // =====================================================================
  function renderFavsCount() {
    var n = favIds().length;
    $('favs-count').textContent = n ? T('favs.count', { n: n }) : '';
  }

  // Rebuild the favorites grid from the store without a request (after a heart toggle).
  function syncFavsFromStore() {
    var f = state.favs;
    var byId = {};
    f.items.forEach(function (l) { byId[l.id] = l; });
    f.items = favIds().map(function (id) { return byId[id] || favCache[id] || null; }).filter(Boolean);
    renderFavs();
  }

  function loadFavs(force) {
    var f = state.favs;
    var ids = favIds();
    if (!ids.length) {
      f.items = []; f.loaded = true; f.loading = false; f.error = null; f.dirty = false;
      renderFavs();
      return;
    }
    if (f.loading) return;
    if (f.loaded && !f.dirty && !force) { renderFavs(); return; }

    // show the cached copies at once, then replace them with fresh data
    f.items = ids.map(function (id) { return favCache[id] || null; }).filter(Boolean);
    f.loading = true; f.error = null;
    renderFavs();

    var reqId = ++f.requestId;
    var chunks = [];
    for (var i = 0; i < ids.length; i += 50) chunks.push(ids.slice(i, i + 50));
    Promise.all(chunks.map(function (chunk) {
      return api('/api/listings/batch?ids=' + chunk.join(','));
    })).then(function (results) {
      if (reqId !== f.requestId) return;
      var byId = {};
      results.forEach(function (r) {
        if (r && Array.isArray(r.items)) r.items.forEach(function (l) { if (l && l.id) byId[Number(l.id)] = l; });
      });
      var fresh = [];
      favList = favList.filter(function (fav) {
        if (byId[fav.id]) { fresh.push(byId[fav.id]); favCache[fav.id] = slimListing(byId[fav.id]); return true; }
        if (ids.indexOf(fav.id) < 0) { // saved while the request was running
          if (favCache[fav.id]) fresh.push(favCache[fav.id]);
          return true;
        }
        return false; // no longer exists / not approved any more
      });
      persistFavs();
      f.items = fresh; f.loaded = true; f.loading = false; f.dirty = false;
      renderFavs();
      renderFavsCount();
    }, function (err) {
      if (reqId !== f.requestId || err.status === -1) return;
      f.loading = false;
      f.error = err.message || T('err.generic');
      renderFavs();
      showToast(f.error, { retry: function () { loadFavs(true); } });
    });
  }

  function renderFavs() {
    var f = state.favs;
    var list = $('favs-list');
    clear(list);
    renderFavsCount();

    if (!favIds().length) {
      var go = h('button', { type: 'button', class: 'btn btn-secondary', text: T('favs.go_catalog') });
      go.addEventListener('click', function () { switchTab('catalog'); });
      list.appendChild(stateCard('heart', T('favs.empty_title'), T('favs.empty_text'), go));
      return;
    }
    if (f.items.length === 0) {
      if (f.loading) {
        for (var i = 0; i < Math.min(4, favIds().length); i++) list.appendChild(skeletonCard());
      } else if (f.error) {
        var retry = h('button', { type: 'button', class: 'btn btn-secondary', text: T('common.retry') });
        retry.addEventListener('click', function () { loadFavs(true); });
        list.appendChild(stateCard('error', T('common.load_failed'), f.error, retry));
      } else {
        list.appendChild(stateCard('heart', T('favs.empty_title'), T('favs.empty_text')));
      }
      return;
    }
    f.items.forEach(function (l) { list.appendChild(buildCard(l, 'favs')); });
  }

  // =====================================================================
  // Detail view
  // =====================================================================
  function buildGallery(l, priv) {
    var photos = (l.photos || []).slice();
    if (!photos.length) {
      return h('div', { class: 'gallery is-placeholder' }, h('div', { class: 'media-placeholder' }, lineIcon(LI.house, 64, 1.5)));
    }
    var index = 0;
    var track = h('div', { class: 'gallery-track' });
    photos.forEach(function (url, i) {
      var img = h('img', { src: photoUrl(url, priv), alt: '', loading: i < 2 ? 'eager' : 'lazy', decoding: 'async', draggable: 'false' });
      track.appendChild(h('div', { class: 'gallery-slide' }, img));
    });
    var gallery = h('div', { class: 'gallery' }, track);
    var prev = null, next = null, dots = null, counter = null;
    if (photos.length > 1) {
      prev = h('button', { type: 'button', class: 'gallery-nav prev', 'aria-label': T('gallery.prev') }, lineIcon(LI.prev, 22, 2.2));
      next = h('button', { type: 'button', class: 'gallery-nav next', 'aria-label': T('gallery.next') }, lineIcon(LI.next, 22, 2.2));
      dots = h('div', { class: 'gallery-dots' });
      photos.forEach(function () { dots.appendChild(h('span', { class: 'gallery-dot' })); });
      counter = h('div', { class: 'gallery-counter' });
      gallery.appendChild(prev); gallery.appendChild(next); gallery.appendChild(dots); gallery.appendChild(counter);
      prev.addEventListener('click', function (e) { e.stopPropagation(); go(index - 1); });
      next.addEventListener('click', function (e) { e.stopPropagation(); go(index + 1); });
    }

    function go(i, silent) {
      index = Math.max(0, Math.min(photos.length - 1, i));
      track.classList.remove('no-anim');
      track.style.transform = 'translateX(' + (-index * 100) + '%)';
      if (dots) {
        Array.prototype.forEach.call(dots.children, function (d, k) { d.classList.toggle('is-active', k === index); });
      }
      if (counter) counter.textContent = (index + 1) + ' / ' + photos.length;
      if (prev) prev.disabled = index === 0;
      if (next) next.disabled = index === photos.length - 1;
      if (!silent) haptic('selection');
    }
    go(0, true);

    // touch swipe
    var startX = 0, startY = 0, dx = 0, dragging = false, horizontal = null;
    gallery.addEventListener('touchstart', function (e) {
      if (photos.length < 2 || e.touches.length !== 1) return;
      startX = e.touches[0].clientX; startY = e.touches[0].clientY;
      dx = 0; dragging = true; horizontal = null;
      track.classList.add('no-anim');
    }, { passive: true });
    gallery.addEventListener('touchmove', function (e) {
      if (!dragging) return;
      var x = e.touches[0].clientX - startX, y = e.touches[0].clientY - startY;
      if (horizontal === null && (Math.abs(x) > 6 || Math.abs(y) > 6)) horizontal = Math.abs(x) > Math.abs(y);
      if (!horizontal) return;
      dx = x;
      // resist at the edges
      if ((index === 0 && dx > 0) || (index === photos.length - 1 && dx < 0)) dx = dx / 3;
      track.style.transform = 'translateX(calc(' + (-index * 100) + '% + ' + dx + 'px))';
    }, { passive: true });
    function endTouch() {
      if (!dragging) return;
      dragging = false;
      var w = gallery.clientWidth || 1;
      if (horizontal && Math.abs(dx) > Math.max(40, w * 0.18)) go(index + (dx < 0 ? 1 : -1));
      else go(index, true);
    }
    gallery.addEventListener('touchend', endTouch);
    gallery.addEventListener('touchcancel', endTouch);

    gallery.keyHandler = function (e) {
      if (e.key === 'ArrowLeft') go(index - 1);
      else if (e.key === 'ArrowRight') go(index + 1);
    };
    return gallery;
  }

  var detailKeyHandler = null;

  function mapButton(l) {
    if (typeof l.latitude !== 'number' || typeof l.longitude !== 'number') return null;
    var url = 'https://yandex.uz/maps/?pt=' + l.longitude + ',' + l.latitude + '&z=17&l=map';
    var btn = h('button', { type: 'button', class: 'icon-btn addr-map', 'aria-label': T('detail.map'), title: T('detail.map') }, lineIcon(LI.map, 20));
    btn.addEventListener('click', function () {
      haptic('impact');
      if (tg && typeof tg.openLink === 'function') {
        try { tg.openLink(url); return; } catch (e) { /* fall through */ }
      }
      window.open(url, '_blank', 'noopener');
    });
    return btn;
  }

  function openDetail(l, source) {
    var priv = source === 'my';
    var detail = $('detail');
    var scroll = $('detail-scroll');
    var bar = $('detail-bar');
    clear(scroll); clear(bar);

    var gallery = buildGallery(l, priv);

    // heart in the header (public listings only)
    var favBtn = $('detail-fav');
    favBtn.hidden = priv;
    if (!priv) {
      var on = isFav(l.id);
      favBtn.setAttribute('data-fav-id', String(l.id));
      favBtn.classList.toggle('is-on', on);
      favBtn.classList.remove('is-pop');
      favBtn.setAttribute('aria-pressed', String(on));
      favBtn.setAttribute('aria-label', T(on ? 'fav.remove' : 'fav.add'));
      favBtn.onclick = function () { toggleFav(l); };
    } else {
      favBtn.removeAttribute('data-fav-id');
      favBtn.onclick = null;
    }

    var badges = h('div', { class: 'detail-badges' },
      h('span', { class: 'badge badge-' + l.type, text: typeText(l) }),
      priv ? h('span', { class: 'badge badge-' + l.status, text: statusText(l) }) : null,
      h('span', { class: 'badge badge-id', text: '#' + l.id }));

    // 3-tile spec strip: rooms / m² / floor
    function spec(icon, value, key, label) {
      return h('div', { class: 'spec', role: 'group', 'aria-label': label },
        lineIcon(icon, 22, 1.8),
        h('div', { class: 'spec-val', text: value }),
        h('div', { class: 'spec-key', text: key }));
    }
    var floorVal = (l.floor && l.total_floors) ? (l.floor + ' / ' + l.total_floors) : (l.floor ? String(l.floor) : (l.total_floors ? String(l.total_floors) : '—'));
    var strip = h('div', { class: 'spec-strip' },
      spec(LI.door, String(l.rooms), T('spec.rooms'), T('detail.rooms')),
      spec(LI.area, l.area ? formatNum(l.area) : '—', T('spec.area'), T('detail.area')),
      spec(LI.layers, floorVal, T('spec.floor'), T(l.floor ? 'detail.floor' : 'detail.total_floors')));

    var grid = h('dl', { class: 'detail-grid' });
    function row(label, value) {
      if (value === null || value === undefined || value === '') return;
      grid.appendChild(h('div', null, h('dt', { text: label }), h('dd', { text: String(value) })));
    }
    row(T('detail.district'), l.district || null);
    row(T('detail.number'), '#' + l.id);
    row(T('detail.date'), fullDate(l.created_at));
    if (l.owner_name) row(T('detail.owner'), l.owner_name);

    var viewsText = h('span', { text: T('detail.views', { n: l.view_count || 0 }) });
    var viewsEl = h('span', null, lineIcon(LI.eye, 15), viewsText);
    if (!priv) {
      // GET /api/listings/{id} counts the view and returns the fresh counter (best-effort)
      api('/api/listings/' + l.id).then(function (fresh) {
        if (!fresh || typeof fresh.view_count !== 'number') return;
        l.view_count = fresh.view_count;
        viewsText.textContent = T('detail.views', { n: fresh.view_count });
      }, function () { /* ignore: counting views must never break the detail view */ });
    }

    var title = cardTitle(l);
    var subtitle = listingTitle(l);
    var body = h('div', { class: 'detail-body' },
      priceNode(l, 'detail-price'),
      badges,
      h('h2', { class: 'detail-title', text: title }),
      title !== subtitle ? h('div', { class: 'detail-subtitle', text: subtitle }) : null,
      strip,
      h('div', { class: 'addr-row' },
        lineIcon(LI.pin, 20, 1.8),
        h('div', { class: 'addr-text', text: l.address || T('city') }),
        mapButton(l)),
      l.description ? h('div', { class: 'detail-section' },
        h('div', { class: 'detail-section-title', text: T('detail.description') }),
        h('p', { class: 'detail-desc', text: l.description })) : null,
      h('div', { class: 'detail-section' }, h('div', { class: 'detail-section-title', text: T('detail.info') }), grid),
      h('div', { class: 'detail-meta' },
        viewsEl,
        priv ? h('span', null, lineIcon(LI.phone, 15), h('span', { text: T('detail.contacts', { n: l.contact_count || 0 }) })) : null,
        h('span', null, lineIcon(LI.clock, 15), h('span', { text: relativeDate(l.created_at) }))));

    scroll.appendChild(h('div', { class: 'detail-inner' }, gallery, body));

    var barInner = h('div', { class: 'detail-bar-inner' });
    if (priv) {
      var del = h('button', { type: 'button', class: 'btn btn-danger' }, lineIcon(LI.trash, 20), h('span', { text: T('action.delete') }));
      del.addEventListener('click', function () { deleteListing(l, del); });
      barInner.appendChild(del);
    } else {
      var contact = h('button', { type: 'button', class: 'btn' }, lineIcon(LI.phone, 20), h('span', { text: T('action.contact') }));
      contact.addEventListener('click', function () { requestContact(l, contact); });
      barInner.appendChild(contact);
    }
    bar.appendChild(barInner);

    state.detail = { listing: l, source: source };
    detail.hidden = false;
    scroll.scrollTop = 0;
    void detail.offsetWidth;
    detail.classList.add('is-open');

    if (detailKeyHandler) document.removeEventListener('keydown', detailKeyHandler);
    detailKeyHandler = gallery.keyHandler || null;
    if (detailKeyHandler) document.addEventListener('keydown', detailKeyHandler);

    openLayer('detail', function () {
      state.detail = null;
      detail.classList.remove('is-open');
      if (detailKeyHandler) { document.removeEventListener('keydown', detailKeyHandler); detailKeyHandler = null; }
      setTimeout(function () { if (!detail.classList.contains('is-open')) { detail.hidden = true; clear(scroll); clear(bar); } }, 220);
    });
  }

  function closeDetail() {
    // closes the detail view together with any sheet above it
    var idx = -1;
    for (var i = layers.length - 1; i >= 0; i--) {
      if (layers[i].name === 'detail') { idx = i; break; }
    }
    if (idx < 0) return;
    closeLayers(layers.length - idx);
  }

  // ---------- Contact ----------
  function requestContact(l, btn) {
    if (!inTelegram) { showToast(msgOutside()); return; }
    haptic('impact', 'medium');
    btn.disabled = true;
    api('/api/listings/' + l.id + '/contact', { method: 'POST' }).then(function (data) {
      btn.disabled = false;
      haptic('notification', 'success');
      openContactSheet(data || {}, l);
    }, function (err) {
      btn.disabled = false;
      if (err.status === 401) showToast(msgOutside());
      else showToast(err.message || T('err.generic'), { retry: function () { requestContact(l, btn); } });
    });
  }

  function openContactSheet(data, l) {
    var phone = data.phone || '';
    var tel = phone.replace(/[^\d+]/g, '');
    var callBtn = h('a', { class: 'btn', href: 'tel:' + tel }, lineIcon(LI.phone, 20), h('span', { text: T('contact.call') }));
    var copyBtn = h('button', { type: 'button', class: 'btn btn-secondary' }, lineIcon(LI.copy, 20), h('span', { text: T('contact.copy') }));
    copyBtn.addEventListener('click', function () {
      copyText(phone).then(function () {
        haptic('notification', 'success');
        showToast(T('contact.copied'));
      }, function () { showToast(T('contact.copy_failed')); });
    });
    var body = h('div', null,
      h('div', { class: 'contact-phone', text: phone || '—' }),
      data.contact_name ? h('div', { class: 'contact-name', text: data.contact_name }) : null,
      h('div', { class: 'contact-name', text: listingTitle(l) + ' · #' + l.id }),
      h('div', { class: 'contact-actions' }, callBtn, copyBtn));
    openSheet(T('contact.title'), body);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }
  function legacyCopy(text) {
    return new Promise(function (resolve, reject) {
      try {
        var ta = h('textarea', { readonly: true, style: { position: 'fixed', top: '-1000px', opacity: '0' } });
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        var ok = document.execCommand('copy');
        document.body.removeChild(ta);
        ok ? resolve() : reject(new Error('copy failed'));
      } catch (e) { reject(e); }
    });
  }

  // ---------- Delete ----------
  function deleteListing(l, btn) {
    haptic('impact', 'medium');
    confirmDialog(T('delete.confirm', { id: l.id }), function (ok) {
      if (!ok) return;
      if (btn) btn.disabled = true;
      api('/api/my/' + l.id, { method: 'DELETE' }).then(function () {
        state.my.items = state.my.items.filter(function (x) { return x.id !== l.id; });
        if (state.detail && state.detail.listing.id === l.id) closeDetail();
        renderMy();
        haptic('notification', 'success');
        showToast(T('delete.done'));
      }, function (err) {
        if (btn) btn.disabled = false;
        haptic('notification', 'error');
        var msg = err.status === 403 ? T('delete.forbidden') : (err.message || T('err.generic'));
        showToast(msg, { retry: function () { deleteListing(l, btn); } });
      });
    });
  }

  // =====================================================================
  // Profile
  // =====================================================================
  function tgDisplayName() {
    if (!TG_USER) return '';
    return [TG_USER.first_name, TG_USER.last_name].filter(function (s) { return typeof s === 'string' && s.trim(); }).join(' ').trim();
  }

  function loadProfile(force) {
    var me = state.me;
    if (!inTelegram) { renderProfile(); return; }
    if (me.loading) return;
    if (me.loaded && !force) { renderProfile(); return; }
    me.loading = true; me.error = null;
    renderProfile();
    api('/api/me').then(function (data) {
      me.data = (data && typeof data === 'object') ? data : {};
      me.loaded = true; me.loading = false;
      renderProfile();
    }, function (err) {
      me.loading = false;
      me.error = err.message || T('err.generic');
      renderProfile();
    });
  }

  function renderProfile() {
    var me = state.me;
    var wrap = $('profile-card');
    clear(wrap);
    var mySection = $('my-section');

    if (!inTelegram) {
      mySection.hidden = true;
      wrap.appendChild(inTelegramNoUser
        ? stateCard('refresh', T('my.reopen_title'),
            T('my.reopen_text', { view: T('bot.view_listings'), app: T('bot.app_menu') }))
        : stateCard('phone', T('my.only_tg_title'), T('my.only_tg_text')));
      return;
    }
    mySection.hidden = false;

    var d = me.data || {};
    var name = (typeof d.full_name === 'string' && d.full_name.trim()) ? d.full_name.trim() : (tgDisplayName() || T('profile.guest'));
    var username = (typeof d.username === 'string' && d.username) ? d.username : ((TG_USER && TG_USER.username) || '');
    var initial = (name.charAt(0) || '?').toUpperCase();

    var phoneText = '';
    if (me.loaded) phoneText = (typeof d.phone_number === 'string' && d.phone_number) ? d.phone_number : T('profile.no_phone');
    else if (me.loading) phoneText = T('common.loading');

    var info = h('div', { class: 'profile-info' },
      h('div', { class: 'profile-name', text: name }),
      username ? h('div', { class: 'profile-username', text: '@' + username }) : null,
      phoneText ? h('div', { class: 'profile-phone', text: phoneText }) : null,
      me.loaded ? h('span', {
        class: 'badge ' + (d.registered ? 'badge-approved' : 'badge-pending'),
        text: T(d.registered ? 'profile.registered' : 'profile.not_registered')
      }) : null);

    wrap.appendChild(h('div', { class: 'profile' }, h('div', { class: 'avatar', 'aria-hidden': 'true', text: initial }), info));

    if (me.error && !me.loaded) {
      var retry = h('button', { type: 'button', class: 'btn btn-secondary btn-sm', text: T('common.retry') });
      retry.addEventListener('click', function () { loadProfile(true); });
      wrap.appendChild(h('div', { class: 'profile-retry' }, retry));
    }
  }

  function renderLangSwitch() {
    Array.prototype.forEach.call($('lang-switch').querySelectorAll('.lang-btn'), function (b) {
      var active = b.getAttribute('data-lang') === LANG;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  // Switch the UI language: static texts, labels, and every server-localized list.
  function setLang(lang) {
    lang = exactLang(lang);
    if (!lang || lang === LANG) return;
    LANG = lang;
    storageSet('sessionStorage', lang);
    storageSet('localStorage', lang);
    haptic('selection');
    applyStaticI18n();
    renderLangSwitch();
    renderSortLabel();
    renderChips();
    renderBrandUser();
    renderFavsCount();
    state.favs.dirty = true;
    loadCatalog(true);
    if (state.tab === 'favs') loadFavs(true);
    renderProfile();
    if (inTelegram) {
      state.my.loaded = false;
      if (state.tab === 'profile') loadMy(true); else renderMy();
    }
  }

  // =====================================================================
  // My listings (inside the profile)
  // =====================================================================
  function loadMy(force) {
    var m = state.my;
    if (!inTelegram) { renderMy(); return; }
    if (m.loading) return;
    if (m.loaded && !force) { renderMy(); return; }
    m.loading = true; m.error = null;
    renderMy();
    api('/api/my').then(function (data) {
      m.items = (data && Array.isArray(data.items)) ? data.items : [];
      m.registered = !!(data && data.registered);
      m.loaded = true; m.loading = false;
      renderMy();
    }, function (err) {
      m.error = err.message || T('err.generic');
      m.loading = false;
      renderMy();
      showToast(m.error, { retry: function () { loadMy(true); } });
    });
  }

  function renderMy() {
    var m = state.my;
    var list = $('my-list');
    clear(list);
    if (!inTelegram) return;

    if (m.loading && !m.loaded) {
      for (var i = 0; i < 2; i++) list.appendChild(skeletonRow());
      return;
    }
    if (m.error && !m.loaded) {
      var retry = h('button', { type: 'button', class: 'btn btn-secondary', text: T('common.retry') });
      retry.addEventListener('click', function () { loadMy(true); });
      list.appendChild(stateCard('error', T('common.load_failed'), m.error, retry));
      return;
    }
    if (m.loaded && m.registered === false) {
      var closeBtn = h('button', { type: 'button', class: 'btn', text: T('my.to_bot') });
      closeBtn.addEventListener('click', closeApp);
      list.appendChild(stateCard('doc', T('my.not_registered_title'),
        T('my.not_registered_text', { register: T('bot.register') }), closeBtn));
      return;
    }

    if (m.items.length === 0) {
      list.appendChild(stateCard('folder', T('my.empty_title'), T('my.empty_text')));
    } else {
      m.items.forEach(function (l) { list.appendChild(buildMyRow(l)); });
    }

    var addBtn = h('button', { type: 'button', class: 'btn' }, lineIcon(LI.plus, 20, 2.2), h('span', { text: T('add.button') }));
    addBtn.addEventListener('click', function () { openBotLink(BOT_ADD_URL); });
    list.appendChild(h('div', { class: 'info-card' },
      h('div', { class: 'info-card-title', text: T('my.add_title') }),
      h('div', { class: 'info-card-text', text: T('my.add_text', { add: T('bot.add_listing') }) }),
      addBtn));
  }

  // =====================================================================
  // Tabs
  // =====================================================================
  function switchTab(tab) {
    if (TABS.indexOf(tab) < 0) tab = 'catalog';
    if (tab === state.tab) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    state.scroll[state.tab] = window.scrollY || 0;
    state.tab = tab;
    TABS.forEach(function (name) { $('view-' + name).hidden = name !== tab; });
    Array.prototype.forEach.call($('tabbar').querySelectorAll('.tab'), function (b) {
      var active = b.getAttribute('data-tab') === tab;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    haptic('selection');
    window.scrollTo(0, state.scroll[tab] || 0);
    if (tab === 'favs') loadFavs(false);
    else if (tab === 'profile') { loadProfile(false); loadMy(false); }
  }

  function setupTabs() {
    $('tabbar').addEventListener('click', function (e) {
      var btn = e.target.closest('.tab');
      if (btn) switchTab(btn.getAttribute('data-tab'));
    });
    $('my-refresh').addEventListener('click', function () {
      haptic('impact', 'light');
      if (!inTelegram) { renderProfile(); renderMy(); return; }
      loadProfile(true);
      loadMy(true);
    });
    $('lang-switch').addEventListener('click', function (e) {
      var btn = e.target.closest('.lang-btn');
      if (btn) setLang(btn.getAttribute('data-lang'));
    });
    $('add-btn').addEventListener('click', function (e) { openBotLink(BOT_ADD_URL, e); });
    $('bot-link').addEventListener('click', function (e) { openBotLink(BOT_URL, e); });
  }

  function renderBrandUser() {
    var u = (TG_USER && typeof TG_USER.username === 'string' && TG_USER.username) ? '@' + TG_USER.username : '';
    $('brand-user').textContent = u;
  }

  // =====================================================================
  // Init
  // =====================================================================
  function init() {
    // a reload may leave a stale layer depth in history.state
    try { if (historyDepth() > 0) history.replaceState(null, ''); } catch (e) { /* ignore */ }
    applyStaticI18n();
    setupTelegram();
    renderBrandUser();
    $('detail-close').addEventListener('click', closeDetail);
    $('sheet-close').addEventListener('click', closeSheet);
    $('sheet-backdrop').addEventListener('click', closeSheet);
    setupTabs();
    setupCatalog();
    setupSearch();
    renderChips();
    renderSortLabel();
    renderLangSwitch();
    renderFavsCount();
    renderProfile();
    loadCatalog(true);

    // ?tab=favs|add|profile lets the bot deep-link into a section
    var startTab = '';
    try { startTab = new URLSearchParams(location.search).get('tab') || ''; } catch (e) { startTab = ''; }
    if (startTab && TABS.indexOf(startTab) > 0) switchTab(startTab);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
