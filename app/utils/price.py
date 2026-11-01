"""Price input parsing: understands '3 mln', '2,5 mln', '2 mln 500 ming', '800 ming', '$45 000', '45000$', '1 500 000'."""
import re
from typing import Optional, Tuple

USD = "USD"
UZS = "UZS"

# Unit words (Latin / Cyrillic, common spellings). Longer words first.
_UNITS = [
    (r"mlrd|milliard|milyard|млрд|миллиард", 1_000_000_000),
    (r"mln|million|millon|milyon|mlyon|million|млн|миллион|mil", 1_000_000),
    (r"ming|минг|тыс|тысяч|k|к", 1_000),
]
_UNIT_RE = "|".join(p for p, _ in _UNITS)
_NOT_LETTER_BEFORE = r"(?<![a-zа-яёўқғҳʻ'])"
_NOT_LETTER_AFTER = r"(?![a-zа-яёўқғҳʻ'])"

_USD_RE = re.compile(
    r"\$|usd|dollar|доллар|долл|" + _NOT_LETTER_BEFORE + r"(?:y\.?e\.?|у\.?е\.?)" + _NOT_LETTER_AFTER
)
_UZS_RE = re.compile(r"so['ʻ‘’`]?m|сум|сўм|uzs|" + _NOT_LETTER_BEFORE + r"sum" + _NOT_LETTER_AFTER)

# Sensible ranges per (type, currency). Rent is per month.
PRICE_LIMITS = {
    ("rent", UZS): (100_000, 100_000_000),
    ("rent", USD): (100, 5_000),
    ("sale", UZS): (10_000_000, 100_000_000_000),
    ("sale", USD): (5_000, 1_000_000),
}

_MAX_DIGITS = 15  # anything longer is nonsense (and avoids float overflow)


def _to_number(raw: str, decimal_allowed: bool) -> Optional[float]:
    """'1 500 000' / '1.500.000' -> 1500000; '2,5' -> 2.5 (only if decimal_allowed)."""
    raw = re.sub(r"[\s'’]", "", raw).strip(".,")
    if not raw or len(re.sub(r"\D", "", raw)) > _MAX_DIGITS:
        return None
    # Dots/commas followed by groups of exactly 3 digits are thousand separators
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", raw):
        return float(re.sub(r"[.,]", "", raw))
    if re.fullmatch(r"\d+", raw):
        return float(raw)
    if decimal_allowed and re.fullmatch(r"\d+[.,]\d+", raw):
        return float(raw.replace(",", "."))
    return None


def parse_price(text: str) -> Optional[Tuple[int, Optional[str], bool]]:
    """
    Parse a free-form price.
    Returns (amount, currency, used_unit_word) or None if it is not a price.
    currency is 'USD', 'UZS' or None (not written).
    """
    if not text:
        return None
    t = text.strip().lower()

    # Explicit so'm wins over a stray dollar-ish match
    if _UZS_RE.search(t):
        currency = UZS
    elif _USD_RE.search(t):
        currency = USD
    else:
        currency = None

    # Sum every "number + unit" pair: '2 mln 500 ming' -> 2 500 000
    pairs = list(re.finditer(rf"(\d[\d\s.,'’]*?)\s*({_UNIT_RE}){_NOT_LETTER_AFTER}", t))
    if pairs:
        total = 0.0
        for m in pairs:
            number = _to_number(m.group(1), decimal_allowed=True)
            if number is None:
                return None
            unit = m.group(2)
            multiplier = next(v for p, v in _UNITS if re.fullmatch(p, unit))
            total += number * multiplier
        amount = int(round(total))
        used_unit = True
    else:
        m = re.search(r"\d[\d\s.,'’]*", t)
        if not m:
            return None
        # Plain number: decimals only make sense for dollars ('450.5$')
        number = _to_number(m.group(0), decimal_allowed=(currency == USD))
        if number is None:
            return None
        amount = int(round(number))
        used_unit = False

    if amount <= 0:
        return None
    return amount, currency, used_unit


def resolve_price(text: str, apartment_type: str) -> Tuple[Optional[int], Optional[str], str]:
    """
    Parse and validate a price for 'rent' or 'sale'.
    Returns (amount, currency, status):
      ''              OK, currency was written or obvious
      'guessed_usd'   OK, no currency written and the number only makes sense in dollars
      'not_a_number' / 'too_low' / 'too_high'  -> ask again
    """
    parsed = parse_price(text)
    if not parsed:
        return None, None, "not_a_number"
    amount, currency, used_unit = parsed

    def in_range(cur: str) -> bool:
        low, high = PRICE_LIMITS[(apartment_type, cur)]
        return low <= amount <= high

    status = ""
    if currency is None:
        if used_unit or in_range(UZS):
            currency = UZS          # 'mln' / 'ming' always means so'm
        elif in_range(USD):
            currency, status = USD, "guessed_usd"
        else:
            currency = UZS

    if in_range(currency):
        return amount, currency, status

    low, _ = PRICE_LIMITS[(apartment_type, currency)]
    return amount, currency, ("too_low" if amount < low else "too_high")
