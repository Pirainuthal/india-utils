from __future__ import annotations

import pytest

from india_utils import ValidationError, is_valid_ifsc, parse_ifsc


def test_parse_known_bank() -> None:
    ifsc = parse_ifsc(" sbin0000001 ")
    assert ifsc.value == "SBIN0000001"
    assert str(ifsc) == "SBIN0000001"
    assert ifsc.bank_code == "SBIN"
    assert ifsc.branch_code == "000001"
    assert ifsc.bank_name == "State Bank of India"


def test_parse_unknown_bank_is_still_valid() -> None:
    ifsc = parse_ifsc("ZZZZ0AB12CD")
    assert ifsc.bank_name is None
    assert ifsc.branch_code == "AB12CD"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("SBIN000001", "expected 11 characters"),
        ("SBIN1000001", "5th character must be '0'"),
        ("SB1N0000001", "expected 4 letters"),
        ("SBIN00000-1", "expected 4 letters"),
    ],
)
def test_invalid(value: str, reason: str) -> None:
    assert not is_valid_ifsc(value)
    with pytest.raises(ValidationError, match=reason):
        parse_ifsc(value)


def test_valid() -> None:
    assert is_valid_ifsc("HDFC0001234")
