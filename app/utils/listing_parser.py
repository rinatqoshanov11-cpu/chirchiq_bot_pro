"""Free-text listing parser for the admin "Forward orqali import" feature.

Given the text of an apartment ad (OLX, a Telegram channel, a realtor's message;
Russian / Uzbek Latin / Uzbek Cyrillic / mixed) it extracts the fields it can:
type, rooms, area, floor / total floors, price + currency, phone, Chirchiq area
and street, plus a tidied description.

Pure functions: no I/O, no aiogram imports. ``parse_listing_text`` never raises.
Notes for the admin are Uzbek (admin-only feature).
"""
import html
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.utils.areas import AREA_LABELS, CHIRCHIQ_AREAS, CITY, area_label
from app.utils.formatters import validate_phone_number
from app.utils.price import PRICE_LIMITS, parse_price, resolve_price

__all__ = ["ParsedListing", "parse_listing_text", "address_from"]


@dataclass
class ParsedListing:
    type: Optional[str] = None          # 'rent' | 'sale' | None
    rooms: Optional[int] = None         # 1..10
    area: Optional[float] = None        # m², 5..1000
    floor: Optional[int] = None         # 1..100
    total_floors: Optional[int] = None  # >= floor, <= 100
    price: Optional[int] = None
    currency: Optional[str] = None      # 'UZS' | 'USD' (set whenever price is set)
    phone: Optional[str] = None         # E.164 via validate_phone_number
    area_name: Optional[str] = None     # canonical name from CHIRCHIQ_AREAS, or None
    street: Optional[str] = None        # short street/house fragment, or None
    description: str = ""               # original text, phones removed, whitespace tidied, cut
    found: list = field(default_factory=list)   # names of fields detected, in order
    notes: list = field(default_factory=list)   # short Uzbek notes for the admin


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

ROOMS_RANGE = (1, 10)
AREA_RANGE = (5.0, 1000.0)
FLOOR_RANGE = (1, 100)
STREET_MAX = 60
_MAX_INPUT = 20_000  # longer texts are cut before parsing (speed + sanity)

# ---------------------------------------------------------------------------
# Character classes / helpers
# ---------------------------------------------------------------------------

_L = r"a-zа-яёўқғҳ"          # letters (lower-case; the work text is lower-cased)
_AP = r"'ʻ‘’`"               # apostrophes used in Uzbek Latin
_NL = rf"(?<![{_L}])"        # not preceded by a letter
_NLA = rf"(?![{_L}])"        # not followed by a letter
_ND = r"(?<![\d.,/])"        # not preceded by a digit / separator (number start)

_TAG_RE = re.compile(r"</?[a-zA-Z][^<>]{0,200}>")
_ZERO_WIDTH_RE = re.compile(r"[​‌‍⁠﻿]")
_SPACES_RE = re.compile(r"[      \t]")


def _lower_keep_len(text: str) -> str:
    """Lower-case the text without changing its length (keeps spans aligned)."""
    out = []
    for ch in text:
        low = ch.lower()
        out.append(low if len(low) == 1 else ch)
    return "".join(out)


def _to_float(raw: str) -> Optional[float]:
    try:
        return float(raw.replace(",", ".").replace(" ", ""))
    except (TypeError, ValueError):
        return None


def _in(value, low, high) -> bool:
    return value is not None and low <= value <= high


def _mask(text: str, spans: List[Tuple[int, int]]) -> str:
    """Replace the given spans with '#' so later passes do not re-read them."""
    if not spans:
        return text
    chars = list(text)
    for start, end in spans:
        for i in range(max(0, start), min(len(chars), end)):
            chars[i] = "#"
    return "".join(chars)


# ---------------------------------------------------------------------------
# Phones
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(
    r"(?<![\d+])"
    r"(?:\+?\s?998[\s\-]?)?"                          # optional country code
    r"\(?(?:20|33|50|55|6\d|7\d|88|9[013-9])\)?[\s\-]?"  # operator / city code
    r"\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
    r"(?!\d)"
)
# A 9-digit run followed by a money / size word is not a phone ("998000000 сум")
_PHONE_TAIL_BAD = re.compile(
    rf"^\s*(?:сум|сўм|so[{_AP}]?m|som|sum|uzs|\$|usd|у\.?\s?е|долл|dollar|млн|mln|"
    r"тыс|ming|минг|млрд|k\b|к\b|м²|m²|м2|m2|кв|kv|%)",
    re.I,
)
_PHONE_LABEL_RE = re.compile(
    rf"(?:(?:тел|tel|phone|телефон|telefon|aloqa|алоқа|murojaat|мурожаат|контакт\w*|kontakt\w*|"
    rf"звонит[ье]|zvonit[ye]|qo[{_AP}]?ng[{_AP}]?iroq|қўнғироқ|номер|raqam\w*|рақам\w*|"
    rf"связь|whatsapp|telegram|tg|call)\.?\s*(?:uchun|учун|для\s*связи|по\s*телефону)?\s*[:\-–]?\s*"
    r"|[☎📞📱📲✆]️?\s*[:\-–]?\s*)+$",
    re.I,
)


def _find_phones(text: str) -> List[Tuple[int, int, str]]:
    """(start, end, E.164) for every phone number in the text, in order."""
    phones = []
    for m in _PHONE_RE.finditer(text):
        tail = text[m.end():m.end() + 12]
        if _PHONE_TAIL_BAD.search(tail):
            continue
        if text[max(0, m.start() - 1):m.start()] == "$":
            continue
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) not in (9, 12):
            continue
        if len(digits) == 12 and not digits.startswith("998"):
            continue
        e164 = validate_phone_number(m.group(0))
        if not e164 or not e164.startswith("+998"):
            continue
        phones.append((m.start(), m.end(), e164))
    return phones


# ---------------------------------------------------------------------------
# Type
# ---------------------------------------------------------------------------

_RENT_STRONG_RE = re.compile(
    _NL + r"(?:аренд\w*|сда[её]тся|сда[её]м|сдам|сдаю|сдадим|сдача|сдается|"
    rf"ijara\w*|ижара\w*|arenda\w*|арендага|посуточн\w*|kunlik|sutkalik|ijarachi\w*|kvartirant\w*)" + _NLA
)
_RENT_WEAK_RE = re.compile(
    _NL + r"(?:в\s*месяц|мес(?:яц\w*|\.)?|oylik|oyiga|ойлик|ойига|per\s*month|/\s*month|monthly)" + _NLA
)
_SALE_STRONG_RE = re.compile(
    _NL + r"(?:прода[её]тся|прода[её]м|продам|продаю|продаж\w*|продается|"
    r"sotiladi|sotaman|sotamiz|sotuv\w*|sotilmoqda|sotib\s+ol\w*|"
    r"сотилади|сотаман|сотамиз|сотув\w*|сотилмоқда)" + _NLA
)


def _detect_type(work: str) -> Tuple[Optional[str], bool]:
    """Return ('rent' | 'sale' | None, conflict)."""
    rent_hits = [(m.start(), 2) for m in _RENT_STRONG_RE.finditer(work)]
    rent_hits += [(m.start(), 1) for m in _RENT_WEAK_RE.finditer(work)]
    sale_hits = [(m.start(), 2) for m in _SALE_STRONG_RE.finditer(work)]
    rent_score = sum(w for _, w in rent_hits)
    sale_score = sum(w for _, w in sale_hits)
    if not rent_score and not sale_score:
        return None, False
    conflict = bool(rent_score and sale_score) and any(w == 2 for _, w in rent_hits)
    if rent_score > sale_score:
        return "rent", conflict
    if sale_score > rent_score:
        return "sale", conflict
    first_rent = min(p for p, _ in rent_hits)
    first_sale = min(p for p, _ in sale_hits)
    return ("rent" if first_rent < first_sale else "sale"), True


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

_ROOM_WORDS: List[Tuple[re.Pattern, int]] = [
    (re.compile(_NL + r"(?:одно[-\s]?комн\w*|однушк\w*|1[-\s]?комн\w*|bir\s*xonali|бир\s*хонали|студи[яи]\w*|studiya|studio)" + _NLA), 1),
    (re.compile(_NL + r"(?:двух[-\s]?комн\w*|двушк\w*|ikki\s*xonali|икки\s*хонали)" + _NLA), 2),
    (re.compile(_NL + r"(?:тр[её]х[-\s]?комн\w*|тр[её]шк\w*|uch\s*xonali|уч\s*хонали)" + _NLA), 3),
    (re.compile(_NL + rf"(?:четыр[её]х[-\s]?комн\w*|to[{_AP}]?rt\s*xonali|тўрт\s*хонали)" + _NLA), 4),
    (re.compile(_NL + r"(?:пяти[-\s]?комн\w*|besh\s*xonali|беш\s*хонали)" + _NLA), 5),
]
_ROOMS_KW_RE = re.compile(
    r"(?:комнат\w*|xona\w*|хона\w*|rooms?)\s*(?:soni|сони)?\s*[:\-–]?\s*(\d{1,2})(?![\d/])"
)
_ROOMS_NUM_RE = re.compile(
    _ND + r"(\d{1,2})\s*[-–]?\s*(?:х|x|ти|ta)?\s*[-–]?\s*"
    r"(?:комн\w*|ком\.|кк" + _NLA + r"|хонали\w*|хона" + _NLA + r"|xonali\w*|xonalik|xona" + _NLA +
    r"|rooms?" + _NLA + r"|bedroom\w*)"
)
_ROOMS_K_RE = re.compile(_ND + r"(\d{1,2})\s?[-–]?(?:к|k)(?![" + _L + r"$\d])(?!\s*(?:\$|usd|сум|so))")
_RFT_RE = re.compile(_ND + r"([1-9]|10)\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})(?![\d/])(?![.,]\d)")


def _detect_rooms(work: str, spans: list) -> Optional[int]:
    for rx, value in _ROOM_WORDS:
        m = rx.search(work)
        if m:
            spans.append((m.start(), m.end()))
            return value
    for rx in (_ROOMS_NUM_RE, _ROOMS_KW_RE, _ROOMS_K_RE):
        for m in rx.finditer(work):
            value = int(m.group(1))
            if _in(value, *ROOMS_RANGE):
                spans.append((m.start(), m.end()))
                return value
    return None


# ---------------------------------------------------------------------------
# Area (m²)
# ---------------------------------------------------------------------------

_AREA_NUM = r"(\d{1,4}(?:[.,]\d{1,2})?)"
_AREA_UNIT = (
    r"(?:кв\.?\s*м(?:етр\w*|²|2)?\.?|м²|м2|m²|m2|m\^2|м\^2|кв\.?(?![а-яё])|"
    r"kv\.?\s*m(?:etr\w*|²|2)?\.?|kv\.?(?![a-zа-яё])|kvadrat\w*|квадрат\w*|"
    r"sq\.?\s*m\.?|sqm|square\s*met\w*)"
)
_AREA_KW_RE = re.compile(
    r"(?:общ(?:ая|\.)?\s*(?:площадь|пл\.?)?|площадь|площади|umumiy\s*maydon\w*|maydon\w*|майдон\w*|"
    r"\bs\s*[=:])\s*[:\-–=]?\s*" + _AREA_NUM + r"(?![\d/])"
)
_AREA_TRIPLE_RE = re.compile(_ND + r"(\d{2,3})\s*/\s*\d{1,3}\s*/\s*\d{1,3}\s*" + _AREA_UNIT)
_AREA_UNIT_RE = re.compile(_ND + _AREA_NUM + r"\s*" + _AREA_UNIT + _NLA)
_AREA_BARE_M_RE = re.compile(
    _ND + r"(\d{2,3}(?:[.,]\d)?)\s*(?:м|m)(?![" + _L + r"²2^/])"
    r"(?!\s*(?:до|от|к\b|da\b|dan\b|gacha|yurish|пешком|ходьбы))"
)


def _detect_area(work: str, spans: list) -> Optional[float]:
    for rx in (_AREA_KW_RE, _AREA_TRIPLE_RE, _AREA_UNIT_RE, _AREA_BARE_M_RE):
        for m in rx.finditer(work):
            value = _to_float(m.group(1))
            if _in(value, *AREA_RANGE):
                spans.append((m.start(), m.end()))
                return value
    return None


# ---------------------------------------------------------------------------
# Floor / total floors
# ---------------------------------------------------------------------------

_ORD = r"(?:й|ый|ий|чи|nchi|chi)?"
_FLOOR_W = r"(?:этаж(?![нк])\w*|эт\.?(?![а-яё])|qavat(?!li)\w*|қават(?!ли)\w*)"
_TOTAL_W = r"(?:этажн\w*|этажк\w*|qavatli|қаватли)"

_FLOOR_KW_PAIR_RE = re.compile(
    r"(?:этаж(?!ност)\w*|qavat\w*|қават\w*)\s*[:\-–]?\s*(\d{1,2})\s*(?:/|из|dan)\s*(\d{1,2})(?!\d)"
)
_FLOOR_PAIR_RE = re.compile(
    _ND + r"(\d{1,2})\s*[-–]?\s*" + _ORD + r"\s*[-–]?\s*" + _FLOOR_W +
    r"\s*(?:,?\s*(?:из|dan|/)\s*(\d{1,2})(?!\d)"
    r"|,?\s*(?:в\s*)?(\d{1,2})\s*[-–]?\s*(?:х|ти|ta)?\s*[-–]?\s*" + _TOTAL_W + r")"
)
_BARE_PAIR_RE = re.compile(r"(?<![\d/.,:])([1-9]\d?)\s*/\s*([1-9]\d?)(?![\d/%])(?![.,]\d)")
_TOTAL_KW_RE = re.compile(r"этажност\w*\s*[:\-–]?\s*(\d{1,2})(?!\d)")
_FLOOR_KW_RE = re.compile(r"(?:этаж(?!ност)\w*|qavat\w*|қават\w*)\s*[:\-–]?\s*(\d{1,2})(?![\d/])")
_FLOOR_ONLY_RE = re.compile(_ND + r"(\d{1,2})\s*[-–]?\s*" + _ORD + r"\s*[-–]?\s*" + _FLOOR_W)
_TOTAL_ONLY_RE = re.compile(_ND + r"(\d{1,2})\s*[-–]?\s*(?:х|ти|ta)?\s*[-–]?\s*" + _TOTAL_W)


def _detect_floors(work: str, spans: list) -> Tuple[Optional[int], Optional[int]]:
    floor = total = None
    for rx in (_FLOOR_KW_PAIR_RE, _FLOOR_PAIR_RE, _BARE_PAIR_RE):
        for m in rx.finditer(work):
            f = int(m.group(1))
            t_raw = next((g for g in m.groups()[1:] if g), None)
            t = int(t_raw) if t_raw else None
            if _in(f, *FLOOR_RANGE) and _in(t, f, FLOOR_RANGE[1]):
                spans.append((m.start(), m.end()))
                return f, t
    for rx in (_FLOOR_KW_RE, _FLOOR_ONLY_RE):
        for m in rx.finditer(work):
            f = int(m.group(1))
            if _in(f, *FLOOR_RANGE):
                spans.append((m.start(), m.end()))
                floor = f
                break
        if floor is not None:
            break
    for rx in (_TOTAL_KW_RE, _TOTAL_ONLY_RE):
        for m in rx.finditer(work):
            t = int(m.group(1))
            if _in(t, *FLOOR_RANGE):
                spans.append((m.start(), m.end()))
                total = t
                break
        if total is not None:
            break
    return floor, total


# ---------------------------------------------------------------------------
# Chirchiq areas
# ---------------------------------------------------------------------------

_MKR_BY_NUMBER: Dict[int, str] = {}
for _name in CHIRCHIQ_AREAS:
    _m = re.match(r"(\d+)-mikrorayon", _name)
    if _m:
        _MKR_BY_NUMBER[int(_m.group(1))] = _name

_MKR_WORD = (
    r"(?:мкр\w*|микрорайон\w*|микр\.?|м/р|м-р|mkr\w*|mikrorayon\w*|mikr\.?|"
    r"kichik\s*nohiya\w*|кичик\s*но[ҳх]ия\w*|kichik\s*tuman\w*)"
)
_MKR_RE = re.compile(_ND + r"(\d{1,2})\s*[-–]?\s*(?:й|ой|ий|чи|nchi|chi)?\s*[-–]?\s*" + _MKR_WORD)
_MKR_REV_RE = re.compile(
    r"(?:мкр\w*|микрорайон\w*|mkr\w*|mikrorayon\w*)\.?\s*[-–№#]?\s*(\d{1,2})(?![\w$/.,])"
)

_NAMED_AREAS: List[Tuple[re.Pattern, str]] = [
    (re.compile(_NL + r"(?:ак[-\s]?кавак\w*|аккавак\w*|akkavak\w*|oqqovoq\w*|oqovoq\w*|aqqovoq\w*|оққовоқ\w*|окковок\w*|оккавак\w*)"), "Oqqovoq"),
    (re.compile(_NL + r"(?:троицк\w*|troitsk\w*)"), "Troitsk"),
    (re.compile(_NL + r"(?:аранч[аеиу]\w*|arancha\w*|aranch\w*)"), "Arancha"),
    (re.compile(_NL + rf"(?:500\s*[-–]?\s*(?:ка|ka)(?![{_L}])|пятьсотк\w*|пятисотк\w*|горпарк\w*|gorpark\w*|besh\s*yuz)"), "500-ka (Gorpark)"),
    (re.compile(_NL + r"(?:рощ[аеиу]|roshcha|roscha|рошча)" + _NLA), "Roshcha"),
    (re.compile(_NL + rf"(?:янги\s*[уў]збекистон\w*|yangi\s*o[{_AP}]?zbekiston\w*|yangi\s*uzbekiston\w*|новый\s*узбекистан\w*|yangi\s*o[{_AP}]?zb(?![{_L}]))"), "Yangi O'zbekiston massivi"),
    (re.compile(_NL + r"(?:конструктор\w*|konstruktor\w*)"), "Konstruktorlar mavzesi"),
    (re.compile(_NL + r"(?:химпос[её]л\w*|ximpos\w*|himpos\w*|химгород\w*|химпосёлок)"), "Ximposyolok"),
    (re.compile(_NL + r"(?:джалаир\w*|жалаир\w*|jaloyir\w*|jalayir\w*|жалойир\w*|jaloir\w*)"), "Jaloyir"),
    (re.compile(_NL + r"(?:нижний\s*комсомольск\w*|nijniy\s*komsomolsk\w*|комсомольск(?:е|а|ом|у)?(?![а-яё])|komsomolsk\w*|komsomol(?![a-z]))"), "Nijniy Komsomolsk"),
    (re.compile(_NL + r"(?:центр(?:е|а|у|ом)?(?![а-яё])|markaz\w*|марказ\w*|наво(?:и|ий|ийский)\w*|navoi\w*|навоий\w*)"), "Markaz (Navoiy)"),
    (re.compile(_NL + r"(?:октябр\w*|oktyabr\w*)"), "1-mikrorayon (Oktyabr)"),
]
_CENTER_FALSE_RE = re.compile(r"(?:торгов\w*|тц|бизнес|медицинск\w*|учебн\w*|savdo|biznes|тиббий)\s*$")
_DATE_BEFORE_RE = re.compile(r"(?<![\d/.,])\d{1,2}\s*[-–]?\s*$")   # "25 октября" is a date

_LABEL_ALIASES: List[Tuple[str, str]] = sorted(
    ((label.casefold(), canonical) for canonical, labels in AREA_LABELS.items() for label in labels.values()),
    key=lambda item: -len(item[0]),
)


def _detect_area_name(work: str, spans: list, notes: list) -> Optional[str]:
    hits: List[Tuple[int, int, Optional[str], Optional[int]]] = []  # start, end, canonical, mkr number

    for m in _MKR_RE.finditer(work):
        number = int(m.group(1))
        hits.append((m.start(), m.end(), _MKR_BY_NUMBER.get(number), number))
    for m in _MKR_REV_RE.finditer(work):
        number = int(m.group(1))
        canonical = _MKR_BY_NUMBER.get(number)
        # "мкр 45k$": an unknown number after the word is not masked (it may be something else)
        hits.append((m.start(), m.end() if canonical else m.start() + 1, canonical, number))

    for rx, canonical in _NAMED_AREAS:
        for m in rx.finditer(work):
            before = work[max(0, m.start() - 20):m.start()]
            if canonical == "Markaz (Navoiy)" and m.group(0).startswith("центр") and _CENTER_FALSE_RE.search(before):
                continue
            if canonical == "1-mikrorayon (Oktyabr)" and m.group(0).endswith("я") and _DATE_BEFORE_RE.search(before):
                continue
            hits.append((m.start(), m.end(), canonical, None))

    for label, canonical in _LABEL_ALIASES:
        pos = work.find(label)
        if pos >= 0:
            hits.append((pos, pos + len(label), canonical, None))

    if not hits:
        return None
    hits.sort(key=lambda h: h[0])
    for start, end, canonical, number in hits:
        spans.append((start, end))
    for start, end, canonical, number in hits:
        if canonical:
            return canonical
    # Only unknown microdistrict numbers were found
    number = hits[0][3]
    if number is not None:
        notes.append(f"{number}-mikrorayon ro'yxatda yo'q — hudud qo'lda tanlanadi")
    return None


# ---------------------------------------------------------------------------
# Street
# ---------------------------------------------------------------------------

_WORD = rf"[{_L}{_AP}\-]{{2,}}"
_HOUSE = r"(\d{1,3}[а-яa-z]?(?:/\d{1,3})?)(?!\d)"
_STREET_RU_RE = re.compile(
    rf"(?<![{_L}])(ул\.|ул(?=\s)|улиц[аеыу]|у\.|пр-т|пр-кт|проспект|просп\.|пр\.|бульвар|б-р|переулок|пер\.|тупик|массив|мавзе|квартал|кв-л)"
    rf"\s*({_WORD}(?:\s+(?!дом\b|д\.|uy\b|кв\b|№)(?!\d){_WORD})?)"
    rf"(?:\s*,?\s*(?:д\.|дом|№|uy)?\s*{_HOUSE})?",
    re.I,
)
_STREET_UZ_RE = re.compile(
    rf"(?<![{_L}{_AP}])({_WORD}(?:\s+{_WORD})?)"
    rf"\s+(ko[{_AP}]?chasi|ko[{_AP}]?cha|kochasi|кўчаси|кучаси|кўча|куча|mavzesi|massivi|dahasi|mahallasi|маҳалласи|махалласи|shoh\s*ko[{_AP}]?chasi)(?![{_L}])"
    rf"(?:\s*,?\s*{_HOUSE}\s*(?:[-–]?\s*(?:uy|уй|dom|дом)(?![{_L}]))?)?",
    re.I,
)
_HOUSE_RU_RE = re.compile(
    rf"(?<![{_L}])(?:дом|д\.)\s*№?\s*(\d{{1,3}}[а-я]?)(?![\d/])(?!\s*(?:год|г\.|yil|этаж|эт\b|мкр|кв|комн))",
    re.I,
)
_HOUSE_UZ_RE = re.compile(_ND + rf"(\d{{1,3}})\s*[-–]?\s*(?:uy|уй)(?![{_L}])", re.I)

_STREET_STOP_FIRST = {
    "manzil", "manzili", "adres", "адрес", "shahar", "shahri", "chirchiq", "чирчик", "чирчиқ", "город",
    "гор", "tuman", "bizning", "uy", "kvartira", "квартира", "ул", "улица", "mahalla", "район", "rayon",
    "находится", "joylashgan", "расположена", "расположен", "по",
}
_STREET_STOP_SECOND = {
    "продам", "продаю", "продаётся", "продается", "сдам", "сдаю", "сдаётся", "сдается", "цена", "этаж",
    "комн", "квартира", "дом", "срочно", "торг", "рядом", "есть", "тел", "sotiladi", "ijaraga", "narxi",
    "qavat", "xonali", "kvartira", "uy", "район", "mkr", "мкр",
}


def _tidy_fragment(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" ,.;:-–—")
    if len(text) > STREET_MAX:
        text = text[:STREET_MAX].rstrip()
    return text


def _split_name(name: str) -> List[str]:
    return name.split()


def _detect_street(cased: str, spans: list) -> Optional[str]:
    m = _STREET_RU_RE.search(cased)
    if m:
        prefix, name, house = m.group(1), m.group(2), m.group(3)
        words = _split_name(name)
        if len(words) == 2:
            first, second = words
            if second.lower() in _STREET_STOP_SECOND or (first[:1].isupper() and second[:1].islower()):
                words = [first]
        if words and words[0].lower() not in _STREET_STOP_SECOND:
            spans.append((m.start(), m.end()))
            fragment = f"{prefix} {' '.join(words)}"
            if house:
                fragment += f" {house}"
            return _tidy_fragment(fragment)

    m = _STREET_UZ_RE.search(cased)
    if m:
        name, suffix, house = m.group(1), m.group(2), m.group(3)
        words = _split_name(name)
        if len(words) == 2:
            first, second = words
            if first.lower() in _STREET_STOP_FIRST or (first[:1].islower() and second[:1].isupper()):
                words = [second]
        if words and words[0].lower() not in _STREET_STOP_FIRST:
            spans.append((m.start(), m.end()))
            fragment = f"{' '.join(words)} {suffix}"
            if house:
                tail = cased[m.start(3):m.end()]
                fragment += f" {_tidy_fragment(tail)}"
            return _tidy_fragment(fragment)

    for rx in (_HOUSE_RU_RE, _HOUSE_UZ_RE):
        m = rx.search(cased)
        if m:
            spans.append((m.start(), m.end()))
            return _tidy_fragment(m.group(0))
    return None


# ---------------------------------------------------------------------------
# Price
# ---------------------------------------------------------------------------

_NUM = r"\d+(?:(?:[ ]|[.,](?=\d{3}(?!\d)))\d{3})*(?:[.,]\d{1,2})?"
_UNIT = r"(?:млрд|миллиард\w*|mlrd|milliard|млн|миллион\w*|mln|million|тыс\.?|тысяч\w*|ming|минг|(?<=\d)[kк])"
_CUR = (
    rf"(?:\$|usd|у\.?\s?е\.?|y\.?\s?e\.?|долл(?:ар\w*|\.)?|dollar\w*|сум(?:га|дан|ов|а|ы)?|сўм(?:га|дан)?|"
    rf"so[{_AP}]?m(?:ga|dan)?|som(?:ga|dan)?|sum|uzs)"
)
_RENT_HINT = r"(?:в\s*месяц|в\s*мес\.?|мес\.?(?![а-яё])|oyiga|oylik|ойига|ойлик|per\s*month|month)"

_PRICE_A_RE = re.compile(_ND + rf"({_NUM})\s*({_UNIT}\.?)?\s*({_CUR}){_NLA}")
_PRICE_B_RE = re.compile(rf"(?<![{_L}])(\$|usd|у\.е\.)\s*({_NUM})\s*({_UNIT})?(?![{_L}\d])")
_PRICE_C_RE = re.compile(
    rf"(?:цена|стоимость|narx\w*|нарх\w*|price|bahosi|баҳоси|summa|сумма)\s*[:\-–]?\s*(?:от|dan|from)?\s*"
    rf"({_NUM})\s*({_UNIT}\.?)?(?![\d])"
)
_PRICE_D_RE = re.compile(_ND + rf"({_NUM})\s*({_UNIT}\.?)(?![{_L}\d])")
_PRICE_E_RE = re.compile(_ND + rf"({_NUM})\s*({_UNIT}\.?)?\s*(?:{_CUR})?\s*/?\s*{_RENT_HINT}")
_PRICE_KW_BEFORE_RE = re.compile(r"(?:цена|стоимость|narx\w*|нарх\w*|price|bahosi|баҳоси)\s*[:\-–]?\s*(?:от|dan|from)?\s*$")
_NEGOTIABLE_RE = re.compile(
    _NL + r"(?:договорн\w*|по\s*договор[её]нности|kelishil\w*|kelishamiz|kelishib|келишил\w*|келишамиз|negotiable)"
)

_TYPE_UZ = {"rent": "ijara", "sale": "sotuv"}


def _price_candidates(work: str) -> List[Tuple[int, int, str, bool]]:
    """(score, start, raw_text, explicit_currency) sorted best first."""
    found: Dict[int, Tuple[int, int, str, bool]] = {}

    def add(m: re.Match, score: int, raw: str, explicit: bool) -> None:
        if _PRICE_KW_BEFORE_RE.search(work[max(0, m.start() - 20):m.start()]):
            score += 1
        start = m.start()
        if start not in found or found[start][0] < score:
            found[start] = (score, start, raw, explicit)

    for m in _PRICE_A_RE.finditer(work):
        add(m, 3, " ".join(g for g in m.groups() if g), True)
    for m in _PRICE_B_RE.finditer(work):
        add(m, 3, " ".join(g for g in m.groups() if g), True)
    for m in _PRICE_C_RE.finditer(work):
        add(m, 2, " ".join(g for g in m.groups() if g), False)
    for m in _PRICE_E_RE.finditer(work):
        explicit = re.search(_CUR, m.group(0)) is not None
        raw = m.group(0) if explicit else " ".join(g for g in m.groups() if g)
        add(m, 2, raw, explicit)
    for m in _PRICE_D_RE.finditer(work):
        add(m, 1, " ".join(g for g in m.groups() if g), False)

    return sorted(found.values(), key=lambda c: (-c[0], c[1]))


def _check_price(raw: str, apartment_type: str) -> Optional[Tuple[int, str, str]]:
    """(amount, currency, status) if the price fits ``apartment_type``, else None."""
    amount, currency, status = resolve_price(raw, apartment_type)
    if amount is None:
        return None
    if status in ("", "guessed_usd"):
        return amount, currency, status
    parsed = parse_price(raw)
    if parsed and parsed[1] is None:  # currency not written: try the other one
        value = parsed[0]
        for alt in ("USD", "UZS"):
            low, high = PRICE_LIMITS[(apartment_type, alt)]
            if low <= value <= high:
                return value, alt, "guessed_usd" if alt == "USD" else ""
    return None


def _detect_price(work: str, apartment_type: Optional[str], notes: list) -> Tuple[Optional[int], Optional[str]]:
    negotiable = _NEGOTIABLE_RE.search(work) is not None
    candidates = _price_candidates(work)
    if negotiable:
        candidates = [c for c in candidates if c[3]]  # only an explicit-currency price beats "kelishiladi"

    rejected: List[str] = []
    for score, start, raw, explicit in candidates:
        if apartment_type:
            result = _check_price(raw, apartment_type)
            if not result:
                rejected.append(raw)
                continue
            amount, currency, status = result
            if status == "guessed_usd":
                notes.append("Narx dollar deb olindi (valyuta yozilmagan)")
            if negotiable:
                notes.append("Matnda «kelishiladi» ham yozilgan — narx tekshirilsin")
            return amount, currency

        rent = _check_price(raw, "rent")
        sale = _check_price(raw, "sale")
        if not rent and not sale:
            rejected.append(raw)
            continue
        if rent and sale and (rent[0], rent[1]) != (sale[0], sale[1]):
            sale = None
        chosen = rent or sale
        amount, currency, status = chosen
        if status == "guessed_usd":
            notes.append("Narx dollar deb olindi (valyuta yozilmagan)")
        if not (rent and sale):
            fits = "rent" if rent else "sale"
            notes.append(f"Narx faqat {_TYPE_UZ[fits]} oralig'iga mos keladi — e'lon turi tekshirilsin")
        if negotiable:
            notes.append("Matnda «kelishiladi» ham yozilgan — narx tekshirilsin")
        return amount, currency

    if negotiable:
        notes.append("Narx «kelishiladi» deb yozilgan — narx so'raladi")
    elif rejected:
        shown = re.sub(r"\s+", " ", rejected[0]).strip()
        scope = _TYPE_UZ.get(apartment_type, "ijara/sotuv")
        notes.append(f"Narx topildi ({shown}), lekin {scope} oralig'iga mos kelmadi — narx so'raladi")
    return None, None


# ---------------------------------------------------------------------------
# Description
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _ZERO_WIDTH_RE.sub("", text)
    text = _SPACES_RE.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r" {2,}", " ", text)


def _build_description(cased: str, phones: List[Tuple[int, int, str]], max_description: int, notes: list) -> str:
    cuts: List[Tuple[int, int]] = []
    for start, end, _ in phones:
        label = _PHONE_LABEL_RE.search(cased[max(0, start - 40):start])
        if label:
            start -= len(label.group(0))
        cuts.append((start, end))
    pieces, pos = [], 0
    for start, end in sorted(cuts):
        if start < pos:
            start = pos
        pieces.append(cased[pos:start])
        pos = max(pos, end)
    pieces.append(cased[pos:])
    text = "".join(pieces)

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        line = re.sub(r"(?:\s*[,/|;]\s*){2,}", ", ", line)          # ", ," left by removed phones
        line = re.sub(r"^\s*[,/|;]+\s*", "", line)
        line = re.sub(r"\s*[,/|;]+\s*$", "", line)
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if max_description is None or max_description <= 0:
        return text
    if len(text) > max_description:
        text = text[:max(0, max_description - 1)].rstrip() + "…" if max_description > 1 else text[:max_description]
        notes.append(f"Tavsif {max_description} belgigacha qisqartirildi")
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_listing_text(text: str, max_description: int = 1000) -> ParsedListing:
    """Extract listing fields from free text. Never raises."""
    result = ParsedListing()
    try:
        return _parse(text, max_description, result)
    except Exception:  # pragma: no cover - last line of defence
        try:
            safe = _clean_text(str(text or ""))[:_MAX_INPUT]
            result.description = re.sub(r"[ \t]+", " ", safe).strip()[:max(0, max_description or 0)]
        except Exception:
            result.description = ""
        result.notes.append("Matnni to'liq tahlil qilib bo'lmadi — maydonlar qo'lda so'raladi")
        return result


def _parse(text, max_description: int, result: ParsedListing) -> ParsedListing:
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    try:
        max_description = int(max_description)
    except (TypeError, ValueError):
        max_description = 1000

    cased = _clean_text(text[:_MAX_INPUT])
    if not cased.strip():
        return result

    phones = _find_phones(cased)
    work = _lower_keep_len(cased)
    work = _mask(work, [(s, e) for s, e, _ in phones])
    cased_masked = _mask(cased, [(s, e) for s, e, _ in phones])

    notes: List[str] = []
    spans: List[Tuple[int, int]] = []

    # Type
    apartment_type, conflict = _detect_type(work)
    if conflict:
        notes.append("Matnda ham ijara, ham sotuv so'zlari bor — e'lon turi tekshirilsin")

    # Rooms (word / keyword forms first, then the "2/3/9" triple)
    rooms = _detect_rooms(work, spans)
    floor = total = None
    rft = _RFT_RE.search(work)
    if rft:
        r, f, t = int(rft.group(1)), int(rft.group(2)), int(rft.group(3))
        if (rooms is None or rooms == r) and _in(f, *FLOOR_RANGE) and _in(t, f, FLOOR_RANGE[1]):
            rooms = r
            floor, total = f, t
            spans.append((rft.start(), rft.end()))

    # Area
    area = _detect_area(work, spans)

    # Floors
    if floor is None:
        floor, total = _detect_floors(work, spans)
    if floor is not None and total is not None and total < floor:
        notes.append(f"Qavatlar soni ({total}) qavatdan ({floor}) kichik — qavatlar soni tashlab yuborildi")
        total = None

    # Chirchiq area + street
    area_name = _detect_area_name(work, spans, notes)
    street = _detect_street(cased_masked, spans)
    if street and not re.search(r"\d", street) and area_name:
        # "массив Янги Узбекистан" is the area itself, not a street
        probe = _lower_keep_len(street)
        if any(rx.search(probe) for rx, canonical in _NAMED_AREAS if canonical == area_name) or \
                any(label in probe for label, canonical in _LABEL_ALIASES if canonical == area_name):
            street = None

    # Price (structured numbers are masked so they cannot be read as money)
    price_work = _mask(work, spans)
    price, currency = _detect_price(price_work, apartment_type, notes)

    # Phone
    phone = phones[0][2] if phones else None
    if len(phones) > 1:
        others = ", ".join(sorted({p for _, _, p in phones[1:]}))
        notes.append(f"Bir nechta telefon topildi, birinchisi olindi (qolganlari: {others})")

    result.type = apartment_type
    result.rooms = rooms
    result.area = area
    result.floor = floor
    result.total_floors = total
    result.price = price
    result.currency = currency if price is not None else None
    result.phone = phone
    result.area_name = area_name
    result.street = street
    result.description = _build_description(cased, phones, max_description, notes)

    for name in ("type", "rooms", "area", "floor", "total_floors", "price", "phone", "area_name", "street"):
        if getattr(result, name) is not None:
            result.found.append(name)
    result.notes = notes
    return result


def address_from(parsed: ParsedListing) -> Optional[str]:
    """"Chirchiq, <area uz label>[, <street>]" / "Chirchiq, <street>" / None."""
    try:
        parts = [CITY]
        area_name = getattr(parsed, "area_name", None)
        street = getattr(parsed, "street", None)
        if area_name:
            parts.append(area_label(area_name, "uz"))
        if street:
            street = _tidy_fragment(str(street))
            if street:
                parts.append(street)
        if len(parts) == 1:
            return None
        return ", ".join(parts)
    except Exception:
        return None
