"""Tamil number words.

``VERIFIED`` lists values checked against an external source (see the README's
"Tamil number words" section): Tamil and English Wikipedia "Tamil numerals"
pages, learntamil.com, and the number-word list in C-DAC's Tamil ASR demo,
which gives both spaced (இருபத்து ஒன்று) and joined (இருபத்தொன்று) forms.
``CONVENTIONAL`` lists forms produced by the documented sandhi rules that
match common written usage but were not found in one of those sources; they
are pinned here so any change is deliberate and reviewable.
"""

from __future__ import annotations

import re

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from india_utils import amount_in_words, number_to_words
from india_utils._words_ta import _THOUSANDS, _UNITS, join, tamil_words

VERIFIED: dict[int, str] = {
    0: "பூஜ்ஜியம்",
    1: "ஒன்று",
    2: "இரண்டு",
    3: "மூன்று",
    4: "நான்கு",
    5: "ஐந்து",
    6: "ஆறு",
    7: "ஏழு",
    8: "எட்டு",
    9: "ஒன்பது",
    10: "பத்து",
    11: "பதினொன்று",
    12: "பன்னிரண்டு",
    13: "பதின்மூன்று",
    14: "பதினான்கு",
    15: "பதினைந்து",
    16: "பதினாறு",
    17: "பதினேழு",
    18: "பதினெட்டு",
    19: "பத்தொன்பது",
    20: "இருபது",
    21: "இருபத்தொன்று",
    22: "இருபத்திரண்டு",
    29: "இருபத்தொன்பது",
    30: "முப்பது",
    31: "முப்பத்தொன்று",
    32: "முப்பத்திரண்டு",
    39: "முப்பத்தொன்பது",
    40: "நாற்பது",
    50: "ஐம்பது",
    60: "அறுபது",
    70: "எழுபது",
    80: "எண்பது",
    90: "தொண்ணூறு",
    91: "தொண்ணூற்றொன்று",
    92: "தொண்ணூற்றிரண்டு",
    99: "தொண்ணூற்றொன்பது",
    100: "நூறு",
    1000: "ஆயிரம்",
    10000: "பத்தாயிரம்",
    100000: "ஒரு லட்சம்",
    10000000: "ஒரு கோடி",
    100000000: "பத்துக் கோடி",
}

VERIFIED_SPACED: dict[int, str] = {
    21: "இருபத்து ஒன்று",
    23: "இருபத்து மூன்று",
    25: "இருபத்து ஐந்து",
    31: "முப்பத்து ஒன்று",
    91: "தொண்ணூற்று ஒன்று",
    99: "தொண்ணூற்று ஒன்பது",
}

CONVENTIONAL: dict[int, str] = {
    23: "இருபத்து மூன்று",
    24: "இருபத்து நான்கு",
    25: "இருபத்தைந்து",
    26: "இருபத்தாறு",
    27: "இருபத்தேழு",
    28: "இருபத்தெட்டு",
    101: "நூற்றொன்று",
    109: "நூற்றொன்பது",
    110: "நூற்றுப் பத்து",
    120: "நூற்று இருபது",
    190: "நூற்றுத் தொண்ணூறு",
    200: "இருநூறு",
    300: "முந்நூறு",
    400: "நானூறு",
    500: "ஐந்நூறு",
    600: "அறுநூறு",
    700: "எழுநூறு",
    800: "எண்ணூறு",
    900: "தொள்ளாயிரம்",
    567: "ஐந்நூற்று அறுபத்தேழு",
    999: "தொள்ளாயிரத்துத் தொண்ணூற்றொன்பது",
    1001: "ஆயிரத்தொன்று",
    1010: "ஆயிரத்துப் பத்து",
    1100: "ஆயிரத்து நூறு",
    1200: "ஆயிரத்து இருநூறு",
    1900: "ஆயிரத்துத் தொள்ளாயிரம்",
    2000: "இரண்டாயிரம்",
    3000: "மூவாயிரம்",
    4000: "நான்காயிரம்",
    9000: "ஒன்பதாயிரம்",
    11000: "பதினோராயிரம்",
    13000: "பதின்மூன்றாயிரம்",
    20000: "இருபதாயிரம்",
    21000: "இருபத்தோராயிரம்",
    23000: "இருபத்து மூவாயிரம்",
    25000: "இருபத்தைந்தாயிரம்",
    90000: "தொண்ணூறாயிரம்",
    100001: "ஒரு லட்சத்து ஒன்று",
    101000: "ஒரு லட்சத்து ஆயிரம்",
    110000: "ஒரு லட்சத்து பத்தாயிரம்",
    1100000: "பதினொரு லட்சம்",
    2100000: "இருபத்தொரு லட்சம்",
    1234567: "பன்னிரண்டு லட்சத்து முப்பத்து நான்காயிரத்து ஐந்நூற்று அறுபத்தேழு",
    10000001: "ஒரு கோடியே ஒன்று",
    12000000: "ஒரு கோடியே இருபது லட்சம்",
    80000000: "எட்டுக் கோடி",
    20000000: "இரண்டு கோடி",
    10**9: "நூறு கோடி",
    10**10: "ஆயிரம் கோடி",
    1001 * 10**7: "ஆயிரத்தொரு கோடி",
    10**12: "ஒரு லட்சம் கோடி",
    10**14: "ஒரு கோடி கோடி",
}


@pytest.mark.parametrize(("n", "expected"), sorted(VERIFIED.items()))
def test_verified_values(n: int, expected: str) -> None:
    assert number_to_words(n, "ta") == expected


@pytest.mark.parametrize(("n", "expected"), sorted(VERIFIED_SPACED.items()))
def test_verified_spaced_values(n: int, expected: str) -> None:
    assert number_to_words(n, "ta", style="spaced") == expected


@pytest.mark.parametrize(("n", "expected"), sorted(CONVENTIONAL.items()))
def test_conventional_values(n: int, expected: str) -> None:
    assert number_to_words(n, "ta") == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (101, "நூற்று ஒன்று"),
        (110, "நூற்று பத்து"),
        (1001, "ஆயிரத்து ஒன்று"),
        (21000, "இருபத்து ஓராயிரம்"),
        (2100000, "இருபத்து ஒரு லட்சம்"),
        (10**8, "பத்து கோடி"),
        (
            1234567,
            "பன்னிரண்டு லட்சத்து முப்பத்து நான்காயிரத்து ஐந்நூற்று அறுபத்து ஏழு",
        ),
    ],
)
def test_spaced_style(n: int, expected: str) -> None:
    assert number_to_words(n, "ta", style="spaced") == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [(1, "ஒரு"), (11, "பதினொரு"), (21, "இருபத்தொரு"), (101, "நூற்றொரு"), (1001, "ஆயிரத்தொரு")],
)
def test_adjective_form(n: int, expected: str) -> None:
    assert tamil_words(n, form="adjective") == expected


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (100000, "ஒரு லட்சம் ரூபாய் மட்டும்"),
        (1, "ஒரு ரூபாய் மட்டும்"),
        (21, "இருபத்தொரு ரூபாய் மட்டும்"),
        (1001, "ஆயிரத்தொரு ரூபாய் மட்டும்"),
        (0, "பூஜ்ஜியம் ரூபாய் மட்டும்"),
        (0.5, "ஐம்பது பைசா மட்டும்"),
        (0.01, "ஒரு பைசா மட்டும்"),
        (
            1234567.5,
            "பன்னிரண்டு லட்சத்து முப்பத்து நான்காயிரத்து ஐந்நூற்று அறுபத்தேழு ரூபாய் ஐம்பது பைசா மட்டும்",
        ),
    ],
)
def test_amount_in_words_ta(amount: float, expected: str) -> None:
    assert amount_in_words(amount, "ta") == expected


def test_amount_in_words_ta_options() -> None:
    assert amount_in_words(1500, "ta", only=False) == "ஆயிரத்து ஐந்நூறு ரூபாய்"
    assert amount_in_words(21, "ta", style="spaced") == "இருபத்து ஒரு ரூபாய் மட்டும்"


def test_thousand_table_matches_sandhi_rule() -> None:
    """Every x-thousand form except the documented irregulars follows u-elision."""
    irregular = {1, 3, 11}  # ஆயிரம், மூவாயிரம், பதினோராயிரம்
    for n, word in _THOUSANDS.items():
        if n not in irregular:
            assert join(_UNITS[n], "ஆயிரம்", "sandhi", tens_unit=True) == word


def test_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        tamil_words(-1)
    with pytest.raises(ValueError, match="form"):
        tamil_words(1, form="thousand")
    with pytest.raises(ValueError, match="style"):
        tamil_words(1, style="poetic")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="style"):
        join("இருபத்து", "ஒன்று", "poetic")  # type: ignore[arg-type]


def test_distinct_words_up_to_two_lakh() -> None:
    for style in ("sandhi", "spaced"):
        seen = {tamil_words(n, style=style) for n in range(200_001)}
        assert len(seen) == 200_001


_ALLOWED = set("அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநபமயரலவழளறனஜஷஸஹ ாிீுூெேைொோௌ்")


@given(st.integers(min_value=0, max_value=10**16), st.sampled_from(["sandhi", "spaced"]))
@example(50_000_000_000, "spaced")  # ஐந்தாயிரம் கோடி: a ம் before a space is fine
def test_output_is_clean_tamil(n: int, style: str) -> None:
    words = tamil_words(n, style=style)  # type: ignore[arg-type]
    assert set(words) <= _ALLOWED
    assert "  " not in words
    assert words == words.strip()
    if style == "spaced":
        # Spaced style never inserts a doubled hard consonant (க் ச் த் ப்) before a
        # space. A word may still end in ம் before a space: ஐந்தாயிரம் கோடி.
        assert not re.search("[கசதப]் ", words)


@given(st.integers(min_value=1, max_value=10**12))
def test_adjective_differs_only_at_the_end(n: int) -> None:
    cardinal = tamil_words(n)
    adjective = tamil_words(n, form="adjective")
    if n % 100 in (1, 11) or (n % 10 == 1 and n % 100 > 20):
        assert cardinal != adjective
        assert cardinal.endswith("ன்று")
        assert adjective.endswith("ரு")
    else:
        assert cardinal == adjective
