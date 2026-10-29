"""Permanent Account Number (PAN) validation and parsing.

A PAN is ten characters: ``AAAAA9999A``. Characters 1-3 are an alphabetic
series, the 4th is the holder type, the 5th is the first letter of the
holder's surname (individuals) or name (everyone else), 6-9 are a sequence
number and the 10th is an alphabetic check character. The Income Tax
Department does not publish the check-character algorithm, so it is **not**
verified here: a PAN that passes this module is well-formed, not necessarily
issued.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._errors import ValidationError

__all__ = ["PAN", "PAN_HOLDER_TYPES", "is_valid_pan", "pan_holder_type", "parse_pan"]

PAN_HOLDER_TYPES: dict[str, str] = {
    "A": "Association of Persons (AOP)",
    "B": "Body of Individuals (BOI)",
    "C": "Company",
    "F": "Firm / Limited Liability Partnership",
    "G": "Government",
    "H": "Hindu Undivided Family (HUF)",
    "J": "Artificial Juridical Person",
    "L": "Local Authority",
    "P": "Individual",
    "T": "Trust",
}

_PAN_RE = re.compile(r"[A-Z]{5}[0-9]{4}[A-Z]")


@dataclass(frozen=True)
class PAN:
    """A parsed PAN. ``str(pan)`` returns the normalised ten-character value."""

    value: str
    holder_type_code: str
    holder_type: str
    name_initial: str
    sequence: str
    check_char: str

    def __str__(self) -> str:
        return self.value


def _normalise(value: str) -> str:
    return "".join(value.split()).upper()


def parse_pan(value: str) -> PAN:
    """Validate and split a PAN. Raises :class:`ValidationError` when invalid.

    >>> parse_pan("abcpe1234f").holder_type
    'Individual'
    """
    pan = _normalise(value)
    if len(pan) != 10:
        raise ValidationError("pan", f"expected 10 characters, got {len(pan)}")
    if not _PAN_RE.fullmatch(pan):
        raise ValidationError("pan", "expected 5 letters, 4 digits, 1 letter (AAAAA9999A)")
    code = pan[3]
    if code not in PAN_HOLDER_TYPES:
        raise ValidationError("pan", f"unknown holder type {code!r} in 4th position")
    return PAN(
        value=pan,
        holder_type_code=code,
        holder_type=PAN_HOLDER_TYPES[code],
        name_initial=pan[4],
        sequence=pan[5:9],
        check_char=pan[9],
    )


def is_valid_pan(value: str) -> bool:
    """Return ``True`` if *value* is a well-formed PAN."""
    try:
        parse_pan(value)
    except ValidationError:
        return False
    return True


def pan_holder_type(value: str) -> str:
    """Return the holder type described by the 4th character of a PAN."""
    return parse_pan(value).holder_type
