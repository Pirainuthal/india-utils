"""Tamil cardinal words using the Indian (லட்சம் / கோடி) scale.

The vocabulary lives in plain tables so a Tamil reader can review it at a
glance. Two output styles are supported:

``"sandhi"`` (default)
    Compound forms as they are normally written: tens + unit fuse with the
    final ``உ`` dropped before a vowel (இருபத்து + ஐந்து -> இருபத்தைந்து), a
    combining form fuses with a following "one" word (நூற்று + ஒன்று ->
    நூற்றொன்று, ஆயிரத்து + ஒரு -> ஆயிரத்தொரு), and a hard consonant is
    doubled after a hard-geminate ending (நூற்று + பத்து -> நூற்றுப் பத்து,
    பத்து + கோடி -> பத்துக் கோடி). Other boundaries keep a space
    (நூற்று இருபது, ஆயிரத்து இருநூறு).

``"spaced"``
    The same combining forms separated by spaces with no sound changes
    (இருபத்து ஒன்று, நூற்று பத்து). Mechanical and unambiguous; common in
    software and speech-recognition corpora.

In both styles a multiple of a thousand is one fused word (இரண்டாயிரம்,
மூவாயிரம்), and words after லட்சத்து / கோடியே are separated by a space.
"""

from __future__ import annotations

import re
from typing import Literal

__all__ = ["TamilStyle", "WordForm", "join", "tamil_words"]

TamilStyle = Literal["sandhi", "spaced"]
#: ``cardinal``: the number on its own (ஒன்று); ``adjective``: before a noun
#: such as ரூபாய் / லட்சம் / கோடி (ஒரு); ``thousand``: fused with ஆயிரம்.
WordForm = Literal["cardinal", "adjective", "thousand"]

ZERO = "பூஜ்ஜியம்"

# 1-19 as standalone numbers.
_UNITS: dict[int, str] = {
    1: "ஒன்று", 2: "இரண்டு", 3: "மூன்று", 4: "நான்கு", 5: "ஐந்து",
    6: "ஆறு", 7: "ஏழு", 8: "எட்டு", 9: "ஒன்பது", 10: "பத்து",
    11: "பதினொன்று", 12: "பன்னிரண்டு", 13: "பதின்மூன்று", 14: "பதினான்கு",
    15: "பதினைந்து", 16: "பதினாறு", 17: "பதினேழு", 18: "பதினெட்டு",
    19: "பத்தொன்பது",
}  # fmt: skip

# Forms used before a noun ("ஒரு லட்சம்", "பதினொரு கோடி", "ஒரு ரூபாய்").
_ADJECTIVE: dict[int, str] = {1: "ஒரு", 11: "பதினொரு"}

# n x 1000 for n in 1..19. 1 is "ஆயிரம்" alone but "ஓராயிரம்" at the end of a
# compound (21000 -> இருபத்தோராயிரம்); see _thousand_unit().
_THOUSANDS: dict[int, str] = {
    1: "ஆயிரம்", 2: "இரண்டாயிரம்", 3: "மூவாயிரம்", 4: "நான்காயிரம்",
    5: "ஐந்தாயிரம்", 6: "ஆறாயிரம்", 7: "ஏழாயிரம்", 8: "எட்டாயிரம்",
    9: "ஒன்பதாயிரம்", 10: "பத்தாயிரம்", 11: "பதினோராயிரம்",
    12: "பன்னிரண்டாயிரம்", 13: "பதின்மூன்றாயிரம்", 14: "பதினான்காயிரம்",
    15: "பதினைந்தாயிரம்", 16: "பதினாறாயிரம்", 17: "பதினேழாயிரம்",
    18: "பதினெட்டாயிரம்", 19: "பத்தொன்பதாயிரம்",
}  # fmt: skip
_ONE_THOUSAND_IN_COMPOUND = "ஓராயிரம்"

# Tens: (standalone, combining form, x 1000).
_TENS: dict[int, tuple[str, str, str]] = {
    2: ("இருபது", "இருபத்து", "இருபதாயிரம்"),
    3: ("முப்பது", "முப்பத்து", "முப்பதாயிரம்"),
    4: ("நாற்பது", "நாற்பத்து", "நாற்பதாயிரம்"),
    5: ("ஐம்பது", "ஐம்பத்து", "ஐம்பதாயிரம்"),
    6: ("அறுபது", "அறுபத்து", "அறுபதாயிரம்"),
    7: ("எழுபது", "எழுபத்து", "எழுபதாயிரம்"),
    8: ("எண்பது", "எண்பத்து", "எண்பதாயிரம்"),
    9: ("தொண்ணூறு", "தொண்ணூற்று", "தொண்ணூறாயிரம்"),
}

# Hundreds: (standalone, combining form).
_HUNDREDS: dict[int, tuple[str, str]] = {
    1: ("நூறு", "நூற்று"),
    2: ("இருநூறு", "இருநூற்று"),
    3: ("முந்நூறு", "முந்நூற்று"),
    4: ("நானூறு", "நானூற்று"),
    5: ("ஐந்நூறு", "ஐந்நூற்று"),
    6: ("அறுநூறு", "அறுநூற்று"),
    7: ("எழுநூறு", "எழுநூற்று"),
    8: ("எண்ணூறு", "எண்ணூற்று"),
    9: ("தொள்ளாயிரம்", "தொள்ளாயிரத்து"),
}

_LAKH, _LAKH_COMBINING = "லட்சம்", "லட்சத்து"
_CRORE, _CRORE_COMBINING = "கோடி", "கோடியே"

_U_SIGN = "ு"  # ு
_VIRAMA = "்"  # ்
# Independent vowel -> dependent vowel sign ("" for the inherent அ).
_VOWEL_SIGNS: dict[str, str] = {
    "அ": "", "ஆ": "ா", "இ": "ி", "ஈ": "ீ", "உ": "ு", "ஊ": "ூ",
    "எ": "ெ", "ஏ": "ே", "ஐ": "ை", "ஒ": "ொ", "ஓ": "ோ", "ஔ": "ௌ",
}  # fmt: skip
_HARD = "கசதப"
_ONE_INITIALS = "ஒஓ"
# வன்தொடர்க் குற்றியலுகரம்: a doubled hard consonant followed by ு (த்து, ற்று, ட்டு ...).
_HARD_GEMINATE_U = re.compile("(க்க|ச்ச|ட்ட|த்த|ப்ப|ற்ற)" + _U_SIGN + "$")


def join(left: str, right: str, style: TamilStyle, *, tens_unit: bool = False) -> str:
    """Join two number words, applying sandhi when *style* is ``"sandhi"``.

    The final ``உ`` of *left* is dropped before a vowel only for tens + unit
    (இருபத்தொன்று, இருபத்தைந்து) and before the "one" words
    ஒன்று / ஒரு / ஓராயிரம் / ஒன்பது (நூற்றொன்று, ஆயிரத்தொரு). Longer chains
    such as நூற்று இருபது or ஐந்நூற்று அறுபத்தேழு stay spaced, which is how
    they are usually written.
    """
    if style == "sandhi":
        first = right[0]
        elide = tens_unit or first in _ONE_INITIALS
        if elide and left.endswith(_U_SIGN) and first in _VOWEL_SIGNS:
            return left[:-1] + _VOWEL_SIGNS[first] + right[1:]
        if _HARD_GEMINATE_U.search(left) and first in _HARD:
            return f"{left}{first}{_VIRAMA} {right}"
    elif style != "spaced":
        raise ValueError(f"unknown Tamil style {style!r}")
    return f"{left} {right}"


def _unit(n: int, form: WordForm, in_compound: bool) -> str:
    """Words for 1-19 in the requested form."""
    if form == "adjective":
        return _ADJECTIVE.get(n, _UNITS[n])
    if form == "thousand":
        return _ONE_THOUSAND_IN_COMPOUND if (n == 1 and in_compound) else _THOUSANDS[n]
    return _UNITS[n]


def _below_100(n: int, form: WordForm, style: TamilStyle) -> str:
    if n < 20:
        return _unit(n, form, in_compound=False)
    tens, ones = divmod(n, 10)
    standalone, combining, thousand = _TENS[tens]
    if not ones:
        return thousand if form == "thousand" else standalone
    return join(combining, _unit(ones, form, in_compound=True), style, tens_unit=True)


def _below_1000(n: int, form: WordForm, style: TamilStyle) -> str:
    hundreds, rest = divmod(n, 100)
    if not hundreds:
        return _below_100(rest, form, style)
    standalone, combining = _HUNDREDS[hundreds]
    if not rest:
        return standalone
    return join(combining, _below_100(rest, form, style), style)


def tamil_words(n: int, *, form: WordForm = "cardinal", style: TamilStyle = "sandhi") -> str:
    """Spell a non-negative integer in Tamil.

    *form* only affects the last word: ``"adjective"`` gives the form used
    before a noun (``ஒரு`` instead of ``ஒன்று``), which is what amounts in
    words need (``ஒரு ரூபாய்``, ``இருபத்தொரு ரூபாய்``).
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if form not in ("cardinal", "adjective"):
        raise ValueError(f"unsupported form {form!r}")
    if style not in ("sandhi", "spaced"):
        raise ValueError(f"unknown Tamil style {style!r}")
    if n == 0:
        return ZERO

    crore, rest = divmod(n, 10**7)
    lakh, rest = divmod(rest, 10**5)
    thousand, below = divmod(rest, 1000)

    words = ""

    def append(segment: str, *, after_scale: bool) -> None:
        nonlocal words
        if not words:
            words = segment
        elif after_scale:
            words = f"{words} {segment}"  # after லட்சத்து / கோடியே: plain space
        else:
            words = join(words, segment, style)

    if crore:
        last = not (lakh or thousand or below)
        multiplier = tamil_words(crore, form="adjective", style=style)
        append(join(multiplier, _CRORE if last else _CRORE_COMBINING, style), after_scale=True)
    if lakh:
        last = not (thousand or below)
        multiplier = _below_100(lakh, "adjective", style)
        append(f"{multiplier} {_LAKH if last else _LAKH_COMBINING}", after_scale=True)
    if thousand:
        segment = _below_100(thousand, "thousand", style)
        if below:
            segment = segment[: -len("ம்")] + "த்து"  # ஆயிரம் -> ஆயிரத்து
        append(segment, after_scale=True)
    if below:
        append(_below_1000(below, form, style), after_scale=not thousand)
    return words
