"""PIN codes and Indian mobile numbers."""

from __future__ import annotations

import re

from ._errors import ValidationError

__all__ = [
    "PIN_REGIONS",
    "is_valid_mobile",
    "is_valid_pincode",
    "normalize_mobile",
    "normalize_pincode",
    "pincode_region",
]

#: India Post's first-digit postal regions.
PIN_REGIONS: dict[str, str] = {
    "1": "Delhi, Haryana, Punjab, Himachal Pradesh, Jammu and Kashmir, Ladakh, Chandigarh",
    "2": "Uttar Pradesh, Uttarakhand",
    "3": "Rajasthan, Gujarat, Dadra and Nagar Haveli and Daman and Diu",
    "4": "Maharashtra, Goa, Madhya Pradesh, Chhattisgarh",
    "5": "Andhra Pradesh, Telangana, Karnataka",
    "6": "Tamil Nadu, Kerala, Puducherry, Lakshadweep",
    "7": "West Bengal, Odisha, North-Eastern states, Andaman and Nicobar Islands",
    "8": "Bihar, Jharkhand",
    "9": "Army Postal Service",
}

_PIN_RE = re.compile(r"[1-9][0-9]{5}")
_MOBILE_RE = re.compile(r"[6-9][0-9]{9}")
_SEPARATORS = re.compile(r"[\s\-().]")


def normalize_pincode(value: str) -> str:
    """Return the six-digit PIN code, accepting ``"600 001"`` style spacing."""
    pin = "".join(value.split())
    if not _PIN_RE.fullmatch(pin):
        raise ValidationError("pincode", "expected 6 digits not starting with 0")
    return pin


def is_valid_pincode(value: str) -> bool:
    """Return ``True`` for a well-formed six-digit PIN code (format check only)."""
    try:
        normalize_pincode(value)
    except ValidationError:
        return False
    return True


def pincode_region(value: str) -> str:
    """Return the India Post region for a PIN code from its first digit.

    >>> pincode_region("600001")
    'Tamil Nadu, Kerala, Puducherry, Lakshadweep'
    """
    return PIN_REGIONS[normalize_pincode(value)[0]]


def normalize_mobile(value: str) -> str:
    """Normalise an Indian mobile number to E.164 (``+91XXXXXXXXXX``).

    Accepts the usual ways people type numbers: ``98765 43210``,
    ``098765-43210``, ``+91 98765 43210``, ``919876543210`` and
    ``0091 98765 43210``. The ten-digit subscriber number must start with
    6, 7, 8 or 9 (the mobile series in the National Numbering Plan).

    >>> normalize_mobile("098765 43210")
    '+919876543210'
    """
    raw = _SEPARATORS.sub("", value)
    if raw.startswith("+"):
        if not raw.startswith("+91"):
            raise ValidationError("mobile", "only +91 (India) numbers are supported")
        digits = raw[3:]
    elif raw and not raw.isdigit():
        raise ValidationError("mobile", "contains characters other than digits")
    elif len(raw) == 14 and raw.startswith("0091"):
        digits = raw[4:]
    elif len(raw) == 12 and raw.startswith("91"):
        digits = raw[2:]
    elif len(raw) == 11 and raw.startswith("0"):
        digits = raw[1:]
    else:
        digits = raw
    if not _MOBILE_RE.fullmatch(digits):
        raise ValidationError("mobile", "expected a 10-digit number starting with 6-9")
    return "+91" + digits


def is_valid_mobile(value: str) -> bool:
    """Return ``True`` if *value* normalises to a valid Indian mobile number."""
    try:
        normalize_mobile(value)
    except ValidationError:
        return False
    return True
