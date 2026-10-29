"""Indian Financial System Code (IFSC) validation.

RBI defines the IFSC as 11 characters: a 4-letter bank code, a fifth
character that is always ``0`` (reserved for future use) and a 6-character
alphanumeric branch code. This module checks the format only; whether a
branch exists can only be answered by RBI's published IFSC list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._errors import ValidationError

__all__ = ["IFSC", "KNOWN_BANK_CODES", "is_valid_ifsc", "parse_ifsc"]

_IFSC_RE = re.compile(r"[A-Z]{4}0[A-Z0-9]{6}")

#: A small, deliberately non-exhaustive map of widely used bank codes, for
#: display only. Unknown bank codes are still valid IFSC prefixes.
KNOWN_BANK_CODES: dict[str, str] = {
    "BARB": "Bank of Baroda",
    "BKID": "Bank of India",
    "CBIN": "Central Bank of India",
    "CIUB": "City Union Bank",
    "CNRB": "Canara Bank",
    "FDRL": "Federal Bank",
    "HDFC": "HDFC Bank",
    "ICIC": "ICICI Bank",
    "IDIB": "Indian Bank",
    "IOBA": "Indian Overseas Bank",
    "KKBK": "Kotak Mahindra Bank",
    "KVBL": "Karur Vysya Bank",
    "MAHB": "Bank of Maharashtra",
    "PSIB": "Punjab and Sind Bank",
    "PUNB": "Punjab National Bank",
    "RBIS": "Reserve Bank of India",
    "SBIN": "State Bank of India",
    "SIBL": "South Indian Bank",
    "TMBL": "Tamilnad Mercantile Bank",
    "UBIN": "Union Bank of India",
    "UCBA": "UCO Bank",
    "UTIB": "Axis Bank",
    "YESB": "Yes Bank",
}


@dataclass(frozen=True)
class IFSC:
    """A parsed IFSC. ``bank_name`` is ``None`` for codes not in :data:`KNOWN_BANK_CODES`."""

    value: str
    bank_code: str
    branch_code: str
    bank_name: str | None

    def __str__(self) -> str:
        return self.value


def parse_ifsc(value: str) -> IFSC:
    """Validate and split an IFSC. Raises :class:`ValidationError` when invalid.

    >>> parse_ifsc("sbin0000001").bank_name
    'State Bank of India'
    """
    code = "".join(value.split()).upper()
    if len(code) != 11:
        raise ValidationError("ifsc", f"expected 11 characters, got {len(code)}")
    if code[4] != "0":
        raise ValidationError("ifsc", "5th character must be '0'")
    if not _IFSC_RE.fullmatch(code):
        raise ValidationError(
            "ifsc", "expected 4 letters, '0', then 6 letters/digits (AAAA0XXXXXX)"
        )
    bank = code[:4]
    return IFSC(
        value=code, bank_code=bank, branch_code=code[5:], bank_name=KNOWN_BANK_CODES.get(bank)
    )


def is_valid_ifsc(value: str) -> bool:
    """Return ``True`` if *value* is a well-formed IFSC."""
    try:
        parse_ifsc(value)
    except ValidationError:
        return False
    return True
