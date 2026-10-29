"""Command-line interface: ``india-utils <command> ...``.

Exit status is 0 on success, 1 when the input is invalid and 2 on a usage
error. Pass ``--json`` to the validators for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict
from typing import Any

from . import __version__
from .contact import normalize_mobile, normalize_pincode, pincode_region
from .currency import NegativeStyle, format_inr, format_inr_compact
from .gstin import gstin_check_digit, parse_gstin
from .ifsc import parse_ifsc
from .pan import parse_pan
from .words import Case, TamilStyle, amount_in_words, number_to_words

__all__ = ["build_parser", "main"]


def _emit(fields: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"valid": True, **fields}, ensure_ascii=False))
        return
    width = max(len(key) for key in fields)
    for key, value in fields.items():
        label = key.replace("_", " ")
        print(f"{label:<{width}}  {'-' if value is None else value}")


def _cmd_format(args: argparse.Namespace) -> None:
    if args.compact:
        print(format_inr_compact(args.amount, symbol=args.symbol or "", decimals=args.decimals))
    else:
        symbol = "₹" if args.symbol is None else args.symbol
        negative: NegativeStyle = "parentheses" if args.parentheses else "minus"
        print(
            format_inr(args.amount, symbol=symbol, decimals=args.decimals, negative_style=negative)
        )


def _cmd_words(args: argparse.Namespace) -> None:
    style: TamilStyle = "spaced" if args.spaced else "sandhi"
    if args.number:
        print(number_to_words(args.amount, args.lang, style=style, use_and=args.use_and))
    else:
        case: Case = "upper" if args.upper else "title"
        print(
            amount_in_words(
                args.amount,
                args.lang,
                only=not args.no_only,
                style=style,
                use_and=args.use_and,
                case=case,
            )
        )


def _cmd_gstin(args: argparse.Namespace) -> None:
    if args.action == "checkdigit":
        print(gstin_check_digit(args.value))
        return
    g = parse_gstin(args.value, allow_legacy_state_codes=args.allow_legacy)
    fields = asdict(g)
    fields["pan_holder_type"] = g.pan_holder_type
    _emit(fields, args.json)


def _cmd_pan(args: argparse.Namespace) -> None:
    _emit(asdict(parse_pan(args.value)), args.json)


def _cmd_ifsc(args: argparse.Namespace) -> None:
    _emit(asdict(parse_ifsc(args.value)), args.json)


def _cmd_pincode(args: argparse.Namespace) -> None:
    pin = normalize_pincode(args.value)
    _emit({"value": pin, "region": pincode_region(pin)}, args.json)


def _cmd_mobile(args: argparse.Namespace) -> None:
    print(normalize_mobile(args.value))


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser (exposed for testing and shell completion)."""
    parser = argparse.ArgumentParser(
        prog="india-utils",
        description="Indian number formats and identifier validation.",
        epilog="Use '--' before a negative amount, e.g. india-utils format -- -1500",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    fmt = sub.add_parser("format", help="format an amount with lakh/crore grouping")
    fmt.add_argument("amount")
    fmt.add_argument("--symbol", help="currency symbol (default ₹; none with --compact)")
    fmt.add_argument("--decimals", type=int, default=2, help="decimal places (default 2)")
    fmt.add_argument("--compact", action="store_true", help="abbreviate as K / L / Cr")
    fmt.add_argument("--parentheses", action="store_true", help="show negatives as (₹100.00)")
    fmt.set_defaults(handler=_cmd_format)

    words = sub.add_parser("words", help="write an amount (or number) in words")
    words.add_argument("amount")
    words.add_argument("--lang", choices=("en", "ta"), default="en", help="language (default en)")
    words.add_argument("--number", action="store_true", help="plain number, no Rupees/Only")
    words.add_argument("--spaced", action="store_true", help="Tamil: spaced style, no sandhi")
    words.add_argument("--and", dest="use_and", action="store_true", help="English: 'and'")
    words.add_argument("--no-only", action="store_true", help="omit the trailing 'Only'")
    words.add_argument("--upper", action="store_true", help="English: UPPER CASE")
    words.set_defaults(handler=_cmd_words)

    gstin = sub.add_parser("gstin", help="validate a GSTIN or compute its check digit")
    gstin.add_argument("action", choices=("check", "checkdigit"))
    gstin.add_argument("value")
    gstin.add_argument("--json", action="store_true", help="print JSON")
    gstin.add_argument(
        "--allow-legacy", action="store_true", help="accept legacy state codes 25 and 28"
    )
    gstin.set_defaults(handler=_cmd_gstin)

    simple: list[tuple[str, str, Callable[[argparse.Namespace], None]]] = [
        ("pan", "validate a PAN and show the holder type", _cmd_pan),
        ("ifsc", "validate an IFSC and show the bank code", _cmd_ifsc),
        ("pincode", "validate a PIN code and show its postal region", _cmd_pincode),
    ]
    for name, help_text, handler in simple:
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("action", choices=("check",))
        cmd.add_argument("value")
        cmd.add_argument("--json", action="store_true", help="print JSON")
        cmd.set_defaults(handler=handler)

    mobile = sub.add_parser("mobile", help="normalise a mobile number to +91 E.164")
    mobile.add_argument("action", choices=("normalize",))
    mobile.add_argument("value")
    mobile.set_defaults(handler=_cmd_mobile, json=False)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit status."""
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except ValueError as exc:  # ValidationError, or e.g. a negative --decimals
        if getattr(args, "json", False):
            print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
