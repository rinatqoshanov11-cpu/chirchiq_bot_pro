"""Chirchiq residential areas offered as one-tap buttons in the address step.

Names were cross-checked (Nov 2026) against Chirchiq apartment ads on OLX.uz,
Tashtrans bus routes (tashtrans.uz/marshruti-chirchika) and OpenStreetMap.
Microdistricts 5-7 are left out on purpose: no apartment ads use them.
Most common areas first.

CHIRCHIQ_AREAS holds the canonical (Uzbek) names; AREA_LABELS gives each one's
button label per language. The "other area" button label is i18n key "btn.other_area".
"""
from typing import Dict, Optional

CHIRCHIQ_AREAS = [
    "1-mikrorayon (Oktyabr)",
    "2-mikrorayon",
    "3-mikrorayon",
    "4-mikrorayon",
    "8-mikrorayon",
    "9-mikrorayon",
    "10-mikrorayon",
    "Markaz (Navoiy)",
    "Troitsk",
    "Oqqovoq",
    "Arancha",
    "500-ka (Gorpark)",
    "Roshcha",
    "Yangi O'zbekiston massivi",
    "Konstruktorlar mavzesi",
    "Ximposyolok",
    "Jaloyir",
    "Nijniy Komsomolsk",
]

# Uzbek label (kept for old code; the localized one is t(lang, "btn.other_area"))
OTHER_AREA = "✍️ Boshqa hudud"

# Uzbek city name (kept for old code; the localized one is t(lang, "city"))
CITY = "Chirchiq"

AREA_LABELS: Dict[str, Dict[str, str]] = {
    "1-mikrorayon (Oktyabr)": {"uz": "1-mikrorayon (Oktyabr)", "ru": "1-микрорайон (Октябрь)", "en": "Microdistrict 1 (Oktyabr)"},
    "2-mikrorayon": {"uz": "2-mikrorayon", "ru": "2-микрорайон", "en": "Microdistrict 2"},
    "3-mikrorayon": {"uz": "3-mikrorayon", "ru": "3-микрорайон", "en": "Microdistrict 3"},
    "4-mikrorayon": {"uz": "4-mikrorayon", "ru": "4-микрорайон", "en": "Microdistrict 4"},
    "8-mikrorayon": {"uz": "8-mikrorayon", "ru": "8-микрорайон", "en": "Microdistrict 8"},
    "9-mikrorayon": {"uz": "9-mikrorayon", "ru": "9-микрорайон", "en": "Microdistrict 9"},
    "10-mikrorayon": {"uz": "10-mikrorayon", "ru": "10-микрорайон", "en": "Microdistrict 10"},
    "Markaz (Navoiy)": {"uz": "Markaz (Navoiy)", "ru": "Центр (Навои)", "en": "Center (Navoi)"},
    "Troitsk": {"uz": "Troitsk", "ru": "Троицк", "en": "Troitsk"},
    "Oqqovoq": {"uz": "Oqqovoq", "ru": "Аккавак", "en": "Akkavak"},
    "Arancha": {"uz": "Arancha", "ru": "Аранча", "en": "Arancha"},
    "500-ka (Gorpark)": {"uz": "500-ka (Gorpark)", "ru": "500-ка (Горпарк)", "en": "500-ka (Gorpark)"},
    "Roshcha": {"uz": "Roshcha", "ru": "Роща", "en": "Roshcha"},
    "Yangi O'zbekiston massivi": {"uz": "Yangi O'zbekiston massivi", "ru": "Массив Янги Узбекистан", "en": "Yangi Uzbekistan area"},
    "Konstruktorlar mavzesi": {"uz": "Konstruktorlar mavzesi", "ru": "Квартал Конструкторов", "en": "Konstruktorlar quarter"},
    "Ximposyolok": {"uz": "Ximposyolok", "ru": "Химпосёлок", "en": "Khimposyolok"},
    "Jaloyir": {"uz": "Jaloyir", "ru": "Джалаир", "en": "Jaloyir"},
    "Nijniy Komsomolsk": {"uz": "Nijniy Komsomolsk", "ru": "Нижний Комсомольск", "en": "Nizhny Komsomolsk"},
}

# Any label (any language, case-insensitive) -> canonical Uzbek name
_LABEL_INDEX: Dict[str, str] = {}
for _canonical in CHIRCHIQ_AREAS:
    _LABEL_INDEX[_canonical.casefold()] = _canonical
    for _label in AREA_LABELS.get(_canonical, {}).values():
        _LABEL_INDEX.setdefault(_label.casefold(), _canonical)


def area_label(canonical: str, lang: str = "uz") -> str:
    """Button / address label of an area in ``lang`` (falls back to Uzbek, then to the input)."""
    labels = AREA_LABELS.get(canonical) or {}
    return labels.get(lang) or labels.get("uz") or canonical


def area_from_label(text: Optional[str]) -> Optional[str]:
    """Canonical Uzbek area name for a button label in any language, or None."""
    if not text:
        return None
    return _LABEL_INDEX.get(text.strip().casefold())
