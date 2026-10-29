from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from india_utils import (
    ValidationError,
    is_valid_mobile,
    is_valid_pincode,
    normalize_mobile,
    normalize_pincode,
    pincode_region,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("600001", "600001"), ("600 001", "600001"), (" 110001 ", "110001")],
)
def test_pincode(value: str, expected: str) -> None:
    assert normalize_pincode(value) == expected
    assert is_valid_pincode(value)


@pytest.mark.parametrize("value", ["060001", "60001", "6000011", "60000A", ""])
def test_pincode_invalid(value: str) -> None:
    assert not is_valid_pincode(value)
    with pytest.raises(ValidationError):
        normalize_pincode(value)


def test_pincode_region() -> None:
    assert pincode_region("600001").startswith("Tamil Nadu")
    assert pincode_region("110001").startswith("Delhi")
    assert pincode_region("560001").endswith("Karnataka")
    assert pincode_region("900001") == "Army Postal Service"


@pytest.mark.parametrize(
    "value",
    [
        "9876543210",
        "98765 43210",
        "098765-43210",
        "+91 98765 43210",
        "+91-98765-43210",
        "(+91) 98765 43210",
        "919876543210",
        "0091 98765 43210",
        "+919876543210",
    ],
)
def test_mobile_normalisation(value: str) -> None:
    assert normalize_mobile(value) == "+919876543210"
    assert is_valid_mobile(value)


def test_mobile_starting_with_91_is_not_stripped() -> None:
    assert normalize_mobile("9123456789") == "+919123456789"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("+1 415 555 0100", "only \\+91"),
        ("98765abc10", "other than digits"),
        ("5876543210", "starting with 6-9"),
        ("987654321", "starting with 6-9"),
        ("+91 98765 4321", "starting with 6-9"),
        ("", "starting with 6-9"),
    ],
)
def test_mobile_invalid(value: str, reason: str) -> None:
    assert not is_valid_mobile(value)
    with pytest.raises(ValidationError, match=reason):
        normalize_mobile(value)


@given(st.sampled_from("6789"), st.text(alphabet="0123456789", min_size=9, max_size=9))
def test_mobile_forms_agree(first: str, rest: str) -> None:
    number = first + rest
    expected = "+91" + number
    for form in (number, "0" + number, "91" + number, "+91 " + number, "0091" + number):
        assert normalize_mobile(form) == expected
