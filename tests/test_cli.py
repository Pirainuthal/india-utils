from __future__ import annotations

import json
import re
import runpy
import subprocess
import sys

import pytest

from india_utils.cli import main


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def test_format(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "format", "1234567.5") == (0, "₹12,34,567.50\n", "")
    assert run(capsys, "format", "1234567", "--compact")[1] == "12.35 L\n"
    assert run(capsys, "format", "--parentheses", "--", "-1500")[1] == "(₹1,500.00)\n"
    assert run(capsys, "format", "1500", "--symbol", "Rs. ", "--decimals", "0")[1] == "Rs. 1,500\n"


def test_words(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "words", "12345")[1] == (
        "Rupees Twelve Thousand Three Hundred Forty-Five Only\n"
    )
    assert run(capsys, "words", "12345", "--lang", "ta")[1] == (
        "பன்னிரண்டாயிரத்து முந்நூற்று நாற்பத்தைந்து ரூபாய் மட்டும்\n"
    )
    assert run(capsys, "words", "21", "--lang", "ta", "--number", "--spaced")[1] == (
        "இருபத்து ஒன்று\n"
    )
    assert run(capsys, "words", "105", "--and", "--upper", "--no-only")[1] == (
        "RUPEES ONE HUNDRED AND FIVE\n"
    )


def test_gstin(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "gstin", "check", "29AAACB1234C1ZB")
    assert code == 0
    assert "Karnataka" in out
    code, out, _ = run(capsys, "gstin", "check", "29AAACB1234C1ZB", "--json")
    payload = json.loads(out)
    assert payload["valid"] is True
    assert payload["state_code"] == "29"
    assert payload["pan_holder_type"] == "Company"
    assert run(capsys, "gstin", "checkdigit", "29AAACB1234C1Z")[1] == "B\n"


def test_gstin_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(capsys, "gstin", "check", "29AAACB1234C1ZC")
    assert code == 1
    assert out == ""
    assert "check digit mismatch" in err
    code, out, _ = run(capsys, "gstin", "check", "29AAACB1234C1ZC", "--json")
    assert code == 1
    assert json.loads(out)["valid"] is False


def test_other_validators(capsys: pytest.CaptureFixture[str]) -> None:
    assert "Individual" in run(capsys, "pan", "check", "ABCPE1234F")[1]
    assert json.loads(run(capsys, "ifsc", "check", "SBIN0000001", "--json")[1])["bank_code"] == (
        "SBIN"
    )
    code, out, _ = run(capsys, "ifsc", "check", "ZZZZ0000001")
    assert code == 0
    assert re.search(r"bank name +-", out)
    assert "Tamil Nadu" in run(capsys, "pincode", "check", "600001")[1]
    assert run(capsys, "mobile", "normalize", "98765 43210")[1] == "+919876543210\n"
    assert run(capsys, "mobile", "normalize", "12345")[0] == 1


def test_bad_option_value(capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = run(capsys, "format", "10", "--decimals", "-1")
    assert code == 1
    assert "decimals" in err


def test_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main(["nonsense"])
    assert info.value.code == 2
    capsys.readouterr()


def test_python_dash_m() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "india_utils", "words", "100000", "--lang", "ta", "--number"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert result.stdout == "ஒரு லட்சம்\n"


def test_module_entry_point(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["india-utils", "mobile", "normalize", "9876543210"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("india_utils", run_name="__main__")
    assert info.value.code == 0
    assert capsys.readouterr().out == "+919876543210\n"
