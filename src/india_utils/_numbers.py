"""Internal helpers for turning user input into exact :class:`~decimal.Decimal` values."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from typing import TypeAlias

from ._errors import ValidationError

#: Anything the public API accepts as an amount.
Number: TypeAlias = int | float | Decimal | str

#: Guard against inputs such as "1e999999" that would need megabytes of digits.
MAX_DIGITS = 40

__all__ = ["MAX_DIGITS", "Number", "group_indian", "quantize", "to_decimal"]


def to_decimal(value: Number) -> Decimal:
    """Convert *value* to a finite :class:`Decimal` without binary-float noise.

    Floats go through ``repr`` so ``0.1`` becomes ``Decimal("0.1")`` rather
    than ``Decimal("0.1000000000000000055511151231257827...")``. Strings may
    contain Indian or Western thousands separators, surrounding whitespace and
    a leading ``₹``.
    """
    if isinstance(value, bool):
        raise ValidationError("amount", "booleans are not numbers")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        result = Decimal(repr(value))
    elif isinstance(value, str):
        result = _parse_str(value)
    else:
        raise TypeError(f"expected int, float, Decimal or str, got {type(value).__name__}")
    if not result.is_finite():
        raise ValidationError("amount", f"{value!r} is not finite")
    if result and result.adjusted() >= MAX_DIGITS:
        raise ValidationError("amount", f"more than {MAX_DIGITS} integer digits")
    return result


def _parse_str(value: str) -> Decimal:
    """Parse ``"-₹ 12,34,567.50"`` style text (sign, symbol, separators)."""
    cleaned = value.strip().replace(",", "").replace("_", "")
    negative = cleaned.startswith("-")
    if negative:
        cleaned = cleaned[1:].lstrip()
    cleaned = cleaned.removeprefix("₹").strip()
    if not cleaned:
        raise ValidationError("amount", f"{value!r} is empty")
    if negative and cleaned[0] in "+-":
        # "--5" or "-₹-5" would otherwise negate twice and come out positive.
        raise ValidationError("amount", f"{value!r} has more than one sign")
    try:
        result = Decimal(cleaned)
    except InvalidOperation:
        raise ValidationError("amount", f"{value!r} is not a number") from None
    return result.copy_negate() if negative else result  # unary minus rounds to 28 digits


def quantize(value: Decimal, decimals: int) -> Decimal:
    """Round half away from zero (commercial rounding) to *decimals* places."""
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    # Widen the context so very large amounts never hit the default 28-digit limit.
    integer_digits = max(value.adjusted() + 1, 1)
    with localcontext() as ctx:
        ctx.prec = max(ctx.prec, integer_digits + decimals + 2)
        return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def group_indian(digits: str) -> str:
    """Insert Indian-style separators into a string of ASCII digits.

    The last three digits form one group and every group to the left has two
    digits: ``"1234567"`` becomes ``"12,34,567"``.
    """
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    groups.insert(0, head)
    return ",".join(groups) + "," + tail
