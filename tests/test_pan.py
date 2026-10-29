from __future__ import annotations

import pytest

from india_utils import ValidationError, is_valid_pan, pan_holder_type, parse_pan
from india_utils.pan import PAN_HOLDER_TYPES


def test_parse() -> None:
    pan = parse_pan(" abcpe1234f ")
    assert pan.value == "ABCPE1234F"
    assert str(pan) == "ABCPE1234F"
    assert pan.holder_type_code == "P"
    assert pan.holder_type == "Individual"
    assert pan.name_initial == "E"
    assert pan.sequence == "1234"
    assert pan.check_char == "F"


@pytest.mark.parametrize(("code", "label"), sorted(PAN_HOLDER_TYPES.items()))
def test_holder_types(code: str, label: str) -> None:
    assert pan_holder_type(f"ABC{code}E1234F") == label


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("ABCPE1234", "expected 10 characters"),
        ("ABCPE12345F", "expected 10 characters"),
        ("ABCP11234F", "5 letters, 4 digits"),
        ("1BCPE1234F", "5 letters, 4 digits"),
        ("ABCPE12341", "5 letters, 4 digits"),
        ("ABCXE1234F", "unknown holder type 'X'"),
        ("ABCKE1234F", "unknown holder type 'K'"),
    ],
)
def test_invalid(value: str, reason: str) -> None:
    assert not is_valid_pan(value)
    with pytest.raises(ValidationError, match=reason):
        parse_pan(value)


def test_valid() -> None:
    assert is_valid_pan("AAACB1234C")
    assert len(PAN_HOLDER_TYPES) == 10
