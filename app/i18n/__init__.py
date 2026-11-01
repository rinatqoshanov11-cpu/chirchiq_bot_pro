"""Bot translations: Uzbek (default), Russian, English.

Every module ``app/i18n/texts_<area>.py`` defines ``TEXTS = {key: {"uz": ..., "ru": ..., "en": ...}}``.
They are discovered and merged here at import time; a key defined in two files raises at import.

Usage::

    from app.i18n import t, variants
    t(lang, "btn.cancel")                       # "❌ Bekor qilish" / "❌ Отмена" / "❌ Cancel"
    t(lang, "lang.current", name="Русский")     # str.format(**kwargs) when kwargs are given
    F.text.in_(variants("btn.cancel"))          # matches the label in any language
"""
import importlib
import pkgutil
from typing import Dict, Iterable, List, Optional

LANGS = ("uz", "ru", "en")
DEFAULT_LANG = "uz"
LANG_NAMES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

TEXTS: Dict[str, Dict[str, str]] = {}


def _load_texts() -> None:
    """Merge TEXTS from every app/i18n/texts_*.py module."""
    origin: Dict[str, str] = {}
    for module_info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        name = module_info.name
        if not name.startswith("texts_"):
            continue
        module = importlib.import_module(f"{__name__}.{name}")
        texts = getattr(module, "TEXTS", None)
        if not isinstance(texts, dict):
            raise TypeError(f"app.i18n.{name}: TEXTS must be a dict")
        for key, value in texts.items():
            if key in TEXTS:
                raise ValueError(
                    f"Duplicate i18n key {key!r} in app.i18n.{name} (already defined in app.i18n.{origin[key]})"
                )
            if not isinstance(value, dict):
                raise TypeError(f"app.i18n.{name}: TEXTS[{key!r}] must be a dict of language -> text")
            TEXTS[key] = value
            origin[key] = name


_load_texts()


def normalize_lang(code: Optional[str]) -> str:
    """Telegram language_code / any code -> 'uz' | 'ru' | 'en'."""
    code = (code or "").strip().lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    return DEFAULT_LANG


def t(lang: Optional[str], key: str, **kwargs) -> str:
    """Text for ``key`` in ``lang`` (fallback: Uzbek, then the key itself), formatted with kwargs."""
    entry = TEXTS.get(key)
    if entry is None:
        text = key
    else:
        text = entry.get(lang or DEFAULT_LANG) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def variants(key: str) -> List[str]:
    """The text of ``key`` in every language (duplicates removed), e.g. for F.text.in_(...)."""
    entry = TEXTS.get(key) or {}
    result: List[str] = []
    for lang in LANGS:
        text = entry.get(lang)
        if text and text not in result:
            result.append(text)
    return result


def match_key(text: Optional[str], keys: Iterable[str]) -> Optional[str]:
    """Which of ``keys`` has ``text`` as its label in any language (None if none)."""
    if not text:
        return None
    for key in keys:
        if text in variants(key):
            return key
    return None


def is_text(text: Optional[str], key: str) -> bool:
    """True if ``text`` equals the label of ``key`` in any language."""
    return bool(text) and text in variants(key)


__all__ = [
    "LANGS",
    "DEFAULT_LANG",
    "LANG_NAMES",
    "TEXTS",
    "t",
    "variants",
    "normalize_lang",
    "match_key",
    "is_text",
]
