from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from india_utils import ValidationError, amount_in_words, number_to_words
from india_utils._words_en import english_words

_SMALL = {
    w: i
    for i, w in enumerate(
        "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen "
        "Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen".split()
    )
}
_TENS = {
    w: 10 * i
    for i, w in enumerate("_ _ Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split())
    if i >= 2
}
_SCALES = {"Hundred": 100, "Thousand": 10**3, "Lakh": 10**5, "Crore": 10**7}


def parse_english(text: str) -> int:
    """Independent parser used to round-trip the generator's output."""
    total, current = 0, 0
    for word in text.replace("-", " ").split():
        if word == "and":
            continue
        if word in _SMALL:
            current += _SMALL[word]
        elif word in _TENS:
            current += _TENS[word]
        elif word == "Hundred":
            current *= 100
        elif word == "Crore":
            total = (total + current) * 10**7
            current = 0
        else:
            total += current * _SCALES[word]
            current = 0
    return total + current


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "Zero"),
        (7, "Seven"),
        (15, "Fifteen"),
        (40, "Forty"),
        (99, "Ninety-Nine"),
        (100, "One Hundred"),
        (101, "One Hundred One"),
        (1000, "One Thousand"),
        (1001, "One Thousand One"),
        (99999, "Ninety-Nine Thousand Nine Hundred Ninety-Nine"),
        (100000, "One Lakh"),
        (1234567, "Twelve Lakh Thirty-Four Thousand Five Hundred Sixty-Seven"),
        (10000000, "One Crore"),
        (10000001, "One Crore One"),
        (123456789, "Twelve Crore Thirty-Four Lakh Fifty-Six Thousand Seven Hundred Eighty-Nine"),
        (10**9, "One Hundred Crore"),
        (10**12, "One Lakh Crore"),
        (10**14, "One Crore Crore"),
    ],
)
def test_number_to_words_en(n: int, expected: str) -> None:
    assert number_to_words(n) == expected


def test_english_options() -> None:
    assert number_to_words(105, use_and=True) == "One Hundred and Five"
    assert number_to_words(100005, use_and=True) == "One Lakh and Five"
    assert number_to_words(5, use_and=True) == "Five"
    assert number_to_words(21, hyphenate=False) == "Twenty One"
    with pytest.raises(ValueError, match="non-negative"):
        english_words(-1)


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (
            1234567.50,
            "Rupees Twelve Lakh Thirty-Four Thousand Five Hundred Sixty-Seven and Fifty Paise Only",
        ),
        (0, "Rupees Zero Only"),
        (1, "Rupees One Only"),
        (0.5, "Fifty Paise Only"),
        (0.01, "One Paisa Only"),
        (Decimal("100.005"), "Rupees One Hundred and One Paisa Only"),
        ("1,00,000", "Rupees One Lakh Only"),
    ],
)
def test_amount_in_words_en(amount: float | int | Decimal | str, expected: str) -> None:
    assert amount_in_words(amount) == expected


def test_amount_in_words_en_options() -> None:
    assert amount_in_words(1500, only=False) == "Rupees One Thousand Five Hundred"
    assert amount_in_words(21, case="upper") == "RUPEES TWENTY-ONE ONLY"
    assert amount_in_words(21, case="lower") == "rupees twenty-one only"
    assert amount_in_words(250, use_and=True) == "Rupees Two Hundred and Fifty Only"
    with pytest.raises(ValueError, match="case"):
        amount_in_words(1, case="snake")  # type: ignore[arg-type]


def test_words_reject_invalid() -> None:
    with pytest.raises(ValidationError, match="negative"):
        amount_in_words(-5)
    with pytest.raises(ValidationError, match="negative"):
        number_to_words(-5)
    with pytest.raises(ValidationError, match="whole number"):
        number_to_words(1.5)
    with pytest.raises(ValueError, match="unsupported language"):
        number_to_words(5, "hi")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported language"):
        amount_in_words(5, "hi")  # type: ignore[arg-type]


def test_whole_number_inputs() -> None:
    assert number_to_words("12,000") == "Twelve Thousand"
    assert number_to_words(Decimal("5.00")) == "Five"


@given(st.integers(min_value=0, max_value=10**18))
def test_english_roundtrip(n: int) -> None:
    words = number_to_words(n)
    assert parse_english(words) == n
    assert "  " not in words
    assert parse_english(number_to_words(n, use_and=True, hyphenate=False)) == n


@given(st.decimals(min_value=0, max_value=10**12, places=2, allow_nan=False))
def test_amount_roundtrip(value: Decimal) -> None:
    text = amount_in_words(value)
    assert text.endswith(" Only")
    rupee_part, _, paise_part = text.removesuffix(" Only").partition(" and ")
    if "Paise" in rupee_part or "Paisa" in rupee_part:
        rupee_part, paise_part = "", rupee_part
    rupees = parse_english(rupee_part.removeprefix("Rupees ")) if rupee_part else 0
    paise = parse_english(paise_part.rsplit(" ", 1)[0]) if paise_part else 0
    assert Decimal(rupees) + Decimal(paise) / 100 == value


def test_huge_amount_is_exact() -> None:
    amount = Decimal("123456789012345678901234567890.99")
    words = amount_in_words(amount)
    assert words.endswith("and Ninety-Nine Paise Only")
    rupees = words.removeprefix("Rupees ").split(" and Ninety-Nine")[0]
    assert parse_english(rupees) == 123456789012345678901234567890
