# india-utils

**Indian number formats and identifier validation for Python: lakh/crore formatting, rupee amounts in words in English and Tamil, and GSTIN, PAN, IFSC, PIN code and mobile number checks. Zero dependencies, fully typed.**

[![CI](https://github.com/Pirainuthal/india-utils/actions/workflows/ci.yml/badge.svg)](https://github.com/Pirainuthal/india-utils/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](pyproject.toml)
[![Typed: mypy --strict](https://img.shields.io/badge/typing-mypy%20--strict-informational.svg)](pyproject.toml)
[![Coverage 100%](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](#testing)

```python
>>> from india_utils import format_inr, amount_in_words, parse_gstin
>>> format_inr(1234567.5)
'₹12,34,567.50'
>>> amount_in_words(1001, lang="ta")
'ஆயிரத்தொரு ரூபாய் மட்டும்'
>>> parse_gstin("29AAACB1234C1ZB").state_name
'Karnataka'
```

## Why

Invoices, payment screens and KYC forms in India all need the same handful of helpers, and each app ends up with its own copy. Common mistakes:

- **Western grouping** (`1,234,567`) where Indian readers expect `12,34,567`.
- **Float rounding.** `round(2.675, 2)` returns `2.67` in Python, but the invoice should say `2.68`.
- **Regex-only GSTIN checks** that accept typos, because the mod-36 check digit is never computed.
- **No Tamil "amount in words"**, or one that writes `ஒன்று ரூபாய்` where Tamil says `ஒரு ரூபாய்`.

`india-utils` does these jobs in one small package. Every amount is handled as a `Decimal` and every rule comes with tests.

## Install

The package name is **`india-utils`**. The name was free on PyPI when this README was written; the package is not published yet.

```bash
pip install india-utils
```

Until it is on PyPI, install from source:

```bash
git clone https://github.com/Pirainuthal/india-utils
cd india-utils
pip install .
```

You need Python 3.10 or newer. The package has no runtime dependencies.

## Quick usage

Every example below is real output from this repository.

### Rupee formatting (lakh / crore grouping)

```python
>>> from india_utils import format_inr, format_inr_compact, format_indian_number
>>> format_inr(1234567.5)
'₹12,34,567.50'
>>> format_inr(-1500, symbol="Rs. ", decimals=0)
'-Rs. 1,500'
>>> format_indian_number(123456789)
'12,34,56,789'
>>> format_inr_compact(12000000, symbol="₹")
'₹1.2 Cr'
>>> format_inr_compact(9999999)        # rounds to 100 L, so it is promoted to Cr
'1 Cr'
```

### Amount in words: English

```python
>>> from india_utils import amount_in_words, number_to_words
>>> amount_in_words(1234567.50)
'Rupees Twelve Lakh Thirty-Four Thousand Five Hundred Sixty-Seven and Fifty Paise Only'
>>> number_to_words(10**12)
'One Lakh Crore'
>>> amount_in_words(250, use_and=True, case="upper")
'RUPEES TWO HUNDRED AND FIFTY ONLY'
```

### Amount in words: Tamil (தமிழ்)

```python
>>> number_to_words(100000, lang="ta")
'ஒரு லட்சம்'
>>> number_to_words(10**12, lang="ta")
'ஒரு லட்சம் கோடி'
>>> amount_in_words(1001, lang="ta")
'ஆயிரத்தொரு ரூபாய் மட்டும்'
>>> amount_in_words(21, lang="ta", style="spaced")
'இருபத்து ஒரு ரூபாய் மட்டும்'
```

### GSTIN, PAN and IFSC

```python
>>> from india_utils import parse_gstin, gstin_check_digit, parse_pan, parse_ifsc, ValidationError
>>> g = parse_gstin("29AAACB1234C1ZB")
>>> g
GSTIN(value='29AAACB1234C1ZB', state_code='29', state_name='Karnataka', pan='AAACB1234C', entity_number='1', default_char='Z', check_digit='B')
>>> g.pan_holder_type
'Company'
>>> gstin_check_digit("33ABCPE1234F1Z")
'I'
>>> try:
...     parse_gstin("29AAACB1234C1ZC")
... except ValidationError as e:
...     print(e.field, "->", e.reason)
gstin -> check digit mismatch: got 'C', expected 'B'
>>> parse_pan("abcpe1234f")
PAN(value='ABCPE1234F', holder_type_code='P', holder_type='Individual', name_initial='E', sequence='1234', check_char='F')
>>> parse_ifsc("HDFC0001234")
IFSC(value='HDFC0001234', bank_code='HDFC', branch_code='001234', bank_name='HDFC Bank')
```

### PIN codes and mobile numbers

```python
>>> from india_utils import normalize_mobile, pincode_region
>>> normalize_mobile("+91 98765 43210")
'+919876543210'
>>> pincode_region("600001")
'Tamil Nadu, Kerala, Puducherry, Lakshadweep'
```

### Command line

```console
$ india-utils format 1234567 --compact
12.35 L
$ india-utils format --parentheses -- -1500
(₹1,500.00)
$ india-utils words 12345 --lang ta
பன்னிரண்டாயிரத்து முந்நூற்று நாற்பத்தைந்து ரூபாய் மட்டும்
$ india-utils words 2100000 --lang ta --number
இருபத்தொரு லட்சம்
$ india-utils words 2100000 --lang ta --number --spaced
இருபத்து ஒரு லட்சம்
$ india-utils gstin check 29AAACB1234C1ZB
value            29AAACB1234C1ZB
state code       29
state name       Karnataka
pan              AAACB1234C
entity number    1
default char     Z
check digit      B
pan holder type  Company
$ india-utils gstin check 29AAACB1234C1ZC
error: invalid gstin: check digit mismatch: got 'C', expected 'B'
$ echo $?
1
$ india-utils pan check ABCPE1234F --json
{"valid": true, "value": "ABCPE1234F", "holder_type_code": "P", "holder_type": "Individual", "name_initial": "E", "sequence": "1234", "check_char": "F"}
$ india-utils ifsc check SBIN0000001
value        SBIN0000001
bank code    SBIN
branch code  000001
bank name    State Bank of India
$ india-utils mobile normalize 098765-43210
+919876543210
```

Exit status is `0` on success, `1` for invalid input and `2` for a usage error. `python -m india_utils ...` works too. Put options before `--` when the amount is negative.

## API reference

All public names are importable from `india_utils`. Every validator raises `ValidationError`, a subclass of `ValueError` with `.field` and `.reason` attributes, and has an `is_valid_*` companion that returns a `bool`. Amount arguments accept `int`, `float`, `Decimal` or `str`. Strings may contain commas, a leading `₹` and one leading sign (`"--5"` is rejected, not read as 5). Floats are converted through `repr`, so `2.675` stays `2.675`.

| Function | Returns | Notes |
|---|---|---|
| `format_inr(amount, *, symbol="₹", decimals=2, negative_style="minus")` | `str` | Half-up rounding. `negative_style="parentheses"` gives `(₹1,500.00)`. |
| `format_indian_number(amount, decimals=0)` | `str` | Same grouping with no symbol. |
| `format_inr_compact(amount, *, symbol="", decimals=2, thousands=True)` | `str` | `K` / `L` / `Cr`, trailing zeros dropped, overflow promoted to the next unit. |
| `number_to_words(n, lang="en", *, style="sandhi", hyphenate=True, use_and=False)` | `str` | Whole numbers ≥ 0. `style` applies to Tamil; `hyphenate` and `use_and` to English. |
| `amount_in_words(amount, lang="en", *, only=True, style="sandhi", hyphenate=True, use_and=False, case="title")` | `str` | Rounds to paise. Negative amounts are rejected. `case` (`title`/`upper`/`lower`) applies to English. |
| `parse_gstin(value, *, allow_legacy_state_codes=False)` / `is_valid_gstin` | `GSTIN` / `bool` | Checks the layout, state code, embedded PAN holder type and check digit. |
| `gstin_check_digit(first14)` | `str` | Luhn mod-36 check character. |
| `parse_pan(value)` / `is_valid_pan` / `pan_holder_type` | `PAN` / `bool` / `str` | Checks the format and the holder type (4th character). |
| `parse_ifsc(value)` / `is_valid_ifsc` | `IFSC` / `bool` | Checks the format. `bank_name` comes from a small table of common banks, or is `None`. |
| `normalize_pincode` / `is_valid_pincode` / `pincode_region` | `str` / `bool` / `str` | Six digits, not starting with 0. The region comes from the first digit. |
| `normalize_mobile` / `is_valid_mobile` | `str` / `bool` | Returns `+91XXXXXXXXXX`. Accepts `0`, `91`, `+91` and `0091` prefixes, spaces, dashes and brackets. |
| `state_name(code, *, allow_legacy=False)`, `STATE_CODES` | `str \| None`, `dict` | GST state and UT codes. |

`GSTIN`, `PAN` and `IFSC` are frozen dataclasses, and `str()` on any of them returns the normalised value.

## Design notes and sources

### Indian grouping and rounding
The last three integer digits form one group and every group to the left has two digits. Amounts are `Decimal` from start to finish. Rounding is `ROUND_HALF_UP`, so `0.005` becomes `0.01`, the way invoices are rounded, not banker's rounding. Very large values keep every digit: the code uses `copy_abs()` and a wider decimal context instead of `abs()`, which would round to 28 significant digits. Inputs of 10^40 or more are rejected so that a string like `"1e999999"` cannot use up memory.

### English words
The text follows the layout used on Indian cheques: `Rupees … and … Paise Only`. Crore is recursive, so 10^12 is "One Lakh Crore" and 10^14 is "One Crore Crore". One paisa is written "One Paisa".

### Tamil number words
The vocabulary lives in plain tables in [`src/india_utils/_words_ta.py`](src/india_utils/_words_ta.py), so a Tamil reader can review it quickly. There are two styles:

- **`sandhi` (default).** Tens and units fuse, dropping the final உ before a vowel: இருபத்தொன்று, இருபத்தைந்து, தொண்ணூற்றொன்று. A combining form fuses with a following "one" word: நூற்றொன்று, ஆயிரத்தொரு. A hard consonant doubles after a hard-geminate ending: நூற்றுப் பத்து, ஆயிரத்துத் தொள்ளாயிரம், பத்துக் கோடி. Other boundaries keep a space (நூற்று இருபது, ஐந்நூற்று அறுபத்தேழு), and so do the words after லட்சத்து and கோடியே.
- **`spaced`.** The same combining forms with no sound changes: இருபத்து ஒன்று, நூற்று பத்து. This style is mechanical and unambiguous.

Both styles write multiples of a thousand as one word (இரண்டாயிரம், மூவாயிரம், பதினோராயிரம், இருபத்தோராயிரம்). Before a noun, "one" becomes ஒரு: ஒரு லட்சம், இருபத்தொரு ரூபாய், ஆயிரத்தொரு ரூபாய். Amounts read `<ரூபாய்> ரூபாய் <பைசா> பைசா மட்டும்`.

Sources checked:
- [Tamil numerals (English Wikipedia)](https://en.wikipedia.org/wiki/Tamil_numerals): 0–10, the tens, நூறு, ஆயிரம், பத்தாயிரம், இலட்சம், கோடி, பத்துக் கோடி, and the combining form நூற்று.
- [தமிழ் எண்கள் (Tamil Wikipedia)](https://ta.wikipedia.org/wiki/தமிழ்_எண்கள்)
- [learntamil.com: numbers](https://www.learntamil.com/part1/intro/numbers-1-100-fractions/): 11–19.
- The number-word list in C-DAC's [Tamil ASR demo](https://huggingface.co/spaces/cdactvm/Tamil_ASR_Demo/blob/c7b93d703634ff761bc314e5179e2ce8b3885962/replaceWords.py): both the spaced and the joined forms for 21–99, e.g. இருபத்து ஒன்று / இருபத்தொன்று, தொண்ணூற்று ஒன்று / தொண்ணூற்றொன்று.

`tests/test_words_ta.py` separates the values checked against those sources (`VERIFIED`) from forms that come out of the documented rules and match common usage but were not in those sources (`CONVENTIONAL`). For spelling variants, the tables use the classical forms: முந்நூறு (not முன்னூறு), ஐந்நூறு (not ஐநூறு) and பதின்மூன்று (not பதிமூன்று). Review by a native speaker is welcome; see the roadmap.

### GSTIN
A GSTIN is the 2-digit state code, the 10-character PAN, an entity number (1–9, then A–Z), `Z`, and a check character. The check character uses Luhn mod N over `0-9A-Z` (N = 36). Reading left to right, the weights alternate 1, 2, 1, 2, … Each product adds `product // 36 + product % 36` to a running total, and the check value is `(36 − total % 36) % 36`. Luhn mod N catches every single-character substitution, and a Hypothesis property test checks this. `tests/test_gstin.py` includes a check digit worked by hand. Every GSTIN in this README and in the tests is made up from a fictitious PAN.

The state codes follow the GST state code table: 01–38, with 25 and 28 missing, plus 97 "Other Territory". [Zoho's list of valid GST state codes](https://www.zoho.com/in/books/kb/gst/valid-state-codes-list.html) reproduces the same table. Code 25 (Daman and Diu, merged into 26 in 2020) and code 28 (pre-bifurcation Andhra Pradesh) are only accepted with `allow_legacy_state_codes=True`.

### PAN
The format is `AAAAA9999A`. The 4th character gives the holder type: P Individual, C Company, H HUF, F Firm/LLP, A AOP, T Trust, B BOI, L Local Authority, J Artificial Juridical Person, G Government. Sources: [Income Tax Department PAN tutorial](https://incometaxindia.gov.in/tutorials/1.permanent%20account%20number%20(pan).pdf) and [Wikipedia](https://en.wikipedia.org/wiki/Permanent_account_number). The algorithm for the 10th (check) character is not published, so this library checks the format only.

### IFSC, PIN code and mobile
- **IFSC** (RBI layout): 4 letters for the bank, a literal `0`, then 6 alphanumeric characters for the branch. The format is checked, but the branch is not looked up.
- **PIN regions** come from the first digit, following [India Post's zones](https://en.wikipedia.org/wiki/Postal_Index_Number). 9 is the Army Postal Service.
- **Mobile numbers** have 10 digits starting with 6–9, normalised to E.164.

## Testing

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy                       # strict, covers src/ and tests/
pytest --cov               # unit, property-based (Hypothesis) and doctests
```

The suite has **305 tests and 100% line and branch coverage**. The README examples above run as doctests too. CI enforces at least 95%. The property tests include:
- English words round-trip through an independent parser for any integer up to 10^18.
- `format_inr` output parses back to the same `Decimal`.
- Every generated GSTIN validates, and any single-character substitution is detected.
- Tamil words are distinct for every number from 0 to 2,00,000 in both styles.

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs lint and mypy, runs the tests on Python 3.10–3.13, then builds the wheel and smoke-tests it.

## Roadmap

- [ ] Review of the Tamil forms by native speakers, and an option for spelling variants (முன்னூறு, ஐநூறு, பதிமூன்று).
- [ ] Hindi (`hi`) amount in words.
- [ ] Special GSTIN formats: UIN, OIDAR, NRTP, TDS/TCS.
- [ ] Optional offline IFSC and PIN code datasets as a separate extra.
- [ ] Aadhaar Verhoeff checksum and UPI VPA validation.

## License

[MIT](LICENSE) © 2026 [Pirainuthal S](https://github.com/Pirainuthal)
