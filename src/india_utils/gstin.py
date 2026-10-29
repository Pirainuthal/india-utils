"""GST Identification Number (GSTIN) validation, parsing and check digits.

A regular taxpayer's GSTIN has 15 characters::

    33 ABCPE1234F 1 Z I
    |  |          | | +-- check character (Luhn mod 36)
    |  |          | +---- "Z" for regular taxpayers
    |  |          +------ entity number for this PAN in the state (1-9, then A-Z)
    |  +----------------- PAN of the taxpayer
    +-------------------- GST state code

The check character uses the Luhn mod-N algorithm over the alphabet
``0-9A-Z`` (N = 36): starting from the left, values are multiplied by 1, 2,
1, 2, ...; each product contributes ``product // 36 + product % 36``; the
check value is ``(36 - total % 36) % 36``.

Only the regular-taxpayer layout is accepted. Special registrations (UIN,
OIDAR, NRTP, TDS/TCS deductors) use different layouts and are rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._errors import ValidationError
from .pan import PAN_HOLDER_TYPES
from .states import state_name

__all__ = ["GSTIN", "gstin_check_digit", "is_valid_gstin", "parse_gstin"]

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_VALUES = {ch: i for i, ch in enumerate(_ALPHABET)}
_RADIX = len(_ALPHABET)
_STRUCTURE_RE = re.compile(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]")


@dataclass(frozen=True)
class GSTIN:
    """A parsed GSTIN. ``str(gstin)`` returns the normalised 15-character value."""

    value: str
    state_code: str
    state_name: str
    pan: str
    entity_number: str
    default_char: str
    check_digit: str

    @property
    def pan_holder_type(self) -> str:
        """Holder type of the embedded PAN, e.g. ``"Company"``."""
        return PAN_HOLDER_TYPES[self.pan[3]]

    def __str__(self) -> str:
        return self.value


def _normalise(value: str) -> str:
    return "".join(value.split()).upper()


def gstin_check_digit(first14: str) -> str:
    """Compute the 15th (check) character for the first 14 characters of a GSTIN.

    >>> gstin_check_digit("29AAACB1234C1Z")
    'B'
    """
    body = _normalise(first14)
    if len(body) != 14:
        raise ValidationError("gstin", f"check digit needs exactly 14 characters, got {len(body)}")
    total = 0
    for index, char in enumerate(body):
        try:
            value = _VALUES[char]
        except KeyError:
            raise ValidationError("gstin", f"character {char!r} is not 0-9 or A-Z") from None
        product = value * (2 if index % 2 else 1)
        total += product // _RADIX + product % _RADIX
    return _ALPHABET[(_RADIX - total % _RADIX) % _RADIX]


def parse_gstin(value: str, *, allow_legacy_state_codes: bool = False) -> GSTIN:
    """Validate and split a GSTIN. Raises :class:`ValidationError` when invalid.

    Spaces are ignored and letters are upper-cased. The error message says
    which rule failed (length, layout, state code, PAN holder type or checksum).

    >>> g = parse_gstin("29AAACB1234C1ZB")
    >>> g.state_name, g.pan, g.pan_holder_type
    ('Karnataka', 'AAACB1234C', 'Company')
    """
    gstin = _normalise(value)
    if len(gstin) != 15:
        raise ValidationError("gstin", f"expected 15 characters, got {len(gstin)}")
    if not _STRUCTURE_RE.fullmatch(gstin):
        raise ValidationError(
            "gstin",
            "expected 2 digits, a PAN (AAAAA9999A), an entity number (1-9/A-Z), "
            "'Z' and a check character",
        )
    name = state_name(gstin[:2], allow_legacy=allow_legacy_state_codes)
    if name is None:
        raise ValidationError("gstin", f"unknown state code {gstin[:2]!r}")
    if gstin[5] not in PAN_HOLDER_TYPES:
        raise ValidationError("gstin", f"embedded PAN has unknown holder type {gstin[5]!r}")
    expected = gstin_check_digit(gstin[:14])
    if gstin[14] != expected:
        raise ValidationError(
            "gstin", f"check digit mismatch: got {gstin[14]!r}, expected {expected!r}"
        )
    return GSTIN(
        value=gstin,
        state_code=gstin[:2],
        state_name=name,
        pan=gstin[2:12],
        entity_number=gstin[12],
        default_char=gstin[13],
        check_digit=gstin[14],
    )


def is_valid_gstin(value: str, *, allow_legacy_state_codes: bool = False) -> bool:
    """Return ``True`` if *value* is a structurally valid GSTIN with a correct checksum."""
    try:
        parse_gstin(value, allow_legacy_state_codes=allow_legacy_state_codes)
    except ValidationError:
        return False
    return True
