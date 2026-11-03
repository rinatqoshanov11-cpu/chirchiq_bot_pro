# Chirchiq Kvartira 🏠

Chirchiq shahridagi kvartira ijarasi va sotuvi uchun Telegram bot + Telegram Mini App.

**Bot:** [@Chirchiq_Arenda_bot](https://t.me/Chirchiq_Arenda_bot)

## Imkoniyatlar

- 📱 **Mini ilova**: rasmli e'lonlar, filtr (ijara/sotuv, xonalar, narx, saralash), galereya, xarita, egasi bilan bir bosishda bog'lanish, "Mening e'lonlarim"
- ➕ **E'lon qo'shish** botda, deyarli hammasi tugma bilan: Chirchiq hududlari, narx (`3 mln`, `$45 000`), maydon, qavat, tavsif belgilari, joylashuv, rasmlar, tasdiqlashdan oldin tahrirlash
- 🌐 **Uch til**: o'zbek, rus, ingliz
- ✅ **Admin panel** (`/admin`): e'lonlarni tasdiqlash/rad etish, statistika, foydalanuvchilar, xabar yuborish

## Texnologiyalar

Python 3.13 · aiogram 3 · aiohttp · SQLAlchemy 2 (async) · PostgreSQL

## Tuzilishi

```
main.py                 bot + mini ilova serverini ishga tushiradi
config/settings.py      sozlamalar (.env yoki muhit o'zgaruvchilari)
app/handlers/           bot buyruqlari va qadamlari
app/keyboards/          tugmalar
app/i18n/               uz / ru / en matnlari
app/models/             baza jadvallari
app/services/           baza bilan ishlash
app/webapp/             mini ilova: API (server.py) va sahifa (static/)
app/utils/              narx, hududlar, formatlash, bot profili
assets/avatar.png       bot rasmi
render.yaml             Render.com sozlamasi
```

## Ishga tushirish (kompyuterda)

```bash
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
python main.py
```

`.env` faylida `BOT_TOKEN`, `ADMIN_IDS`, `DATABASE_URL` ni to'ldiring. Jadvallar birinchi ishga tushishda o'zi yaratiladi.

Mini ilova Telegramda ochilishi uchun HTTPS manzil kerak (`WEBAPP_URL`).

## Serverga joylash (Render.com, bepul)

1. Bazani [Neon](https://neon.tech) da yarating, *Connection string* ni oling.
2. Render → **New Web Service** → shu repo. Build: `pip install -r requirements.txt`, Start: `python main.py`, Instance: **Free**.
3. Environment: `BOT_TOKEN`, `ADMIN_IDS`, `ADMIN_USERNAME`, `DATABASE_URL`. Mini ilova manzili Render'dan o'zi olinadi.
4. Botni uxlatmaslik uchun [cron-job.org](https://cron-job.org) da servis manziliga har 10 daqiqada so'rov qo'ying.

Har bir `git push` dan keyin Render yangi kodni o'zi oladi.

## Xavfsizlik

`.env`, tokenlar va parollar repoga **qo'shilmaydi** (`.gitignore`).
