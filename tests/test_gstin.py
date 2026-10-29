from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from india_utils import (
    STATE_CODES,
    ValidationError,
    gstin_check_digit,
    is_valid_gstin,
    parse_gstin,
    state_name,
)
from india_utils.gstin import _ALPHABET

# A made-up GSTIN (fictitious PAN AAACB1234C) with a correct check digit.
SAMPLE = "29AAACB1234C1ZB"


def make_gstin(state: str, pan: str, entity: str = "1") -> str:
    body = f"{state}{pan}{entity}Z"
    return body + gstin_check_digit(body)


def test_sample() -> None:
    g = parse_gstin(SAMPLE)
    assert g.state_code == "29"
    assert g.state_name == "Karnataka"
    assert g.pan == "AAACB1234C"
    assert g.pan_holder_type == "Company"
    assert g.entity_number == "1"
    assert g.default_char == "Z"
    assert g.check_digit == "B"
    assert str(g) == SAMPLE


def test_check_digit_known_values() -> None:
    assert gstin_check_digit("29AAACB1234C1Z") == "B"
    # Worked by hand. Values 3,3,10,11,12,25,14,1,2,3,4,15,1,35 with weights
    # 1,2,1,2,...: products 3,6,10,22,12,50,14,2,2,6,4,30,1,70. Products >= 36
    # contribute quotient + remainder (50 -> 1+14, 70 -> 1+34), giving a total
    # of 162. 162 % 36 = 18 and (36 - 18) % 36 = 18 -> "I".
    assert gstin_check_digit("33ABCPE1234F1Z") == "I"


def test_normalisation() -> None:
    assert parse_gstin(" 29aaacb1234c1zb ").value == SAMPLE
    assert is_valid_gstin("29 AAACB 1234C 1ZB")


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("29AAACB1234C1Z", "expected 15 characters"),
        ("29AAACB1234C1ZBX", "expected 15 characters"),
        ("2AAAACB1234C1ZB", "expected 2 digits"),
        ("29AAACB1234C0ZB", "expected 2 digits"),  # entity number cannot be 0
        ("29AAACB1234C1YB", "expected 2 digits"),  # 14th char must be Z
        ("29AAAC11234C1ZB", "expected 2 digits"),
        ("29AAACB1234C1Z-", "expected 2 digits"),
        ("29AAACB1234C1ZC", "check digit mismatch"),
        ("40AAACB1234C1ZB", "unknown state code '40'"),
        ("00AAACB1234C1ZB", "unknown state code '00'"),
    ],
)
def test_invalid(value: str, reason: str) -> None:
    assert not is_valid_gstin(value)
    with pytest.raises(ValidationError, match=reason) as info:
        parse_gstin(value)
    assert info.value.field == "gstin"
    assert isinstance(info.value, ValueError)


def test_unknown_pan_holder_type() -> None:
    value = make_gstin("33", "ABCXE1234F")
    with pytest.raises(ValidationError, match="holder type 'X'"):
        parse_gstin(value)


def test_legacy_state_codes() -> None:
    legacy = make_gstin("25", "ABCPE1234F")
    assert not is_valid_gstin(legacy)
    g = parse_gstin(legacy, allow_legacy_state_codes=True)
    assert g.state_name.startswith("Daman and Diu")
    assert state_name("28", allow_legacy=True) == "Andhra Pradesh (pre-bifurcation code)"
    assert state_name("28") is None


def test_every_state_code_accepted() -> None:
    for code, name in STATE_CODES.items():
        g = parse_gstin(make_gstin(code, "ABCPE1234F", "A"))
        assert g.state_name == name
    assert len(STATE_CODES) == 37
    assert STATE_CODES["33"] == "Tamil Nadu"
    assert STATE_CODES["37"] == "Andhra Pradesh"
    assert STATE_CODES["38"] == "Ladakh"


def test_check_digit_errors() -> None:
    with pytest.raises(ValidationError, match="exactly 14"):
        gstin_check_digit("29AAACB")
    with pytest.raises(ValidationError, match="not 0-9 or A-Z"):
        gstin_check_digit("29AAACB1234C1#")


_states = st.sampled_from(sorted(STATE_CODES))
_letters = st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=1)
_pans = st.builds(
    lambda a, t, d, c: a + t + d + c,
    st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=3, max_size=3),
    st.sampled_from("ABCFGHJLPT"),
    st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=1).flatmap(
        lambda first: st.text(alphabet="0123456789", min_size=4, max_size=4).map(
            lambda digits: first + digits
        )
    ),
    _letters,
)
_entities = st.sampled_from("123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")


@given(_states, _pans, _entities)
def test_generated_gstins_validate(state: str, pan: str, entity: str) -> None:
    value = make_gstin(state, pan, entity)
    assert is_valid_gstin(value)
    assert parse_gstin(value).pan == pan


@given(_states, _pans, _entities, st.integers(min_value=0, max_value=14), st.data())
def test_single_substitution_is_detected(
    state: str, pan: str, entity: str, position: int, data: st.DataObject
) -> None:
    """Luhn mod N catches every single-character substitution."""
    value = make_gstin(state, pan, entity)
    replacement = data.draw(st.sampled_from([c for c in _ALPHABET if c != value[position]]))
    mutated = value[:position] + replacement + value[position + 1 :]
    assert gstin_check_digit(mutated[:14]) != mutated[14]
