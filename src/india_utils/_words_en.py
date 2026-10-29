"""English cardinal words using the Indian (lakh / crore) scale."""

from __future__ import annotations

__all__ = ["english_words"]

_ONES = (
    "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
)  # fmt: skip
_TENS = ("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety")

_CRORE = 10**7
_LAKH = 10**5
_THOUSAND = 10**3


def _below_100(n: int, hyphenate: bool) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    if not ones:
        return _TENS[tens]
    return _TENS[tens] + ("-" if hyphenate else " ") + _ONES[ones]


def english_words(n: int, *, hyphenate: bool = True, use_and: bool = False) -> str:
    """Spell a non-negative integer in Title Case with lakh and crore.

    Amounts of 100 crore and above repeat the scale words, the way Indian
    newspapers and banks write them: ``10**12`` is ``"One Lakh Crore"``.

    *use_and* inserts the British "and" before the final tens/units
    ("One Hundred and Five", "One Lakh and Five").
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return _ONES[0]

    parts: list[str] = []
    crore, rest = divmod(n, _CRORE)
    lakh, rest = divmod(rest, _LAKH)
    thousand, below = divmod(rest, _THOUSAND)

    if crore:
        parts.append(english_words(crore, hyphenate=hyphenate, use_and=use_and) + " Crore")
    if lakh:
        parts.append(_below_100(lakh, hyphenate) + " Lakh")
    if thousand:
        parts.append(_below_100(thousand, hyphenate) + " Thousand")

    hundreds, tail = divmod(below, 100)
    if hundreds:
        parts.append(_ONES[hundreds] + " Hundred")
    if tail:
        tail_words = _below_100(tail, hyphenate)
        parts.append(f"and {tail_words}" if use_and and parts else tail_words)
    return " ".join(parts)
