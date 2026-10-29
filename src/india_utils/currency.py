"""Indian-style number and rupee formatting (lakh / crore digit grouping).

India groups the integer part as ``XX,XX,XXX``: the last three digits form a
group and every group to the left of it has two digits. One lakh is
1,00,000 (10^5) and one crore is 1,00,00,000 (10^7).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from ._numbers import Number, group_indian, quantize, to_decimal

__all__ = ["NegativeStyle", "format_indian_number", "format_inr", "format_inr_compact"]

NegativeStyle = Literal["minus", "parentheses"]

_CRORE_EXP = 7
_LAKH_EXP = 5
_THOUSAND_EXP = 3


def _plain(value: Decimal) -> str:
    """Render a non-negative Decimal with Indian grouping and no exponent."""
    text = format(value, "f")
    integer, dot, fraction = text.partition(".")
    return group_indian(integer) + (dot + fraction if dot else "")


def _apply_sign(body: str, negative: bool, style: NegativeStyle) -> str:
    if not negative:
        return body
    if style == "parentheses":
        return f"({body})"
    if style == "minus":
        return f"-{body}"
    raise ValueError(f"unknown negative_style {style!r}")


def format_indian_number(amount: Number, decimals: int = 0) -> str:
    """Group a number the Indian way, without a currency symbol.

    >>> format_indian_number(1234567)
    '12,34,567'
    >>> format_indian_number("-98765.432", decimals=2)
    '-98,765.43'
    """
    return format_inr(amount, symbol="", decimals=decimals)


def format_inr(
    amount: Number,
    *,
    symbol: str = "₹",
    decimals: int = 2,
    negative_style: NegativeStyle = "minus",
) -> str:
    """Format *amount* as Indian rupees with lakh/crore grouping.

    Rounding is half away from zero (``0.005`` -> ``0.01``), which matches
    how invoices and bank statements round paise. Floats are converted via
    ``repr`` so ``2.675`` rounds to ``2.68`` (not ``2.67`` as binary floats would).

    >>> format_inr(1234567.5)
    '₹12,34,567.50'
    >>> format_inr(-1500, symbol="Rs. ", decimals=0)
    '-Rs. 1,500'
    >>> format_inr(-1500, negative_style="parentheses")
    '(₹1,500.00)'
    """
    value = quantize(to_decimal(amount), decimals)
    negative = value < 0  # Decimal('-0.00') < 0 is False, so -0.001 prints as 0.00
    return _apply_sign(symbol + _plain(value.copy_abs()), negative, negative_style)


def _trim(value: Decimal) -> str:
    text = _plain(value)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def format_inr_compact(
    amount: Number,
    *,
    symbol: str = "",
    decimals: int = 2,
    thousands: bool = True,
) -> str:
    """Abbreviate an amount using K (thousand), L (lakh) and Cr (crore).

    Trailing zeros after the decimal point are dropped, and a value that rounds
    up to the next unit is promoted (99,99,999 -> ``"1 Cr"``, never ``"100 L"``).
    Crore values keep Indian grouping (``"1,500 Cr"``).

    >>> format_inr_compact(1234567)
    '12.35 L'
    >>> format_inr_compact(12000000, symbol="₹")
    '₹1.2 Cr'
    >>> format_inr_compact(45250, thousands=False)
    '45,250'
    """
    value = to_decimal(amount)
    negative = value < 0
    magnitude = value.copy_abs()  # abs() would round to the context precision

    exponents = [_CRORE_EXP, _LAKH_EXP] + ([_THOUSAND_EXP] if thousands else [])
    labels = {_CRORE_EXP: "Cr", _LAKH_EXP: "L", _THOUSAND_EXP: "K"}

    # Pick the largest unit that fits, then promote if rounding overflows it.
    chosen: int | None = next((e for e in exponents if magnitude >= Decimal(10) ** e), None)
    while True:
        scaled = quantize(magnitude.scaleb(-chosen) if chosen else magnitude, decimals)
        bigger = [e for e in exponents if e > (chosen or 0)]
        next_exp = min(bigger) if bigger else None
        if next_exp is None or scaled < Decimal(10) ** (next_exp - (chosen or 0)):
            break
        chosen = next_exp

    if scaled == 0:
        negative = False
    body = symbol + _trim(scaled) + (f" {labels[chosen]}" if chosen else "")
    return _apply_sign(body, negative, "minus")
