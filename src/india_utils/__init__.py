"""Indian number formats and identifier validation with zero dependencies.

>>> from india_utils import format_inr, amount_in_words, is_valid_gstin
>>> format_inr(1234567.5)
'₹12,34,567.50'
>>> is_valid_gstin("29AAACB1234C1ZB")
True
"""

from __future__ import annotations

from ._errors import ValidationError
from .contact import (
    is_valid_mobile,
    is_valid_pincode,
    normalize_mobile,
    normalize_pincode,
    pincode_region,
)
from .currency import format_indian_number, format_inr, format_inr_compact
from .gstin import GSTIN, gstin_check_digit, is_valid_gstin, parse_gstin
from .ifsc import IFSC, is_valid_ifsc, parse_ifsc
from .pan import PAN, is_valid_pan, pan_holder_type, parse_pan
from .states import STATE_CODES, state_name
from .words import amount_in_words, number_to_words

__version__ = "0.1.0"

__all__ = [
    "GSTIN",
    "IFSC",
    "PAN",
    "STATE_CODES",
    "ValidationError",
    "__version__",
    "amount_in_words",
    "format_indian_number",
    "format_inr",
    "format_inr_compact",
    "gstin_check_digit",
    "is_valid_gstin",
    "is_valid_ifsc",
    "is_valid_mobile",
    "is_valid_pan",
    "is_valid_pincode",
    "normalize_mobile",
    "normalize_pincode",
    "number_to_words",
    "pan_holder_type",
    "parse_gstin",
    "parse_ifsc",
    "parse_pan",
    "pincode_region",
    "state_name",
]
