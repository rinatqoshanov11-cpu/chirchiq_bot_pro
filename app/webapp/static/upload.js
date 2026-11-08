/* Chirchiq Kvartira — "📸 Rasm yuborish" page.
 *
 * Opened from the inline web_app button of the listing flow's photo step.
 * Picks images from the gallery, compresses them (JPEG, longest side 1600 px,
 * quality 0.85), uploads them in one request to /api/upload/photos and closes.
 * The server adds them to the listing and updates the progress message in the chat.
 * Never uses innerHTML: every text goes through textContent.
 */
(function () {
  'use strict';

  var MAX_SIDE = 1600;
  var QUALITY = 0.85;
  var SKIP_BYTES = 400 * 1024;        // small JPEGs are sent as they are
  var MAX_FILE_BYTES = 8 * 1024 * 1024;
  var CLOSE_DELAY = 800;
  var OK_TYPES = { 'image/jpeg': 1, 'image/png': 1, 'image/webp': 1 };

  var TEXTS = {
    uz: {
      title: 'Rasm yuborish',
      sub: 'Kamida {min} ta, ko‘pi bilan {max} ta rasm',
      subStatus: 'Qo‘shilgan: {n}/{max} · kamida {min} ta kerak',
      pick: 'Galereyadan tanlash',
      pickMore: 'Yana tanlash',
      outside: 'Bu sahifa Telegram ichida ishlaydi. Botdagi «📸 Rasm yuborish» tugmasi orqali oching.',
      preparing: 'Tayyorlanmoqda… {i}/{n}',
      uploading: 'Yuborilmoqda… {p}%',
      saving: 'Saqlanmoqda…',
      added: '✅ {n} ta rasm qo‘shildi',
      notWaiting: 'Avval botda e’lon qo‘shishni boshlang',
      unauthorized: 'Sahifani botdagi tugma orqali qayta oching',
      tooMany: 'Ko‘pi bilan {max} ta rasm yuborish mumkin',
      full: 'Rasmlar soni to‘ldi ({max}/{max})',
      trimmed: 'Faqat {n} tasi olinadi (ko‘pi bilan {max} ta)',
      badFile: 'Rasmni o‘qib bo‘lmadi. Boshqa rasm tanlang',
      tooLarge: 'Rasmlar juda katta. Kamroq rasm tanlang',
      busy: 'Oldingi yuklash tugashini kuting',
      network: 'Internet aloqasini tekshirib, qayta urinib ko‘ring',
      failed: 'Yuborib bo‘lmadi. Qayta urinib ko‘ring',
      noImages: 'Rasm tanlanmadi'
    },
    ru: {
      title: 'Отправить фото',
      sub: 'Минимум {min}, максимум {max} фото',
      subStatus: 'Добавлено: {n}/{max} · нужно минимум {min}',
      pick: 'Выбрать из галереи',
      pickMore: 'Выбрать ещё',
      outside: 'Эта страница работает внутри Telegram. Откройте её кнопкой «📸 Отправить фото» в боте.',
      preparing: 'Подготовка… {i}/{n}',
      uploading: 'Отправка… {p}%',
      saving: 'Сохранение…',
      added: '✅ Добавлено фото: {n}',
      notWaiting: 'Сначала начните добавление объявления в боте',
      unauthorized: 'Откройте страницу заново кнопкой в боте',
      tooMany: 'Можно отправить не больше {max} фото',
      full: 'Достигнут лимит фото ({max}/{max})',
      trimmed: 'Будут взяты только {n} (максимум {max})',
      badFile: 'Не удалось прочитать фото. Выберите другое',
      tooLarge: 'Фото слишком большие. Выберите меньше',
      busy: 'Дождитесь окончания предыдущей загрузки',
      network: 'Проверьте интернет и попробуйте снова',
      failed: 'Не удалось отправить. Попробуйте снова',
      noImages: 'Фото не выбраны'
    },
    en: {
      title: 'Send photos',
      sub: 'At least {min}, at most {max} photos',
      subStatus: 'Added: {n}/{max} · at least {min} needed',
      pick: 'Choose from gallery',
      pickMore: 'Choose more',
      outside: 'This page works inside Telegram. Open it with the «📸 Send photos» button in the bot.',
      preparing: 'Preparing… {i}/{n}',
      uploading: 'Uploading… {p}%',
      saving: 'Saving…',
      added: '✅ {n} photo(s) added',
      notWaiting: 'Start adding a listing in the bot first',
      unauthorized: 'Reopen this page with the button in the bot',
      tooMany: 'You can send at most {max} photos',
      full: 'Photo limit reached ({max}/{max})',
      trimmed: 'Only {n} will be taken (at most {max})',
      badFile: 'Could not read the photo. Choose another one',
      tooLarge: 'The photos are too large. Choose fewer',
      busy: 'Wait for the previous upload to finish',
      network: 'Check your internet connection and try again',
      failed: 'Could not send. Please try again',
      noImages: 'No photos selected'
    }
  };

  var tg = (window.Telegram && window.Telegram.WebApp) || null;

  function hashParam(name) {
    try {
      var raw = location.hash.charAt(0) === '#' ? location.hash.slice(1) : location.hash;
      var m = new RegExp('(?:^|&)' + name + '=([^&]*)').exec(raw);
      return m && m[1] ? decodeURIComponent(m[1]) : '';
    } catch (e) { return ''; }
  }
  function queryParam(name) {
    try {
      var m = new RegExp('[?&]' + name + '=([^&#]*)').exec(location.search);
      return m && m[1] ? decodeURIComponent(m[1]) : '';
    } catch (e) { return ''; }
  }

  // initData: from the SDK, else from the launch hash (SDK failed to load)
  var initData = (tg && typeof tg.initData === 'string' && tg.initData) ? tg.initData : hashParam('tgWebAppData');
  var inTelegram = initData.length > 0;

  var lang = (queryParam('lang') || '').toLowerCase().slice(0, 2);
  if (!TEXTS[lang]) {
    var code = '';
    try { code = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.language_code) || ''; } catch (e) { /* ignore */ }
    lang = TEXTS[code.slice(0, 2)] ? code.slice(0, 2) : 'uz';
  }
  var T = TEXTS[lang];

  function fmt(key, vars) {
    var s = T[key] || TEXTS.uz[key] || '';
    if (vars) {
      Object.keys(vars).forEach(function (k) { s = s.split('{' + k + '}').join(String(vars[k])); });
    }
    return s;
  }

  var $ = function (id) { return document.getElementById(id); };
  var els = {
    title: $('t-title'), sub: $('t-sub'), note: $('note'), file: $('file'), pick: $('pick'),
    pickText: $('pick-text'), progress: $('progress'), bar: $('bar'), progressText: $('progress-text'),
    grid: $('grid'), result: $('result')
  };

  var limits = { min: 3, max: 10, total: 0, known: false };
  var busy = false;
  var closed = false;

  // ---------------------------------------------------------------- theme
  function applyTheme() {
    if (tg) {
      try { if (tg.colorScheme) document.documentElement.setAttribute('data-theme', tg.colorScheme); } catch (e) { /* ignore */ }
      return;
    }
    try {
      var params = JSON.parse(hashParam('tgWebAppThemeParams') || '{}');
      var root = document.documentElement.style;
      Object.keys(params).forEach(function (k) { root.setProperty('--tg-theme-' + k.replace(/_/g, '-'), params[k]); });
      if (params.bg_color) {
        var hex = String(params.bg_color).replace('#', '');
        var r = parseInt(hex.substr(0, 2), 16), g = parseInt(hex.substr(2, 2), 16), b = parseInt(hex.substr(4, 2), 16);
        document.documentElement.setAttribute('data-theme', (r * 299 + g * 587 + b * 114) / 1000 < 128 ? 'dark' : 'light');
      }
    } catch (e) { /* ignore */ }
  }

  // ---------------------------------------------------------------- ui
  function renderTexts() {
    document.documentElement.lang = lang;
    document.title = T.title;
    els.title.textContent = T.title;
    els.pickText.textContent = T.pick;
    renderSub();
    if (!inTelegram) showNote(T.outside);
  }
  function renderSub() {
    els.sub.textContent = limits.known
      ? fmt('subStatus', { n: limits.total, max: limits.max, min: limits.min })
      : fmt('sub', { min: limits.min, max: limits.max });
  }
  function showNote(text) {
    els.note.textContent = text;
    els.note.hidden = !text;
  }
  function showResult(text, ok) {
    els.result.textContent = text;
    els.result.className = 'up-result ' + (ok ? 'ok' : 'err');
    els.result.hidden = !text;
  }
  function setProgress(fraction, text) {
    els.progress.hidden = false;
    els.bar.style.width = Math.max(0, Math.min(100, Math.round(fraction * 100))) + '%';
    els.progressText.textContent = text;
  }
  function hideProgress() { els.progress.hidden = true; }
  function setBusy(value) {
    busy = value;
    els.pick.disabled = value || remaining() <= 0;
  }
  function remaining() { return Math.max(0, limits.max - limits.total); }

  function haptic(type) {
    try { if (tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(type); } catch (e) { /* ignore */ }
  }

  function makeTile() {
    var li = document.createElement('li');
    li.className = 'up-thumb is-busy';
    var badge = document.createElement('span');
    badge.className = 'up-badge';
    li.appendChild(badge);
    els.grid.appendChild(li);
    return {
      el: li,
      setImage: function (blob) {
        try {
          var img = document.createElement('img');
          img.alt = '';
          img.decoding = 'async';
          img.src = URL.createObjectURL(blob);
          li.insertBefore(img, badge);
        } catch (e) { /* preview is optional */ }
      },
      setState: function (state, label) {
        li.className = 'up-thumb is-' + state;
        badge.textContent = label || '';
      }
    };
  }

  // ---------------------------------------------------------------- images
  function loadImage(file) {
    return new Promise(function (resolve, reject) {
      var url;
      try { url = URL.createObjectURL(file); } catch (e) { reject(e); return; }
      var img = new Image();
      img.onload = function () { resolve({ img: img, url: url }); };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('decode')); };
      img.src = url;
    });
  }

  function canvasToBlob(canvas) {
    return new Promise(function (resolve) {
      if (canvas.toBlob) {
        canvas.toBlob(function (blob) { resolve(blob); }, 'image/jpeg', QUALITY);
        return;
      }
      try {
        var data = atob(canvas.toDataURL('image/jpeg', QUALITY).split(',')[1]);
        var bytes = new Uint8Array(data.length);
        for (var i = 0; i < data.length; i++) bytes[i] = data.charCodeAt(i);
        resolve(new Blob([bytes], { type: 'image/jpeg' }));
      } catch (e) { resolve(null); }
    });
  }

  // -> Promise<Blob|null>: a JPEG (or an acceptable original) ready to upload
  function prepare(file) {
    var original = OK_TYPES[file.type] && file.size <= MAX_FILE_BYTES ? file : null;
    if (file.type === 'image/jpeg' && file.size <= SKIP_BYTES) return Promise.resolve(file);
    return loadImage(file).then(function (loaded) {
      var img = loaded.img;
      var w = img.naturalWidth || img.width, h = img.naturalHeight || img.height;
      if (!w || !h) { URL.revokeObjectURL(loaded.url); return original; }
      var scale = Math.min(1, MAX_SIDE / Math.max(w, h));
      var canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(w * scale));
      canvas.height = Math.max(1, Math.round(h * scale));
      var ctx = canvas.getContext('2d');
      if (!ctx) { URL.revokeObjectURL(loaded.url); return original; }
      ctx.fillStyle = '#ffffff'; // transparent PNG -> white, not black
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(loaded.url);
      return canvasToBlob(canvas).then(function (blob) {
        if (!blob || !blob.size) return original;
        if (original && original.size <= blob.size && scale === 1) return original;
        return blob.size <= MAX_FILE_BYTES ? blob : original;
      });
    }, function () {
      return original; // the browser cannot decode it (e.g. HEIC): send only if the server can take it
    });
  }

  // ---------------------------------------------------------------- network
  function errorText(code) {
    switch (code) {
      case 'not_waiting': return T.notWaiting;
      case 'unauthorized': return T.unauthorized;
      case 'too_many': return remaining() <= 0 ? fmt('full', { max: limits.max }) : fmt('tooMany', { max: limits.max });
      case 'bad_file': return T.badFile;
      case 'too_large': return T.tooLarge;
      case 'busy': return T.busy;
      case 'network': return T.network;
      default: return T.failed;
    }
  }

  function loadStatus() {
    if (!inTelegram || !window.fetch) return;
    fetch('/api/upload/status', { headers: { 'X-Telegram-Init-Data': initData }, cache: 'no-store' })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        if (!data || !data.ok) {
          if (data && data.error === 'unauthorized') showResult(T.unauthorized, false);
          return;
        }
        limits.min = data.min || limits.min;
        limits.max = data.max || limits.max;
        limits.total = data.total || 0;
        limits.known = true;
        renderSub();
        if (!data.waiting) {
          showResult(T.notWaiting, false);
          els.pick.disabled = true;
        } else if (remaining() <= 0) {
          showResult(fmt('full', { max: limits.max }), false);
          els.pick.disabled = true;
        } else if (!busy) {
          els.pick.disabled = false;
        }
      })
      .catch(function () { /* the upload itself reports problems */ });
  }

  function upload(blobs, onProgress) {
    return new Promise(function (resolve) {
      var form = new FormData();
      blobs.forEach(function (blob, i) { form.append('photo', blob, 'photo' + (i + 1) + '.jpg'); });
      var xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/upload/photos');
      xhr.setRequestHeader('X-Telegram-Init-Data', initData);
      xhr.timeout = 120000;
      if (xhr.upload) {
        xhr.upload.onprogress = function (e) { if (e.lengthComputable) onProgress(e.loaded / e.total); };
      }
      xhr.onload = function () {
        var data = null;
        try { data = JSON.parse(xhr.responseText); } catch (e) { /* not JSON */ }
        if (!data || typeof data !== 'object') data = { ok: false, error: 'failed' };
        resolve(data);
      };
      xhr.onerror = xhr.ontimeout = function () { resolve({ ok: false, error: 'network' }); };
      xhr.send(form);
    });
  }

  // ---------------------------------------------------------------- flow
  function handleFiles(fileList) {
    var files = Array.prototype.slice.call(fileList || []).filter(function (f) {
      return !f.type || f.type.indexOf('image/') === 0;
    });
    els.file.value = '';
    if (!files.length) { showResult(T.noImages, false); return; }

    showResult('', true);
    var room = remaining();
    if (room <= 0) { showResult(fmt('full', { max: limits.max }), false); return; }
    if (files.length > room) {
      showNote(fmt('trimmed', { n: room, max: limits.max }));
      files = files.slice(0, room);
    } else if (inTelegram) {
      showNote('');
    }

    setBusy(true);
    els.grid.textContent = '';
    var tiles = files.map(function () { return makeTile(); });
    var blobs = [];
    var index = 0;

    function next() {
      if (index >= files.length) return Promise.resolve();
      var i = index++;
      setProgress(0.3 * (i / files.length), fmt('preparing', { i: i + 1, n: files.length }));
      return prepare(files[i]).then(function (blob) {
        if (blob) {
          blobs.push({ blob: blob, tile: tiles[i] });
          tiles[i].setImage(blob);
          tiles[i].setState('busy');
        } else {
          tiles[i].setState('error', '!');
        }
      }, function () {
        tiles[i].setState('error', '!');
      }).then(next);
    }

    next().then(function () {
      if (!blobs.length) {
        hideProgress();
        showResult(T.badFile, false);
        setBusy(false);
        return;
      }
      if (!inTelegram) {
        // Outside Telegram there is nobody to send the photos to
        blobs.forEach(function (b) { b.tile.setState('ready'); });
        hideProgress();
        showNote(T.outside);
        setBusy(false);
        return;
      }
      setProgress(0.3, fmt('uploading', { p: 0 }));
      return upload(blobs.map(function (b) { return b.blob; }), function (f) {
        var p = Math.round(f * 100);
        setProgress(0.3 + 0.6 * f, p >= 100 ? T.saving : fmt('uploading', { p: p }));
      }).then(function (data) {
        if (data.ok) {
          var added = data.added || 0;
          limits.total = data.total || limits.total + added;
          if (data.max) limits.max = data.max;
          if (data.min) limits.min = data.min;
          limits.known = true;
          renderSub();
          blobs.forEach(function (b, i) { b.tile.setState(i < added ? 'done' : 'error', i < added ? '✓' : '!'); });
          setProgress(1, '');
          showResult(fmt('added', { n: added }), true);
          haptic('success');
          closed = true;
          setTimeout(function () {
            try { if (tg) tg.close(); } catch (e) { /* ignore */ }
          }, CLOSE_DELAY);
          return;
        }
        blobs.forEach(function (b) { b.tile.setState('error', '!'); });
        hideProgress();
        showResult(errorText(data.error), false);
        haptic('error');
        setBusy(false);
        if (data.error === 'not_waiting') els.pick.disabled = true;
        els.pickText.textContent = T.pickMore;
      });
    }).catch(function () {
      hideProgress();
      showResult(T.failed, false);
      setBusy(false);
    });
  }

  function openPicker() {
    if (busy || closed) return;
    try { els.file.click(); } catch (e) { /* ignore */ }
  }

  // ---------------------------------------------------------------- start
  applyTheme();
  renderTexts();

  if (tg) {
    try { tg.ready(); } catch (e) { /* ignore */ }
    try { tg.expand(); } catch (e) { /* ignore */ }
    try {
      tg.onEvent('themeChanged', function () { applyTheme(); });
    } catch (e) { /* ignore */ }
  }

  els.pick.addEventListener('click', openPicker);
  els.file.addEventListener('change', function () { handleFiles(els.file.files); });

  loadStatus();

  // Open the gallery right away where the platform allows it without a tap
  // (inside Telegram only; plain browsers block it and would log a warning).
  if (inTelegram) {
    setTimeout(function () {
      if (!busy && !closed) openPicker();
    }, 50);
  }
})();
