"""Numbers and rupee amounts in words (English and Tamil, Indian scale)."""

from __future__ import annotations

from typing import Literal

from ._errors import ValidationError
from ._numbers import Number, quantize, to_decimal
from ._words_en import english_words
from ._words_ta import TamilStyle, tamil_words

__all__ = ["Case", "Language", "TamilStyle", "amount_in_words", "number_to_words"]

Language = Literal["en", "ta"]
Case = Literal["title", "upper", "lower"]


def _non_negative_int(value: Number) -> int:
    number = to_decimal(value)
    if number != number.to_integral_value():
        raise ValidationError("number", f"{value!r} is not a whole number")
    if number < 0:
        raise ValidationError("number", "negative numbers are not supported")
    return int(number)


def _apply_case(text: str, case: Case) -> str:
    if case == "title":
        return text
    if case == "upper":
        return text.upper()
    if case == "lower":
        return text.lower()
    raise ValueError(f"unknown case {case!r}")


def number_to_words(
    number: Number,
    lang: Language = "en",
    *,
    style: TamilStyle = "sandhi",
    hyphenate: bool = True,
    use_and: bool = False,
) -> str:
    """Spell a whole number using the Indian scale.

    *style* applies to Tamil only; *hyphenate* and *use_and* to English only.

    >>> number_to_words(1234567)
    'Twelve Lakh Thirty-Four Thousand Five Hundred Sixty-Seven'
    >>> number_to_words(100000, lang="ta")
    'ஒரு லட்சம்'
    """
    n = _non_negative_int(number)
    if lang == "en":
        return english_words(n, hyphenate=hyphenate, use_and=use_and)
    if lang == "ta":
        return tamil_words(n, style=style)
    raise ValueError(f"unsupported language {lang!r}; use 'en' or 'ta'")


def amount_in_words(
    amount: Number,
    lang: Language = "en",
    *,
    only: bool = True,
    style: TamilStyle = "sandhi",
    hyphenate: bool = True,
    use_and: bool = False,
    case: Case = "title",
) -> str:
    """Write a rupee amount in words, as on a cheque or tax invoice.

    The amount is rounded half-up to whole paise first. Negative amounts are
    rejected: state the sign (credit note, refund) separately.

    English follows the common Indian banking layout
    ``Rupees <rupees> and <paise> Paise Only``; Tamil uses
    ``<rupees> ரூபாய் <paise> பைசா மட்டும்`` with adjective forms before the
    nouns (ஒரு ரூபாய், இருபத்தொரு ரூபாய்). *case* applies to English only.

    >>> amount_in_words(1234567.50)
    'Rupees Twelve Lakh Thirty-Four Thousand Five Hundred Sixty-Seven and Fifty Paise Only'
    >>> amount_in_words(100000, lang="ta")
    'ஒரு லட்சம் ரூபாய் மட்டும்'
    """
    value = quantize(to_decimal(amount), 2)
    if value < 0:
        raise ValidationError("amount", "negative amounts are not supported")
    # value has exactly two decimal places; integer arithmetic keeps huge amounts exact.
    rupees, paise = divmod(int(format(value, "f").replace(".", "")), 100)

    if lang == "en":
        r_words = english_words(rupees, hyphenate=hyphenate, use_and=use_and)
        p_words = english_words(paise, hyphenate=hyphenate, use_and=use_and)
        p_unit = "Paisa" if paise == 1 else "Paise"
        if rupees and paise:
            text = f"Rupees {r_words} and {p_words} {p_unit}"
        elif paise:
            text = f"{p_words} {p_unit}"
        else:
            text = f"Rupees {r_words}"
        if only:
            text += " Only"
        return _apply_case(text, case)

    if lang == "ta":
        r_words = tamil_words(rupees, form="adjective", style=style)
        p_words = tamil_words(paise, form="adjective", style=style)
        if rupees and paise:
            text = f"{r_words} ரூபாய் {p_words} பைசா"
        elif paise:
            text = f"{p_words} பைசா"
        else:
            text = f"{r_words} ரூபாய்"
        return text + " மட்டும்" if only else text

    raise ValueError(f"unsupported language {lang!r}; use 'en' or 'ta'")
