"""Admin contact helpers (shown in 'contact the admin' messages)."""
from html import escape

from config import settings
from app.i18n import DEFAULT_LANG, t


def admin_username() -> str:
    """Admin username without '@', or '' if not configured."""
    return (settings.admin_username or "").strip().lstrip("@")


def admin_link_html(lang: str = DEFAULT_LANG) -> str:
    """'<a href="https://t.me/name">@name</a>' or plain 'admin' when not configured (HTML parse mode)."""
    name = admin_username()
    if not name:
        return t(lang, "contact.admin_word")
    return f'<a href="https://t.me/{escape(name)}">@{escape(name)}</a>'


def contact_admin_html(lang: str = DEFAULT_LANG) -> str:
    """'admin (@name) bilan bog'laning' phrase in ``lang``, ready to embed in an HTML message."""
    name = admin_username()
    if not name:
        return t(lang, "contact.admin")
    return t(lang, "contact.admin_with_link", link=admin_link_html(lang))
