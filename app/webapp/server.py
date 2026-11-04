"""aiohttp backend for the "Chirchiq Kvartira" Telegram Mini App.

The server runs inside the bot process (see ``main.py``) and serves:

* ``/``            -> ``app/webapp/static/index.html`` (the mini app)
* ``/static/...``  -> files under ``app/webapp/static/``
* ``/api/...``     -> JSON API

All error responses are JSON ``{"error": "..."}``; a traceback never reaches
the client. Text fields are returned raw (not HTML-escaped) - the frontend
must insert them with ``textContent``.

Language: every listing endpoint localizes ``type_text``, ``status_text`` and
``price_text``. The language comes from the ``lang`` query parameter
(``uz`` | ``ru`` | ``en``), else the ``X-Lang`` header, else Uzbek.
"""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from aiogram import Bot
from aiogram.utils.web_app import WebAppUser, safe_parse_webapp_init_data
from aiohttp import web
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.i18n import DEFAULT_LANG, LANGS, t
from app.models import Apartment, User
from app.models.apartment import ApartmentStatus, ApartmentType
from app.models.base import async_session_maker
from app.services.apartment_service import ApartmentService
from app.services.user_service import UserService
from app.utils.formatters import format_price
from config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"
PHOTO_CACHE_DIR = PROJECT_ROOT / "cache" / "photos"

INIT_DATA_HEADER = "X-Telegram-Init-Data"
LANG_HEADER = "X-Lang"
DEFAULT_LIMIT = 12
MAX_LIMIT = 30
MAX_ROOMS = 6  # "6" in the API means 6 rooms or more
MAX_PARALLEL_DOWNLOADS = 4

TYPE_TEXT = {
    ApartmentType.RENT: {"uz": "Ijaraga", "ru": "Аренда", "en": "For rent"},
    ApartmentType.SALE: {"uz": "Sotiladi", "ru": "Продажа", "en": "For sale"},
}
STATUS_TEXT = {
    ApartmentStatus.PENDING: {"uz": "Tekshiruvda", "ru": "На проверке", "en": "Under review"},
    ApartmentStatus.APPROVED: {"uz": "Faol", "ru": "Активно", "en": "Active"},
    ApartmentStatus.REJECTED: {"uz": "Rad etilgan", "ru": "Отклонено", "en": "Rejected"},
    ApartmentStatus.ARCHIVED: {"uz": "Arxivda", "ru": "В архиве", "en": "Archived"},
}

# Used only if app.utils.formatters.format_price does not accept ``lang`` yet
_SOM_TEXT = {"uz": "so'm", "ru": "сум", "en": "UZS"}
_NEGOTIABLE_TEXT = {"uz": "Kelishiladi", "ru": "Договорная", "en": "Negotiable"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def json_error(status: int, message: str) -> web.Response:
    """Build a JSON error response."""
    return web.json_response({"error": message}, status=status)


class ApiError(Exception):
    """Raised inside handlers; converted to a JSON error by the middleware."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def request_lang(request: web.Request) -> str:
    """Language of the request: ``?lang=``, else the ``X-Lang`` header, else Uzbek."""
    for raw in (request.query.get("lang"), request.headers.get(LANG_HEADER)):
        code = (raw or "").strip().lower()[:2]
        if code in LANGS:
            return code
    return DEFAULT_LANG


def _format_price_supports_lang() -> bool:
    try:
        params = inspect.signature(format_price).parameters
    except (TypeError, ValueError):
        return False
    return "lang" in params or any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
    )


_FORMAT_PRICE_HAS_LANG = _format_price_supports_lang()


def localized_price(price: Any, currency: str, lang: str) -> str:
    """format_price in ``lang`` (with a local fallback for an older formatter)."""
    if _FORMAT_PRICE_HAS_LANG:
        return format_price(price, currency, lang=lang)
    if price is None:
        return _NEGOTIABLE_TEXT.get(lang, _NEGOTIABLE_TEXT[DEFAULT_LANG])
    text = format_price(price, currency)
    if lang != DEFAULT_LANG and text.endswith(" so'm"):
        text = text[: -len("so'm")] + _SOM_TEXT.get(lang, "so'm")
    return text


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value) or "")


def _iso(value: Optional[datetime]) -> Optional[str]:
    """Naive timestamps are stored in UTC -> mark them as such ('Z')."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _loaded_owner(apartment: Apartment) -> Optional[User]:
    """Return apartment.owner without triggering a lazy load."""
    return apartment.__dict__.get("owner")


def listing_to_dict(
    apartment: Apartment, include_private: bool = False, lang: str = DEFAULT_LANG
) -> dict:
    """Serialize an Apartment to the mini app Listing JSON object.

    ``include_private`` adds the owner-only fields (phone number, contact
    name); the public catalog never includes them. ``lang`` localizes
    ``type_text``, ``status_text`` and ``price_text``.
    """
    if lang not in LANGS:
        lang = DEFAULT_LANG
    apartment_type = ApartmentType(_enum_value(apartment.type))
    status = ApartmentStatus(_enum_value(apartment.status))
    currency = (apartment.currency or "UZS").strip().upper()
    if currency not in ("UZS", "USD"):
        currency = "UZS"

    price_text = localized_price(apartment.price, currency, lang)
    if apartment_type == ApartmentType.RENT and apartment.price is not None:
        price_text += t(lang, "price.per_month")

    photos = apartment.photos or []
    owner = _loaded_owner(apartment)

    data = {
        "id": apartment.id,
        "type": apartment_type.value,
        "type_text": TYPE_TEXT[apartment_type][lang],
        "rooms": apartment.rooms,
        "area": apartment.area,
        "floor": apartment.floor,
        "total_floors": apartment.total_floors,
        "address": apartment.address or "",
        "district": apartment.district,
        "latitude": apartment.latitude,
        "longitude": apartment.longitude,
        "price": apartment.price,
        "currency": currency,
        "price_text": price_text,
        "description": apartment.description,
        "photos": [f"/api/photos/{apartment.id}/{i}" for i in range(len(photos))],
        "view_count": apartment.view_count or 0,
        "contact_count": apartment.contact_count or 0,
        "created_at": _iso(apartment.created_at),
        "owner_name": getattr(owner, "full_name", None) if owner is not None else None,
        "status": status.value,
        "status_text": STATUS_TEXT[status][lang],
    }
    if include_private:
        data["phone_number"] = apartment.phone_number
        data["contact_name"] = apartment.contact_name
    return data


def _parse_init_data(raw: Optional[str]) -> Optional[WebAppUser]:
    if not raw:
        return None
    try:
        parsed = safe_parse_webapp_init_data(settings.bot_token, raw)
    except ValueError:
        return None
    except Exception as e:  # malformed JSON inside init data etc.
        logger.debug("initData parse failed: %s", e)
        return None
    return parsed.user


def get_tg_user(request: web.Request, allow_query: bool = False) -> Optional[WebAppUser]:
    """Validate Telegram initData and return the WebAppUser (or None).

    The header ``X-Telegram-Init-Data`` is checked first. The ``init_data``
    query parameter is accepted only when ``allow_query`` is True (used by the
    photos endpoint because ``<img>`` tags cannot send headers).
    """
    user = _parse_init_data(request.headers.get(INIT_DATA_HEADER))
    if user is None and allow_query:
        user = _parse_init_data(request.query.get("init_data"))
    return user


def require_tg_user(request: web.Request) -> WebAppUser:
    user = get_tg_user(request)
    if user is None:
        raise ApiError(401, "unauthorized")
    return user


def _parse_int(
    raw: Optional[str],
    name: str,
    *,
    default: Optional[int] = None,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> Optional[int]:
    """Parse an integer query parameter; 400 on bad input."""
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid {name}")
    if minimum is not None and value < minimum:
        raise ApiError(400, f"invalid {name}")
    if maximum is not None and value > maximum:
        raise ApiError(400, f"invalid {name}")
    return value


def _path_int(request: web.Request, name: str) -> int:
    try:
        value = int(request.match_info[name])
    except (KeyError, ValueError):
        raise ApiError(400, f"invalid {name}")
    if value < 0:
        raise ApiError(400, f"invalid {name}")
    return value


def _is_admin(user: Optional[User], telegram_id: int) -> bool:
    if telegram_id in settings.admin_ids:
        return True
    return bool(user is not None and user.is_admin)


def _is_public(apartment: Apartment) -> bool:
    return bool(apartment.is_active) and (
        _enum_value(apartment.status) == ApartmentStatus.APPROVED.value
    )


async def _get_public_listing(session: AsyncSession, apartment_id: int) -> Apartment:
    """Approved + active listing with owner loaded, else 404."""
    apartment = await ApartmentService.get_by_id(session, apartment_id, load_owner=True)
    if apartment is None or not _is_public(apartment):
        raise ApiError(404, "listing not found")
    return apartment


# ---------------------------------------------------------------------------
# Photo cache
# ---------------------------------------------------------------------------

def photo_cache_path(file_id: str) -> Path:
    digest = hashlib.sha256(file_id.encode("utf-8")).hexdigest()
    return PHOTO_CACHE_DIR / f"{digest}.jpg"


def _read_file(path: Path) -> Optional[bytes]:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as e:
        logger.warning("Photo cache read failed for %s: %s", path, e)
        return None


def _write_file_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except OSError as e:
        logger.warning("Photo cache write failed for %s: %s", path, e)
        try:
            tmp.unlink()
        except OSError:
            pass


def _get_semaphore(app: web.Application) -> asyncio.Semaphore:
    """Download semaphore stored on the app (created lazily on the running loop)."""
    semaphore = app.get("photo_semaphore")
    if semaphore is None:
        semaphore = asyncio.Semaphore(MAX_PARALLEL_DOWNLOADS)
        app["photo_semaphore"] = semaphore
    return semaphore


async def get_photo_bytes(bot: Bot, file_id: str, semaphore: asyncio.Semaphore) -> Optional[bytes]:
    """Return the photo bytes from the disk cache or download them from Telegram."""
    path = photo_cache_path(file_id)
    data = await asyncio.to_thread(_read_file, path)
    if data:
        return data

    async with semaphore:
        # Another request may have cached it while we were waiting
        data = await asyncio.to_thread(_read_file, path)
        if data:
            return data
        try:
            tg_file = await bot.get_file(file_id)
            file_path = getattr(tg_file, "file_path", None)
            if not file_path:
                return None
            buffer = await bot.download_file(file_path)
        except Exception as e:
            logger.warning("Photo download failed (file_id=%s...): %s", file_id[:12], e)
            return None

    if buffer is None:
        return None
    data = buffer.getvalue() if hasattr(buffer, "getvalue") else buffer.read()
    if not data:
        return None
    await asyncio.to_thread(_write_file_atomic, path, data)
    return data


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

routes = web.RouteTableDef()


@routes.get("/")
async def index(request: web.Request) -> web.StreamResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise ApiError(404, "mini app is not built yet (static/index.html missing)")
    return web.FileResponse(index_path, headers={"Cache-Control": "no-cache"})


@routes.get("/static/{path:.*}")
async def static_file(request: web.Request) -> web.StreamResponse:
    """Serve files under app/webapp/static/ (checked up front so 404s are JSON)."""
    base = STATIC_DIR.resolve()
    rel = request.match_info.get("path", "")
    try:
        target = (base / rel).resolve()
    except (OSError, ValueError):
        raise ApiError(404, "file not found")
    if target == base or not target.is_relative_to(base) or not target.is_file():
        raise ApiError(404, "file not found")
    return web.FileResponse(target, headers={"Cache-Control": "no-cache"})


@routes.get("/api/listings")
async def api_listings(request: web.Request) -> web.Response:
    q = request.query
    lang = request_lang(request)

    type_param = (q.get("type") or "all").lower()
    if type_param not in ("all", "rent", "sale"):
        raise ApiError(400, "invalid type")

    rooms = _parse_int(q.get("rooms"), "rooms", minimum=1, maximum=MAX_ROOMS)

    currency = q.get("currency")
    if currency:
        currency = currency.upper()
        if currency not in ("UZS", "USD"):
            raise ApiError(400, "invalid currency")
    else:
        currency = None

    min_price = _parse_int(q.get("min_price"), "min_price", minimum=0)
    max_price = _parse_int(q.get("max_price"), "max_price", minimum=0)

    sort = (q.get("sort") or "new").lower()
    if sort not in ("new", "cheap", "expensive"):
        raise ApiError(400, "invalid sort")

    offset = _parse_int(q.get("offset"), "offset", default=0, minimum=0)
    limit = _parse_int(q.get("limit"), "limit", default=DEFAULT_LIMIT, minimum=1)
    limit = min(limit, MAX_LIMIT)

    conditions = [
        Apartment.is_active == True,  # noqa: E712
        Apartment.status == ApartmentStatus.APPROVED,
    ]
    if type_param != "all":
        conditions.append(Apartment.type == ApartmentType(type_param))
    if rooms is not None:
        if rooms >= MAX_ROOMS:
            conditions.append(Apartment.rooms >= MAX_ROOMS)
        else:
            conditions.append(Apartment.rooms == rooms)
    if currency is not None:
        conditions.append(Apartment.currency == currency)
        # Price bounds only make sense inside one currency
        if min_price is not None:
            conditions.append(Apartment.price >= min_price)
        if max_price is not None:
            conditions.append(Apartment.price <= max_price)

    where = and_(*conditions)

    if sort == "cheap":
        order = (Apartment.currency.asc(), Apartment.price.asc(), Apartment.id.asc())
    elif sort == "expensive":
        order = (Apartment.currency.asc(), Apartment.price.desc(), Apartment.id.desc())
    else:
        order = (Apartment.created_at.desc(), Apartment.id.desc())

    async with async_session_maker() as session:
        total = (
            await session.execute(select(func.count(Apartment.id)).where(where))
        ).scalar_one()
        result = await session.execute(
            select(Apartment)
            .options(selectinload(Apartment.owner))
            .where(where)
            .order_by(*order)
            .offset(offset)
            .limit(limit)
        )
        items = [listing_to_dict(a, lang=lang) for a in result.scalars().all()]

    return web.json_response(
        {"items": items, "total": total, "offset": offset, "limit": limit}
    )


@routes.get("/api/listings/{id}")
async def api_listing(request: web.Request) -> web.Response:
    apartment_id = _path_int(request, "id")
    lang = request_lang(request)
    async with async_session_maker() as session:
        apartment = await _get_public_listing(session, apartment_id)
        new_count = (
            await session.execute(
                update(Apartment)
                .where(Apartment.id == apartment.id)
                .values(view_count=Apartment.view_count + 1)
                .returning(Apartment.view_count)
                .execution_options(synchronize_session=False)
            )
        ).scalar_one()
        await session.commit()
        apartment.view_count = new_count
        data = listing_to_dict(apartment, lang=lang)
    return web.json_response(data)


@routes.post("/api/listings/{id}/contact")
async def api_listing_contact(request: web.Request) -> web.Response:
    require_tg_user(request)
    apartment_id = _path_int(request, "id")
    async with async_session_maker() as session:
        apartment = await _get_public_listing(session, apartment_id)
        await session.execute(
            update(Apartment)
            .where(Apartment.id == apartment.id)
            .values(contact_count=Apartment.contact_count + 1)
        )
        await session.commit()
        payload = {
            "phone": apartment.phone_number,
            "contact_name": apartment.contact_name,
        }
    return web.json_response(payload)


@routes.get("/api/my")
async def api_my(request: web.Request) -> web.Response:
    tg_user = require_tg_user(request)
    lang = request_lang(request)
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, tg_user.id)
        if user is None or not user.is_registered:
            return web.json_response({"items": [], "registered": False})
        result = await session.execute(
            select(Apartment)
            .options(selectinload(Apartment.owner))
            .where(Apartment.owner_id == user.id)
            .order_by(Apartment.created_at.desc(), Apartment.id.desc())
        )
        items = [
            listing_to_dict(a, include_private=True, lang=lang)
            for a in result.scalars().all()
        ]
    return web.json_response({"items": items, "registered": True})


@routes.delete("/api/my/{id}")
async def api_my_delete(request: web.Request) -> web.Response:
    tg_user = require_tg_user(request)
    apartment_id = _path_int(request, "id")
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, tg_user.id)
        if user is None or not user.is_registered:
            raise ApiError(403, "forbidden")
        apartment = await ApartmentService.get_by_id(session, apartment_id, load_owner=False)
        if apartment is None:
            raise ApiError(404, "listing not found")
        if apartment.owner_id != user.id:
            raise ApiError(403, "forbidden")
        await ApartmentService.delete_apartment(session, apartment)
        logger.info("Mini app: user %s deleted listing #%s", tg_user.id, apartment_id)
    return web.json_response({"ok": True})


@routes.get("/api/photos/{listing_id}/{index}")
async def api_photo(request: web.Request) -> web.Response:
    listing_id = _path_int(request, "listing_id")
    index = _path_int(request, "index")
    bot: Bot = request.app["bot"]

    async with async_session_maker() as session:
        apartment = await ApartmentService.get_by_id(session, listing_id, load_owner=True)
        if apartment is None:
            raise ApiError(404, "listing not found")

        if not _is_public(apartment):
            tg_user = get_tg_user(request, allow_query=True)
            if tg_user is None:
                raise ApiError(401, "unauthorized")
            owner = _loaded_owner(apartment)
            is_owner = owner is not None and owner.telegram_id == tg_user.id
            if not is_owner:
                viewer = await UserService.get_by_telegram_id(session, tg_user.id)
                if not _is_admin(viewer, tg_user.id):
                    raise ApiError(403, "forbidden")

        photos = list(apartment.photos or [])

    if index >= len(photos):
        raise ApiError(404, "photo not found")
    file_id = photos[index]
    if not isinstance(file_id, str) or not file_id:
        raise ApiError(404, "photo not found")

    data = await get_photo_bytes(bot, file_id, _get_semaphore(request.app))
    if not data:
        raise ApiError(404, "photo not found")

    return web.Response(
        body=data,
        content_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@routes.get("/api/me")
async def api_me(request: web.Request) -> web.Response:
    tg_user = require_tg_user(request)
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, tg_user.id)
        payload = {
            "telegram_id": tg_user.id,
            "registered": bool(user is not None and user.is_registered),
            "full_name": user.full_name if user is not None else None,
            "is_admin": _is_admin(user, tg_user.id),
        }
    return web.json_response(payload)


# ---------------------------------------------------------------------------
# Middleware + app factory
# ---------------------------------------------------------------------------

@web.middleware
async def error_middleware(request: web.Request, handler):
    """Turn every error into JSON; never leak a traceback."""
    try:
        response = await handler(request)
        # e.g. the static handler returns (not raises) a plain-text 404
        if (
            response.status >= 400
            and getattr(response, "content_type", "") != "application/json"
        ):
            return json_error(response.status, response.reason or "error")
        return response
    except ApiError as e:
        return json_error(e.status, e.message)
    except web.HTTPException as e:
        if e.status >= 400:
            return json_error(e.status, e.reason or "error")
        raise
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Mini app: unhandled error on %s %s", request.method, request.path)
        return json_error(500, "internal server error")


# Read-only endpoints the public website (GitHub Pages) may call from another origin.
# Everything else (my listings, contact, delete) stays same-origin + initData only.
PUBLIC_API_PREFIXES = ("/api/listings", "/api/photos/")
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "X-Lang",
    "Access-Control-Max-Age": "86400",
}


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """Allow cross-origin GET on the public listing endpoints only."""
    public = request.path.startswith(PUBLIC_API_PREFIXES) and request.method in ("GET", "OPTIONS")
    if public and request.method == "OPTIONS":
        return web.Response(status=204, headers=CORS_HEADERS)
    response = await handler(request)
    if public:
        response.headers.update(CORS_HEADERS)
    return response


def create_app(bot: Bot) -> web.Application:
    """Create the aiohttp application for the mini app."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # cors first (outermost) so JSON error responses get the headers too
    app = web.Application(middlewares=[cors_middleware, error_middleware], client_max_size=64 * 1024)
    app["bot"] = bot
    app.add_routes(routes)
    return app


async def start_webapp(bot: Bot) -> Optional[web.AppRunner]:
    """Start the mini app web server. Returns None (and logs) if it cannot bind."""
    app = create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    host, port = settings.webapp_host, settings.webapp_port
    site = web.TCPSite(runner, host, port)
    try:
        await site.start()
    except OSError as e:
        logger.error("Mini app web server could not bind %s:%s: %s", host, port, e)
        await runner.cleanup()
        return None
    except Exception as e:
        logger.error("Mini app web server failed to start: %s", e)
        await runner.cleanup()
        return None

    logger.info("Mini app web server listening on http://%s:%s", host, port)
    if settings.webapp_url:
        logger.info("Mini app public URL: %s", settings.webapp_url)
    else:
        logger.info("WEBAPP_URL is empty: mini app buttons are hidden until it is set")
    return runner


async def stop_webapp(runner: Optional[web.AppRunner]) -> None:
    """Stop the mini app web server."""
    if runner is None:
        return
    try:
        await runner.cleanup()
        logger.info("Mini app web server stopped")
    except Exception as e:
        logger.warning("Mini app web server cleanup failed: %s", e)
