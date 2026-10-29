from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from india_utils import ValidationError, format_indian_number, format_inr, format_inr_compact
from india_utils._numbers import group_indian, quantize, to_decimal


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0, "₹0.00"),
        (1, "₹1.00"),
        (999, "₹999.00"),
        (1000, "₹1,000.00"),
        (99999, "₹99,999.00"),
        (100000, "₹1,00,000.00"),
        (1234567.5, "₹12,34,567.50"),
        (10000000, "₹1,00,00,000.00"),
        (123456789012, "₹1,23,45,67,89,012.00"),
        (Decimal("0.005"), "₹0.01"),  # half-up, not banker's rounding
        (Decimal("0.015"), "₹0.02"),
        (2.675, "₹2.68"),  # float goes through repr, so no binary surprise
        ("12,34,567.5", "₹12,34,567.50"),
        ("₹ 1,000", "₹1,000.00"),
        (-1234567.5, "-₹12,34,567.50"),
        ("-₹500", "-₹500.00"),
        (Decimal("-0.001"), "₹0.00"),  # no negative zero
    ],
)
def test_format_inr(amount: int | float | Decimal | str, expected: str) -> None:
    assert format_inr(amount) == expected


def test_format_inr_options() -> None:
    assert format_inr(1500, symbol="Rs. ", decimals=0) == "Rs. 1,500"
    assert format_inr(-1500, negative_style="parentheses") == "(₹1,500.00)"
    assert format_inr(1234.5678, decimals=3) == "₹1,234.568"
    assert format_inr(10**30) == "₹" + group_indian(str(10**30)) + ".00"


def test_format_inr_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="negative_style"):
        format_inr(-1, negative_style="brackets")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="decimals"):
        format_inr(1, decimals=-1)


def test_format_indian_number() -> None:
    assert format_indian_number(1234567) == "12,34,567"
    assert format_indian_number("-98765.432", decimals=2) == "-98,765.43"


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0, "0"),
        (999.5, "999.5"),
        (999.999, "1 K"),  # rounds to 1000.00 and is promoted
        (45250, "45.25 K"),
        (1234567, "12.35 L"),
        (100000, "1 L"),
        (9999999, "1 Cr"),  # 99.99999 L rounds to 100 L -> 1 Cr
        (12000000, "1.2 Cr"),
        (15000000000, "1,500 Cr"),
        (-250000, "-2.5 L"),
        (-0.001, "0"),
    ],
)
def test_format_inr_compact(amount: int | float, expected: str) -> None:
    assert format_inr_compact(amount) == expected


def test_format_inr_compact_options() -> None:
    assert format_inr_compact(12000000, symbol="₹") == "₹1.2 Cr"
    assert format_inr_compact(45250, thousands=False) == "45,250"
    assert format_inr_compact(99999.999, thousands=False) == "1 L"
    assert format_inr_compact(1234567, decimals=0) == "12 L"
    assert format_inr_compact(1250000, decimals=1) == "12.5 L"


@pytest.mark.parametrize(
    "bad",
    [True, "abc", "", "  ", "-", float("nan"), float("inf"), "Infinity", "--5", "-₹-5", "-+5"],
)
def test_to_decimal_rejects(bad: bool | str | float) -> None:
    with pytest.raises(ValidationError):
        to_decimal(bad)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("-5", Decimal(-5)), ("- ₹ 5", Decimal(-5)), ("₹-5", Decimal(-5)), ("+5", Decimal(5))],
)
def test_to_decimal_signs(text: str, expected: Decimal) -> None:
    assert to_decimal(text) == expected


def test_to_decimal_rejects_wrong_type() -> None:
    with pytest.raises(TypeError):
        to_decimal([1])  # type: ignore[arg-type]


def test_quantize_large_value() -> None:
    assert quantize(Decimal(10) ** 40, 2) == Decimal(10) ** 40


@given(st.integers(min_value=0, max_value=10**20))
def test_group_indian_roundtrip(n: int) -> None:
    grouped = group_indian(str(n))
    assert grouped.replace(",", "") == str(n)
    groups = grouped.split(",")
    assert len(groups[-1]) == min(3, len(str(n)))
    assert all(len(g) == 2 for g in groups[1:-1])
    assert 1 <= len(groups[0]) <= (3 if len(groups) == 1 else 2)


@given(st.decimals(min_value=-(10**15), max_value=10**15, places=2, allow_nan=False))
def test_format_inr_roundtrip(value: Decimal) -> None:
    text = format_inr(value)
    parsed = to_decimal(text)
    assert parsed == value


def test_huge_inputs() -> None:
    big = "-" + "9" * 35
    assert to_decimal(big) == Decimal(big)
    assert format_indian_number(big) == "-" + group_indian("9" * 35)
    with pytest.raises(ValidationError, match="integer digits"):
        to_decimal("1e999999")
    assert to_decimal("1e-999999") > 0
    assert to_decimal("0") == 0
