/* Chirchiq Kvartira — Telegram Mini App (frontend)
 * Plain JS, no build step. All server data is inserted via textContent.
 */
(function () {
  'use strict';

  // =====================================================================
  // Telegram SDK
  // =====================================================================
  var tg = (window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;

  // Telegram passes launch data in the URL hash (#tgWebAppData=...). The official SDK
  // reads it, but if the SDK script (telegram.org) fails to load — common on some
  // networks — we read it ourselves so auth still works.
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
      'seg.label': "E'lon turi",
      'seg.all': 'Hammasi',
      'seg.rent': 'Ijaraga',
      'seg.sale': 'Sotuv',
      'filter.button': 'Filtr',
      'filter.title': 'Filtr',
      'filter.rooms': 'Xonalar soni',
      'filter.currency': 'Valyuta',
      'filter.price': 'Narx',
      'filter.sort': 'Saralash',
      'filter.apply': "Qo'llash",
      'filter.clear': 'Tozalash',
      'filter.reset': 'Filtrni tozalash',
      'price.from': 'Dan',
      'price.to': 'Gacha',
      'price.need_currency': "Narx bo'yicha filtr uchun valyutani tanlang",
      'sort.new': 'Yangi',
      'sort.cheap': 'Arzon',
      'sort.expensive': 'Qimmat',
      'cur.som': "so'm",
      'catalog.more': "Yana ko'rsatish",
      'catalog.found': 'Topildi: {n} ta',
      'catalog.empty_title': "E'lonlar topilmadi",
      'catalog.empty_text': "Filtrni o'zgartirib ko'ring yoki keyinroq qayting",
      'common.loading': 'Yuklanmoqda…',
      'common.retry': 'Qayta urinish',
      'common.close': 'Yopish',
      'common.load_failed': "Yuklab bo'lmadi",
      'toast.retry': 'Qayta',
      'tabs.label': "Bo'limlar",
      'tabs.catalog': "E'lonlar",
      'tabs.my': "Mening e'lonlarim",
      'type.rent': 'Ijaraga',
      'type.sale': 'Sotiladi',
      'status.pending': 'Tekshiruvda',
      'status.approved': 'Faol',
      'status.rejected': 'Rad etilgan',
      'status.archived': 'Arxivda',
      'title.rooms': '{n} xonali',
      'title.area': '{n} m²',
      'title.floor_of': '{floor}/{total} qavat',
      'title.floor': '{floor}-qavat',
      'title.total_floors': '{n} qavatli',
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
      'detail.map': "🗺 Xaritada ko'rish",
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
      'action.delete': "🗑 O'chirish",
      'action.contact': "📞 Bog'lanish",
      'contact.title': "Bog'lanish",
      'contact.call': "📞 Qo'ng'iroq qilish",
      'contact.copy': '📋 Nusxalash',
      'contact.copied': 'Raqam nusxalandi',
      'contact.copy_failed': "Nusxalab bo'lmadi",
      'contact.outside': "Telefon raqamini ko'rish uchun ilovani Telegram ichida oching",
      'contact.outside_no_user': "Telefon raqamini ko'rish uchun ilovani yozuv maydoni yonidagi «{app}» tugmasi orqali qayta oching",
      'delete.confirm': "E'lon #{id} o'chirilsinmi? Bu amalni qaytarib bo'lmaydi.",
      'delete.done': "E'lon o'chirildi",
      'delete.forbidden': "Bu e'lon sizga tegishli emas",
      'app.only_in_telegram': 'Bu tugma faqat Telegram ichida ishlaydi',
      'my.title': "Mening e'lonlarim",
      'my.refresh': 'Yangilash',
      'my.reopen_title': 'Ilovani qayta oching',
      'my.reopen_text': "Bu bo'lim uchun ilovani botdagi «{view}» tugmasi yoki yozuv maydoni yonidagi «{app}» tugmasi orqali oching",
      'my.only_tg_title': "Bu bo'lim faqat Telegram ichida ishlaydi",
      'my.only_tg_text': "E'lonlaringizni ko'rish uchun ilovani Telegram botidan oching",
      'my.to_bot': "Botga o'tish",
      'my.not_registered_title': "Ro'yxatdan o'tmagansiz",
      'my.not_registered_text': "E'lon qo'shish uchun botda «{register}» tugmasini bosing",
      'my.empty_title': "Hali e'lonlaringiz yo'q",
      'my.empty_text': "Birinchi e'loningizni bot orqali qo'shing",
      'my.add_title': "➕ Yangi e'lon qo'shish",
      'my.add_text': "Botdagi «{add}» tugmasi orqali yangi e'lon joylashtiring",
      // Bot button labels (must match app/i18n texts: btn.view_listings, btn.app_menu, btn.register, btn.add_listing)
      'bot.view_listings': "📱 E'lonlarni ko'rish",
      'bot.app_menu': 'Ilova',
      'bot.register': "📝 Ro'yxatdan o'tish",
      'bot.add_listing': "➕ E'lon qo'shish"
    },
    ru: {
      'seg.label': 'Тип объявления',
      'seg.all': 'Все',
      'seg.rent': 'Аренда',
      'seg.sale': 'Продажа',
      'filter.button': 'Фильтр',
      'filter.title': 'Фильтр',
      'filter.rooms': 'Количество комнат',
      'filter.currency': 'Валюта',
      'filter.price': 'Цена',
      'filter.sort': 'Сортировка',
      'filter.apply': 'Применить',
      'filter.clear': 'Сбросить',
      'filter.reset': 'Сбросить фильтр',
      'price.from': 'От',
      'price.to': 'До',
      'price.need_currency': 'Чтобы фильтровать по цене, выберите валюту',
      'sort.new': 'Новые',
      'sort.cheap': 'Дешевле',
      'sort.expensive': 'Дороже',
      'cur.som': 'сум',
      'catalog.more': 'Показать ещё',
      'catalog.found': 'Найдено: {n}',
      'catalog.empty_title': 'Объявления не найдены',
      'catalog.empty_text': 'Измените фильтр или загляните позже',
      'common.loading': 'Загрузка…',
      'common.retry': 'Повторить',
      'common.close': 'Закрыть',
      'common.load_failed': 'Не удалось загрузить',
      'toast.retry': 'Повторить',
      'tabs.label': 'Разделы',
      'tabs.catalog': 'Объявления',
      'tabs.my': 'Мои объявления',
      'type.rent': 'Аренда',
      'type.sale': 'Продажа',
      'status.pending': 'На проверке',
      'status.approved': 'Активно',
      'status.rejected': 'Отклонено',
      'status.archived': 'В архиве',
      'title.rooms': '{n}-комн.',
      'title.area': '{n} м²',
      'title.floor_of': '{floor}/{total} этаж',
      'title.floor': '{floor} этаж',
      'title.total_floors': '{n}-этажный',
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
      'detail.map': '🗺 Показать на карте',
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
      'action.delete': '🗑 Удалить',
      'action.contact': '📞 Связаться',
      'contact.title': 'Связаться',
      'contact.call': '📞 Позвонить',
      'contact.copy': '📋 Скопировать',
      'contact.copied': 'Номер скопирован',
      'contact.copy_failed': 'Не удалось скопировать',
      'contact.outside': 'Чтобы увидеть номер телефона, откройте приложение в Telegram',
      'contact.outside_no_user': 'Чтобы увидеть номер телефона, откройте приложение заново кнопкой «{app}» рядом с полем ввода',
      'delete.confirm': 'Удалить объявление #{id}? Это действие нельзя отменить.',
      'delete.done': 'Объявление удалено',
      'delete.forbidden': 'Это объявление вам не принадлежит',
      'app.only_in_telegram': 'Эта кнопка работает только в Telegram',
      'my.title': 'Мои объявления',
      'my.refresh': 'Обновить',
      'my.reopen_title': 'Откройте приложение заново',
      'my.reopen_text': 'Для этого раздела откройте приложение кнопкой «{view}» в боте или кнопкой «{app}» рядом с полем ввода',
      'my.only_tg_title': 'Этот раздел работает только в Telegram',
      'my.only_tg_text': 'Чтобы увидеть свои объявления, откройте приложение из Telegram-бота',
      'my.to_bot': 'Перейти в бот',
      'my.not_registered_title': 'Вы не зарегистрированы',
      'my.not_registered_text': 'Чтобы добавить объявление, нажмите в боте кнопку «{register}»',
      'my.empty_title': 'У вас пока нет объявлений',
      'my.empty_text': 'Добавьте первое объявление через бота',
      'my.add_title': '➕ Новое объявление',
      'my.add_text': 'Разместите новое объявление кнопкой «{add}» в боте',
      'bot.view_listings': '📱 Смотреть объявления',
      'bot.app_menu': 'Приложение',
      'bot.register': '📝 Регистрация',
      'bot.add_listing': '➕ Добавить объявление'
    },
    en: {
      'seg.label': 'Listing type',
      'seg.all': 'All',
      'seg.rent': 'Rent',
      'seg.sale': 'Sale',
      'filter.button': 'Filter',
      'filter.title': 'Filter',
      'filter.rooms': 'Rooms',
      'filter.currency': 'Currency',
      'filter.price': 'Price',
      'filter.sort': 'Sort by',
      'filter.apply': 'Apply',
      'filter.clear': 'Clear',
      'filter.reset': 'Clear filters',
      'price.from': 'From',
      'price.to': 'To',
      'price.need_currency': 'Choose a currency to filter by price',
      'sort.new': 'Newest',
      'sort.cheap': 'Cheapest',
      'sort.expensive': 'Most expensive',
      'cur.som': 'UZS',
      'catalog.more': 'Show more',
      'catalog.found': 'Found: {n}',
      'catalog.empty_title': 'No listings found',
      'catalog.empty_text': 'Try changing the filters or check back later',
      'common.loading': 'Loading…',
      'common.retry': 'Try again',
      'common.close': 'Close',
      'common.load_failed': "Couldn't load",
      'toast.retry': 'Retry',
      'tabs.label': 'Sections',
      'tabs.catalog': 'Listings',
      'tabs.my': 'My listings',
      'type.rent': 'For rent',
      'type.sale': 'For sale',
      'status.pending': 'Under review',
      'status.approved': 'Active',
      'status.rejected': 'Rejected',
      'status.archived': 'Archived',
      'title.rooms': '{n}-room',
      'title.area': '{n} m²',
      'title.floor_of': 'floor {floor}/{total}',
      'title.floor': 'floor {floor}',
      'title.total_floors': '{n} floors',
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
      'detail.map': '🗺 View on map',
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
      'action.delete': '🗑 Delete',
      'action.contact': '📞 Contact',
      'contact.title': 'Contact',
      'contact.call': '📞 Call',
      'contact.copy': '📋 Copy',
      'contact.copied': 'Number copied',
      'contact.copy_failed': "Couldn't copy",
      'contact.outside': 'Open the app inside Telegram to see the phone number',
      'contact.outside_no_user': 'To see the phone number, reopen the app with the “{app}” button next to the message field',
      'delete.confirm': 'Delete listing #{id}? This cannot be undone.',
      'delete.done': 'Listing deleted',
      'delete.forbidden': "This listing doesn't belong to you",
      'app.only_in_telegram': 'This button works only inside Telegram',
      'my.title': 'My listings',
      'my.refresh': 'Refresh',
      'my.reopen_title': 'Reopen the app',
      'my.reopen_text': 'To use this section, open the app with the “{view}” button in the bot or the “{app}” button next to the message field',
      'my.only_tg_title': 'This section works only inside Telegram',
      'my.only_tg_text': 'Open the app from the Telegram bot to see your listings',
      'my.to_bot': 'Go to the bot',
      'my.not_registered_title': "You're not registered",
      'my.not_registered_text': 'To add a listing, tap “{register}” in the bot',
      'my.empty_title': 'You have no listings yet',
      'my.empty_text': 'Add your first listing via the bot',
      'my.add_title': '➕ Add a new listing',
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
    try {
      var u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
      if (u && u.language_code) return u.language_code;
    } catch (e) { /* ignore */ }
    try {
      // SDK missing: read user.language_code from the raw initData ourselves
      var m = /(?:^|&)user=([^&]*)/.exec(initData || '');
      if (m) {
        var user = JSON.parse(decodeURIComponent(m[1]));
        if (user && user.language_code) return user.language_code;
      }
    } catch (e) { /* ignore */ }
    return '';
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

  // T('catalog.found', { n: 5 }) -> "Topildi: 5 ta"
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

  function confirmDialog(message, cb) {
    if (tg && typeof tg.showConfirm === 'function') {
      try { tg.showConfirm(message, cb); return; } catch (e) { /* unsupported version */ }
    }
    cb(window.confirm(message));
  }

  // =====================================================================
  // State
  // =====================================================================
  var DEFAULT_FILTERS = { type: 'all', rooms: null, currency: null, min_price: null, max_price: null, sort: 'new' };

  var state = {
    tab: 'catalog',
    filters: Object.assign({}, DEFAULT_FILTERS),
    catalog: { items: [], total: 0, offset: 0, limit: 12, loading: false, loaded: false, error: null, rendered: 0, requestId: 0 },
    my: { items: [], registered: null, loading: false, loaded: false, error: null },
    detail: null, // { listing, source: 'catalog' | 'my' }
    scroll: { catalog: 0, my: 0 }
  };

  var MSG_OUTSIDE = inTelegramNoUser
    ? T('contact.outside_no_user', { app: T('bot.app_menu') })
    : T('contact.outside');

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
  var ICON_PREV = 'M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z';
  var ICON_NEXT = 'M8.59 16.59 10 18l6-6-6-6-1.41 1.41L13.17 12z';

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

  function listingTitle(l) {
    var parts = [T('title.rooms', { n: l.rooms })];
    if (l.area) parts.push(T('title.area', { n: formatNum(l.area) }));
    if (l.floor && l.total_floors) parts.push(T('title.floor_of', { floor: l.floor, total: l.total_floors }));
    else if (l.floor) parts.push(T('title.floor', { floor: l.floor }));
    else if (l.total_floors) parts.push(T('title.total_floors', { n: l.total_floors }));
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
      el.appendChild(document.createTextNode(m[1]));
      el.appendChild(h('span', { class: 'per', text: ' / ' + m[2] }));
    } else {
      el.textContent = text;
    }
    return el;
  }

  function photoUrl(url, priv) {
    if (priv && initData) {
      return url + (url.indexOf('?') >= 0 ? '&' : '?') + 'init_data=' + encodeURIComponent(initData);
    }
    return url;
  }

  // =====================================================================
  // API
  // =====================================================================
  function ApiError(status, message) {
    this.status = status;
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
    return fetch(withLang(path), opts).then(function (res) {
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
    }, function () {
      throw new ApiError(0, T('err.network'));
    });
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
  // Cards
  // =====================================================================
  function placeholderMedia(media) {
    media.classList.add('is-placeholder');
    media.appendChild(h('span', { class: 'card-placeholder-icon', text: '🏠' }));
  }

  function buildCard(l, source) {
    var priv = source === 'my';
    var media = h('div', { class: 'card-media' });
    if (l.photos && l.photos.length) {
      var img = h('img', { class: 'card-img', src: photoUrl(l.photos[0], priv), alt: '', loading: 'lazy', decoding: 'async' });
      img.addEventListener('error', function () { if (!media.classList.contains('is-placeholder')) placeholderMedia(media); });
      media.appendChild(img);
      if (l.photos.length > 1) media.appendChild(h('span', { class: 'card-count', text: '🖼 ' + l.photos.length }));
    } else {
      placeholderMedia(media);
    }
    var badges = h('div', { class: 'card-badges' }, h('span', { class: 'badge badge-' + l.type, text: typeText(l) }));
    if (priv) badges.appendChild(h('span', { class: 'badge badge-' + l.status, text: statusText(l) }));
    media.appendChild(badges);

    var footer = h('div', { class: 'card-footer' },
      h('span', { text: '👁 ' + (l.view_count || 0) }));
    if (priv) {
      footer.appendChild(h('span', { class: 'sep', text: '·' }));
      footer.appendChild(h('span', { text: '📞 ' + (l.contact_count || 0) }));
    }
    footer.appendChild(h('span', { class: 'grow' }));
    footer.appendChild(h('span', { text: relativeDate(l.created_at) }));

    var body = h('div', { class: 'card-body' },
      priceNode(l, 'card-price'),
      h('div', { class: 'card-title', text: listingTitle(l) }),
      h('div', { class: 'card-address', text: l.address || '' }),
      footer);

    var card = h('article', { class: 'card card-link', role: 'button', tabindex: '0', 'data-id': String(l.id) }, media, body);

    var open = function () { haptic('impact', 'light'); openDetail(l, source); };
    card.addEventListener('click', open);
    card.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
    });

    if (priv) {
      var del = h('button', { type: 'button', class: 'btn btn-danger btn-sm', text: T('action.delete') });
      del.addEventListener('click', function (e) {
        e.stopPropagation();
        deleteListing(l, del);
      });
      card.appendChild(h('div', { class: 'card-actions' }, del));
    }
    return card;
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

  function stateCard(emoji, title, text, button) {
    return h('div', { class: 'state' },
      h('div', { class: 'state-emoji', text: emoji }),
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
    if (f.rooms) p.set('rooms', String(f.rooms));
    if (f.currency) {
      p.set('currency', f.currency);
      if (f.min_price !== null && f.min_price !== undefined) p.set('min_price', String(f.min_price));
      if (f.max_price !== null && f.max_price !== undefined) p.set('max_price', String(f.max_price));
    }
    p.set('sort', f.sort || 'new');
    p.set('offset', String(offset));
    p.set('limit', String(limit));
    return p.toString();
  }

  function loadCatalog(reset) {
    var c = state.catalog;
    if (c.loading && !reset) return;
    if (reset) {
      c.items = []; c.offset = 0; c.total = 0; c.loaded = false; c.rendered = 0;
    }
    c.error = null;
    c.loading = true;
    var reqId = ++c.requestId;
    renderCatalog();
    api('/api/listings?' + buildQuery(state.filters, c.offset, c.limit)).then(function (data) {
      if (reqId !== c.requestId) return;
      var items = (data && Array.isArray(data.items)) ? data.items : [];
      c.items = c.items.concat(items);
      c.total = (data && typeof data.total === 'number') ? data.total : c.items.length;
      c.offset = c.items.length;
      c.loaded = true;
      c.loading = false;
      renderCatalog();
    }, function (err) {
      if (reqId !== c.requestId) return;
      c.error = err.message || T('err.generic');
      c.loading = false;
      renderCatalog();
      showToast(c.error, { retry: function () { loadCatalog(c.items.length === 0); } });
    });
  }

  function renderCatalog() {
    var c = state.catalog;
    var list = $('catalog-list');
    var more = $('catalog-more');
    var moreBtn = $('catalog-more-btn');

    // result count
    $('result-count').textContent = c.loaded ? T('catalog.found', { n: c.total }) : (c.loading ? T('common.loading') : '');

    // active filter count
    var n = activeFilterCount(state.filters);
    $('filter-count').hidden = n === 0;
    $('filter-count').textContent = String(n);
    $('filter-btn').classList.toggle('is-active', n > 0);

    if (c.items.length === 0) {
      clear(list);
      c.rendered = 0;
      if (c.loading) {
        for (var i = 0; i < 4; i++) list.appendChild(skeletonCard());
      } else if (c.error) {
        var retry = h('button', { type: 'button', class: 'btn btn-secondary', text: T('common.retry') });
        retry.addEventListener('click', function () { loadCatalog(true); });
        list.appendChild(stateCard('😕', T('common.load_failed'), c.error, retry));
      } else if (c.loaded) {
        var resetBtn = null;
        if (n > 0 || state.filters.type !== 'all') {
          resetBtn = h('button', { type: 'button', class: 'btn btn-secondary', text: T('filter.reset') });
          resetBtn.addEventListener('click', function () {
            state.filters = Object.assign({}, DEFAULT_FILTERS);
            renderSegment();
            loadCatalog(true);
          });
        }
        list.appendChild(stateCard('🔍', T('catalog.empty_title'), T('catalog.empty_text'), resetBtn));
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

  function activeFilterCount(f) {
    var n = 0;
    if (f.rooms) n++;
    if (f.currency) n++;
    if (f.currency && f.min_price !== null) n++;
    if (f.currency && f.max_price !== null) n++;
    if (f.sort && f.sort !== 'new') n++;
    return n;
  }

  function renderSegment() {
    var btns = $('type-segment').querySelectorAll('.segmented-btn');
    Array.prototype.forEach.call(btns, function (b) {
      var active = b.getAttribute('data-type') === state.filters.type;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-selected', active ? 'true' : 'false');
    });
  }

  function setupCatalog() {
    $('type-segment').addEventListener('click', function (e) {
      var btn = e.target.closest('.segmented-btn');
      if (!btn) return;
      var type = btn.getAttribute('data-type');
      if (type === state.filters.type) return;
      state.filters.type = type;
      haptic('selection');
      renderSegment();
      window.scrollTo(0, 0);
      loadCatalog(true);
    });
    $('filter-btn').addEventListener('click', openFilterSheet);
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
  // Filter sheet
  // =====================================================================
  function openFilterSheet() {
    haptic('impact', 'light');
    var draft = Object.assign({}, state.filters);

    function chipGroup(options, getVal, setVal, allowNone) {
      var wrap = h('div', { class: 'chips' });
      options.forEach(function (o) {
        var btn = h('button', { type: 'button', class: 'chip-opt', text: o.label, 'aria-pressed': String(getVal() === o.value) });
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

    var roomsGroup = chipGroup(
      [1, 2, 3, 4, 5, 6].map(function (n) { return { value: n, label: n === 6 ? '6+' : String(n) }; }),
      function () { return draft.rooms; }, function (v) { draft.rooms = v; }, true);

    var currencyGroup = chipGroup(
      [{ value: 'UZS', label: T('cur.som') }, { value: 'USD', label: '$' }],
      function () { return draft.currency; }, function (v) { draft.currency = v; }, true);

    var sortGroup = chipGroup(
      [{ value: 'new', label: T('sort.new') }, { value: 'cheap', label: T('sort.cheap') }, { value: 'expensive', label: T('sort.expensive') }],
      function () { return draft.sort; }, function (v) { draft.sort = v || 'new'; }, false);

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
      h('div', { class: 'field' }, h('span', { class: 'field-label', text: T('filter.rooms') }), roomsGroup),
      h('div', { class: 'field' }, h('span', { class: 'field-label', text: T('filter.currency') }), currencyGroup),
      h('div', { class: 'field' },
        h('span', { class: 'field-label', text: T('filter.price') }),
        h('div', { class: 'price-row' }, minField.el, maxField.el),
        priceNote),
      h('div', { class: 'field' }, h('span', { class: 'field-label', text: T('filter.sort') }), sortGroup));

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
        rooms: draft.rooms,
        currency: draft.currency,
        min_price: draft.currency ? min : null,
        max_price: draft.currency ? max : null,
        sort: draft.sort || 'new'
      });
      haptic('impact', 'medium');
      closeSheet();
      window.scrollTo(0, 0);
      loadCatalog(true);
    });
    clearBtn.addEventListener('click', function () {
      state.filters = Object.assign({}, DEFAULT_FILTERS, { type: state.filters.type });
      haptic('impact', 'light');
      closeSheet();
      window.scrollTo(0, 0);
      loadCatalog(true);
    });

    openSheet(T('filter.title'), body);
  }

  // =====================================================================
  // Detail view
  // =====================================================================
  function buildGallery(l, priv) {
    var photos = (l.photos || []).slice();
    if (!photos.length) {
      return h('div', { class: 'gallery is-placeholder' }, h('span', { text: '🏠' }));
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
      prev = h('button', { type: 'button', class: 'gallery-nav prev', 'aria-label': T('gallery.prev') }, svgIcon(ICON_PREV, 26));
      next = h('button', { type: 'button', class: 'gallery-nav next', 'aria-label': T('gallery.next') }, svgIcon(ICON_NEXT, 26));
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
    var btn = h('button', { type: 'button', class: 'btn btn-secondary detail-map-btn', text: T('detail.map') });
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

    var badges = h('div', { class: 'detail-badges' },
      h('span', { class: 'badge badge-' + l.type, text: typeText(l) }),
      priv ? h('span', { class: 'badge badge-' + l.status, text: statusText(l) }) : null,
      h('span', { class: 'badge badge-id', text: '#' + l.id }));

    var grid = h('dl', { class: 'detail-grid' });
    function row(label, value, span) {
      if (value === null || value === undefined || value === '') return;
      grid.appendChild(h('div', { class: span ? 'span2' : null }, h('dt', { text: label }), h('dd', { text: String(value) })));
    }
    row(T('detail.rooms'), T('title.rooms', { n: l.rooms }));
    row(T('detail.area'), l.area ? T('title.area', { n: formatNum(l.area) }) : null);
    if (l.floor && l.total_floors) row(T('detail.floor'), l.floor + ' / ' + l.total_floors);
    else if (l.floor) row(T('detail.floor'), l.floor);
    else if (l.total_floors) row(T('detail.total_floors'), l.total_floors);
    row(T('detail.district'), l.district || null);
    row(T('detail.address'), l.address, true);
    row(T('detail.number'), '#' + l.id);
    row(T('detail.date'), fullDate(l.created_at));
    if (l.owner_name) row(T('detail.owner'), l.owner_name);

    var viewsEl = h('span', { text: '👁 ' + T('detail.views', { n: l.view_count || 0 }) });
    if (!priv) {
      // GET /api/listings/{id} counts the view and returns the fresh counter (best-effort)
      api('/api/listings/' + l.id).then(function (fresh) {
        if (!fresh || typeof fresh.view_count !== 'number') return;
        l.view_count = fresh.view_count;
        viewsEl.textContent = '👁 ' + T('detail.views', { n: fresh.view_count });
      }, function () { /* ignore: counting views must never break the detail view */ });
    }

    var body = h('div', { class: 'detail-body' },
      priceNode(l, 'detail-price'),
      badges,
      h('h2', { class: 'detail-title', text: listingTitle(l) }),
      h('div', { class: 'detail-address' }, h('span', { text: '📍' }), h('span', { text: l.address || '' })),
      mapButton(l),
      h('div', { class: 'detail-section' }, h('div', { class: 'detail-section-title', text: T('detail.info') }), grid),
      l.description ? h('div', { class: 'detail-section' },
        h('div', { class: 'detail-section-title', text: T('detail.description') }),
        h('p', { class: 'detail-desc', text: l.description })) : null,
      h('div', { class: 'detail-meta' },
        viewsEl,
        priv ? h('span', { text: '📞 ' + T('detail.contacts', { n: l.contact_count || 0 }) }) : null,
        h('span', { text: '🕒 ' + relativeDate(l.created_at) })));

    scroll.appendChild(h('div', { class: 'detail-inner' }, gallery, body));

    var barInner = h('div', { class: 'detail-bar-inner' });
    if (priv) {
      var del = h('button', { type: 'button', class: 'btn btn-danger', text: T('action.delete') });
      del.addEventListener('click', function () { deleteListing(l, del); });
      barInner.appendChild(del);
    } else {
      var contact = h('button', { type: 'button', class: 'btn', text: T('action.contact') });
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
    if (!inTelegram) { showToast(MSG_OUTSIDE); return; }
    haptic('impact', 'medium');
    btn.disabled = true;
    api('/api/listings/' + l.id + '/contact', { method: 'POST' }).then(function (data) {
      btn.disabled = false;
      haptic('notification', 'success');
      openContactSheet(data || {}, l);
    }, function (err) {
      btn.disabled = false;
      if (err.status === 401) showToast(MSG_OUTSIDE);
      else showToast(err.message || T('err.generic'), { retry: function () { requestContact(l, btn); } });
    });
  }

  function openContactSheet(data, l) {
    var phone = data.phone || '';
    var tel = phone.replace(/[^\d+]/g, '');
    var callBtn = h('a', { class: 'btn', href: 'tel:' + tel, text: T('contact.call') });
    var copyBtn = h('button', { type: 'button', class: 'btn btn-secondary', text: T('contact.copy') });
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
  // My listings
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

    if (!inTelegram) {
      list.appendChild(inTelegramNoUser
        ? stateCard('🔄', T('my.reopen_title'),
            T('my.reopen_text', { view: T('bot.view_listings'), app: T('bot.app_menu') }))
        : stateCard('📱', T('my.only_tg_title'), T('my.only_tg_text')));
      return;
    }
    if (m.loading && !m.loaded) {
      for (var i = 0; i < 3; i++) list.appendChild(skeletonCard());
      return;
    }
    if (m.error && !m.loaded) {
      var retry = h('button', { type: 'button', class: 'btn btn-secondary', text: T('common.retry') });
      retry.addEventListener('click', function () { loadMy(true); });
      list.appendChild(stateCard('😕', T('common.load_failed'), m.error, retry));
      return;
    }
    if (m.loaded && m.registered === false) {
      var closeBtn = h('button', { type: 'button', class: 'btn', text: T('my.to_bot') });
      closeBtn.addEventListener('click', closeApp);
      list.appendChild(stateCard('📝', T('my.not_registered_title'),
        T('my.not_registered_text', { register: T('bot.register') }), closeBtn));
      return;
    }

    if (m.items.length === 0) {
      list.appendChild(stateCard('🗂', T('my.empty_title'), T('my.empty_text')));
    } else {
      m.items.forEach(function (l) { list.appendChild(buildCard(l, 'my')); });
    }

    var addBtn = h('button', { type: 'button', class: 'btn btn-secondary', text: T('my.to_bot') });
    addBtn.addEventListener('click', closeApp);
    list.appendChild(h('div', { class: 'info-card' },
      h('div', { class: 'info-card-title', text: T('my.add_title') }),
      h('div', { class: 'info-card-text', text: T('my.add_text', { add: T('bot.add_listing') }) }),
      addBtn));
  }

  // =====================================================================
  // Tabs
  // =====================================================================
  function switchTab(tab) {
    if (tab === state.tab) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    state.scroll[state.tab] = window.scrollY || 0;
    state.tab = tab;
    $('view-catalog').hidden = tab !== 'catalog';
    $('view-my').hidden = tab !== 'my';
    Array.prototype.forEach.call($('tabbar').querySelectorAll('.tab'), function (b) {
      var active = b.getAttribute('data-tab') === tab;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    haptic('selection');
    window.scrollTo(0, state.scroll[tab] || 0);
    if (tab === 'my') loadMy(false);
  }

  function setupTabs() {
    $('tabbar').addEventListener('click', function (e) {
      var btn = e.target.closest('.tab');
      if (btn) switchTab(btn.getAttribute('data-tab'));
    });
    $('my-refresh').addEventListener('click', function () {
      haptic('impact', 'light');
      if (!inTelegram) { renderMy(); return; }
      loadMy(true);
    });
  }

  // =====================================================================
  // Init
  // =====================================================================
  function init() {
    // a reload may leave a stale layer depth in history.state
    try { if (historyDepth() > 0) history.replaceState(null, ''); } catch (e) { /* ignore */ }
    applyStaticI18n();
    setupTelegram();
    $('detail-close').addEventListener('click', closeDetail);
    $('sheet-close').addEventListener('click', closeSheet);
    $('sheet-backdrop').addEventListener('click', closeSheet);
    setupTabs();
    setupCatalog();
    renderSegment();
    loadCatalog(true);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
