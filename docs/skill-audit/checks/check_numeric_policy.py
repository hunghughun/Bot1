#!/usr/bin/env python3
"""Offline specification checker for NUMERIC-1; NOT a Bot 1 module.

Synthetic inputs only. No network, credentials, persistence or event processor.
Reference model is checked against literal answers and Fraction integer oracles.
Run: python3 docs/skill-audit/checks/check_numeric_policy.py --output <json>
"""

import argparse
from decimal import (
    Decimal, Context, localcontext, ROUND_HALF_EVEN, InvalidOperation,
    DivisionByZero, Overflow, Underflow, Subnormal, Clamped, FloatOperation,
    Inexact, Rounded,
)
from fractions import Fraction
import json
from pathlib import Path
import random
import re

LIMIT = 10**9
SIGNALS = (InvalidOperation, DivisionByZero, Overflow, Underflow, Subnormal,
           Clamped, FloatOperation, Inexact, Rounded)
PATTERN = re.compile(
    r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?(?:0|[1-9][0-9]?))?",
    re.ASCII,
)


class PolicyError(ValueError):
    pass


def exact_context():
    ctx = Context(prec=128, Emin=-999, Emax=999,
                  rounding=ROUND_HALF_EVEN, clamp=0)
    for signal in SIGNALS:
        ctx.traps[signal] = True
    ctx.clear_flags()
    return ctx


def primitive(raw, domain="signed"):
    """Independent reference model, not a production ingestion adapter."""
    if type(raw) is not str:
        raise PolicyError("NUMERIC_TYPE")
    if not 1 <= len(raw) <= 96:
        raise PolicyError("NUMERIC_LENGTH")
    if not raw.isascii():
        raise PolicyError("NUMERIC_SYNTAX")
    if re.fullmatch(r"[+-]?(?:s?nan[0-9]*|inf(?:inity)?)", raw, re.I):
        raise PolicyError("NUMERIC_NONFINITE")
    if not PATTERN.fullmatch(raw):
        raise PolicyError("NUMERIC_SYNTAX")
    parts = re.split("[eE]", raw)
    coefficient = parts[0].lstrip("-")
    exponent = int(parts[1]) if len(parts) == 2 else 0
    if len(coefficient.replace(".", "")) > 48:
        raise PolicyError("NUMERIC_DIGITS")
    fractional = len(coefficient.split(".")[1]) if "." in coefficient else 0
    if fractional > 18:
        raise PolicyError("NUMERIC_SCALE")
    if abs(exponent) > 18:
        raise PolicyError("NUMERIC_EXPONENT")
    value = Decimal(raw)
    if not value.is_finite():
        raise PolicyError("NUMERIC_NONFINITE")
    if not -18 <= value.as_tuple().exponent <= 18:
        raise PolicyError("NUMERIC_SCALE")
    if value.copy_abs() >= Decimal("1e30"):
        raise PolicyError("NUMERIC_MAGNITUDE")
    if domain == "nonnegative":
        if value.is_signed():
            raise PolicyError("NUMERIC_DOMAIN")
    elif domain == "positive":
        if value <= 0:
            raise PolicyError("NUMERIC_DOMAIN")
    elif domain != "signed":
        raise PolicyError("NUMERIC_DOMAIN")
    return Decimal(0) if value.is_zero() else value


def sum_model(raw_values):
    if len(raw_values) > LIMIT:
        raise PolicyError("ACCUMULATION_LIMIT")
    with localcontext(exact_context()):
        return sum((primitive(s) for s in raw_values), Decimal(0))


def aggregate_model(left, left_count, right, right_count):
    """Counts include every leaf even when terms cancel; prevalidated values."""
    if not (type(left_count) is int and type(right_count) is int
            and 1 <= left_count <= LIMIT and 1 <= right_count <= LIMIT
            and left_count + right_count <= LIMIT):
        raise PolicyError("ACCUMULATION_LIMIT")
    with localcontext(exact_context()):
        value = left + right
        if (not value.is_finite() or value.copy_abs() >= Decimal("1e39")
                or value.as_tuple().exponent < -18):
            raise PolicyError("NUMERIC_MAGNITUDE")
        return value, left_count + right_count


def product_model(a, b):
    with localcontext(exact_context()):
        return primitive(a) * primitive(b)


def coefficient(value):
    # Exact Decimal coefficient; no float or integer money conversions.
    return Decimal("".join(str(x) for x in value.as_tuple().digits))


def ratio_model(numerator, denominator, scale):
    if type(scale) is not int or not 0 <= scale <= 18:
        raise PolicyError("NUMERIC_SCALE")
    n, d = primitive(numerator), primitive(denominator)
    if d.is_zero():
        raise PolicyError("NUMERIC_DIV_ZERO")
    with localcontext(exact_context()):
        en, ed = n.as_tuple().exponent, d.as_tuple().exponent
        k = en - ed + scale
        a = coefficient(n) * Decimal(10) ** max(k, 0)
        b = coefficient(d) * Decimal(10) ** max(-k, 0)
        q, r = divmod(a, b)
        if 2 * r > b or (2 * r == b and q % 2 == 1):
            q += 1
        if n.is_signed() != d.is_signed():
            q = q.copy_negate()
        return q.scaleb(-scale), not r.is_zero()


def rational_oracle(n, d, scale):
    """Independent integer rational oracle, only for checking the spec model."""
    value = Fraction(n) / Fraction(d)
    negative = value < 0
    value = abs(value) * 10**scale
    q, r = divmod(value.numerator, value.denominator)
    if 2 * r > value.denominator or (2 * r == value.denominator and q % 2):
        q += 1
    expected = Fraction(-q if negative else q, 10**scale)
    return expected, r != 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []

    def case(name, action):
        try:
            action()
        except Exception as exc:
            rows.append({"id": name, "status": "FAIL", "error": repr(exc)})
        else:
            rows.append({"id": name, "status": "PASS"})

    def equal(actual, expected):
        if actual != expected:
            raise AssertionError(f"{actual!r} != {expected!r}")

    def rejects(action, error_type, code=None):
        try:
            action()
        except error_type as exc:
            if code is not None:
                equal(str(exc), code)
        else:
            raise AssertionError(f"Did not reject as {error_type.__name__}: {code}")

    # F01: all requested tokens and case/sign/payload variants.
    tokens = ["NaN", "sNaN", "Infinity", "-Infinity", "Inf", "-Inf",
              "+Infinity", "+Inf", "-NaN", "+sNaN", "nan", "SNAN",
              "infinity", "NaN123", "-sNaN42"]
    for i, token in enumerate(tokens, 1):
        case(f"NF-{i:02}", lambda t=token: rejects(
            lambda: primitive(t), PolicyError, "NUMERIC_NONFINITE"))

    invalid = [
        (True, "NUMERIC_TYPE"), (1, "NUMERIC_TYPE"),
        (float("0.1"), "NUMERIC_TYPE"), (None, "NUMERIC_TYPE"),
        (Decimal("1"), "NUMERIC_TYPE"), ("", "NUMERIC_LENGTH"),
        ("1" * 97, "NUMERIC_LENGTH"), ("1" * 49, "NUMERIC_DIGITS"),
        ("0." + "1" * 19, "NUMERIC_SCALE"), ("1e19", "NUMERIC_EXPONENT"),
        ("1e-19", "NUMERIC_EXPONENT"), ("1e99", "NUMERIC_EXPONENT"),
        ("1e99999999999999999999999999999", "NUMERIC_SYNTAX"),
        ("1.1e-18", "NUMERIC_SCALE"), ("0.0e-18", "NUMERIC_SCALE"),
        ("1000000000000000000000000000000", "NUMERIC_MAGNITUDE"),
        ("999999999999999999999999999999e1", "NUMERIC_MAGNITUDE"),
        (" 1", "NUMERIC_SYNTAX"), ("1 ", "NUMERIC_SYNTAX"),
        ("+1", "NUMERIC_SYNTAX"), ("01", "NUMERIC_SYNTAX"),
        ("1e01", "NUMERIC_SYNTAX"), (".1", "NUMERIC_SYNTAX"),
        ("1.", "NUMERIC_SYNTAX"), ("1_000", "NUMERIC_SYNTAX"),
        ("1,000", "NUMERIC_SYNTAX"), ("１２", "NUMERIC_SYNTAX"),
        ("abc", "NUMERIC_SYNTAX"),
    ]
    for i, (raw, code) in enumerate(invalid, 1):
        case(f"BOUND-{i:02}", lambda r=raw, c=code: rejects(
            lambda: primitive(r), PolicyError, c))

    valid = ["0", "-0", "-1.25", "0.000000000000000001", "1e-18",
             "1e18", "1e+18", "999999999999999999999999999999.999999999999999999",
             "999999999999999999999999999999999999999999999999e-18"]
    for i, raw in enumerate(valid, 1):
        case(f"VALID-{i:02}", lambda r=raw: equal(primitive(r), Decimal(r)))
    for raw in ["-1", "-0"]:
        case(f"DOMAIN-NONNEG-{raw}", lambda r=raw: rejects(
            lambda: primitive(r, "nonnegative"), PolicyError, "NUMERIC_DOMAIN"))
    for raw in ["-1", "0", "-0"]:
        case(f"DOMAIN-POS-{raw}", lambda r=raw: rejects(
            lambda: primitive(r, "positive"), PolicyError, "NUMERIC_DOMAIN"))
    case("DOMAIN-ZERO-SNAPSHOT", lambda: equal(primitive("0", "nonnegative"), Decimal(0)))
    case("DOMAIN-NEG-PNL", lambda: equal(primitive("-0.5", "signed"), Decimal("-0.5")))

    def context_check():
        ctx = exact_context()
        equal((ctx.prec, ctx.Emin, ctx.Emax, ctx.clamp, ctx.rounding),
              (128, -999, 999, 0, ROUND_HALF_EVEN))
        for signal in SIGNALS:
            equal(ctx.traps[signal], True)
        equal(any(ctx.flags.values()), False)
    case("CTX-CONFIG", context_check)

    def exact_divide(a, b):
        with localcontext(exact_context()):
            return Decimal(a) / Decimal(b)
    case("CTX-INEXACT", lambda: rejects(lambda: exact_divide("1", "3"), Inexact))
    case("CTX-DIVZERO", lambda: rejects(lambda: exact_divide("1", "0"), DivisionByZero))

    def rounded_loss():
        with localcontext(exact_context()):
            return Decimal("1" + "0" * 128) + Decimal(0)
    case("CTX-ROUNDED", lambda: rejects(rounded_loss, Rounded))

    def overflow():
        with localcontext(exact_context()):
            return Decimal("1e999") * Decimal(10)
    case("CTX-OVERFLOW", lambda: rejects(overflow, Overflow))
    case("CTX-UNDERFLOW", lambda: rejects(lambda: exact_divide("1e-999", "3"), Underflow))

    def float_trap():
        with localcontext(exact_context()):
            return Decimal(float("0.1"))  # Deliberate negative test only.
    case("CTX-FLOAT-TRAP", lambda: rejects(float_trap, FloatOperation))

    case("F02-REGRESSION", lambda: equal(sum_model([
        "1234567890123456789012345678.90", "0.01"]),
        Decimal("1234567890123456789012345678.91")))
    case("SUM-TENTHS", lambda: equal(sum_model(["0.1", "0.2"]), Decimal("0.3")))
    case("SUM-TINY", lambda: equal(sum_model(["1e-18"] * 10000), Decimal("1e-14")))
    largest = "999999999999999999999999999999.999999999999999999"

    def product_bound():
        actual = product_model(largest, largest)
        equal(Fraction(actual), Fraction(largest) ** 2)
        equal(len(actual.as_tuple().digits), 96)
    case("PRODUCT-MAX-96-DIGITS", product_bound)

    def sum_bound():
        with localcontext(exact_context()):
            x = primitive(largest)
            # Mathematical boundary oracle; does NOT replay one billion events.
            total = x * Decimal(LIMIT)
            equal(Fraction(total), Fraction(largest) * LIMIT)
            left, right = x * Decimal(LIMIT - 1), x
            actual, count = aggregate_model(left, LIMIT - 1, right, 1)
            equal(actual, total)
            equal(count, LIMIT)
            rejects(lambda: aggregate_model(actual, count, x, 1),
                    PolicyError, "ACCUMULATION_LIMIT")
    case("AGGREGATE-MAX-N-BOUND", sum_bound)
    case("AGGREGATE-CANCEL-COUNT", lambda: equal(
        aggregate_model(Decimal("5"), 7, Decimal("-5"), 9), (Decimal(0), 16)))

    ratios = [("1", "3", 8), ("1", "8", 3), ("1", "8", 2),
              ("3", "8", 2), ("-1", "8", 2), ("1", "-8", 2),
              ("0", "7", 18), ("1e-18", largest, 18),
              (largest, "1e-18", 18),
              ("0.124999999999999999", "1", 2),
              ("0.125000000000000001", "1", 2)]
    def compare_ratio(n, d, s):
        actual, rounded = ratio_model(n, d, s)
        expected, expected_rounded = rational_oracle(n, d, s)
        equal(Fraction(actual), expected)
        equal(rounded, expected_rounded)
    for i, args_ in enumerate(ratios, 1):
        case(f"RATIO-{i:02}", lambda a=args_: compare_ratio(*a))
    case("RATIO-ZERO-DENOM", lambda: rejects(
        lambda: ratio_model("1", "0", 8), PolicyError, "NUMERIC_DIV_ZERO"))
    for scale in [-1, 19, True]:
        case(f"RATIO-SCALE-{scale}", lambda s=scale: rejects(
            lambda: ratio_model("1", "3", s), PolicyError, "NUMERIC_SCALE"))

    def display_only():
        original = primitive("1.005")
        ctx = exact_context()
        ctx.traps[Inexact] = ctx.traps[Rounded] = False
        with localcontext(ctx) as local:
            shown = original.quantize(Decimal("0.01"))
            equal(shown, Decimal("1.00"))
            equal(local.flags[Inexact], True)
            equal(local.flags[Rounded], True)
        equal(original, Decimal("1.005"))
        equal(exact_context().traps[Inexact], True)
    case("DISPLAY-NO-LEDGER-MUTATION", display_only)

    fixture_math = [
        ("S01-DEPOSIT-ARITHMETIC", ["0", "100"], "100"),
        ("S02-WITHDRAW-FEE-ARITHMETIC", ["100", "-20", "-1"], "79"),
        ("S03-SPOT-ARITHMETIC", ["0", "100", "-100"], "0"),
        ("S03-FUTURES-ARITHMETIC", ["0", "100"], "100"),
        ("S03-EXTERNAL-CAPITAL-ORACLE", ["100"], "100"),
        ("S04-FUTURES-ARITHMETIC", ["100", "-30"], "70"),
        ("S04-SPOT-ARITHMETIC", ["0", "30", "-10"], "20"),
        ("S04-FUNDING-ARITHMETIC", ["0", "10"], "10"),
        ("S05-WALLET-DELTA-ORACLE", ["100", "-100"], "0"),
        ("S06-FILL-QUANTITY-ORACLE", ["0.4", "0.6"], "1.0"),
        ("S06-CLOSE-PARTIAL-ORACLE", ["1", "-0.2"], "0.8"),
        ("S07-PNL-FEES-ARITHMETIC", ["100", "8", "-1", "-0.5"], "106.5"),
    ]
    for name, terms, expected in fixture_math:
        case(name, lambda t=terms, e=expected: equal(sum_model(t), Decimal(e)))

    def generated_oracles():
        rng = random.Random(20261106)
        for _ in range(250):
            a, b = rng.randint(-10**18, 10**18), rng.randint(1, 10**18)
            # Integers here generate synthetic strings / independent oracles only.
            n, d = f"{a}e-18", f"{b}e-18"
            compare_ratio(n, d, rng.randint(0, 18))
            equal(Fraction(sum_model([n, d])), Fraction(n) + Fraction(d))
    case("GENERATED-250-RATIO-SUM-PAIRS", generated_oracles)

    result = {
        "policy": "NUMERIC-1", "scope": "independent specification model only; not Bot 1",
        "data": "synthetic only", "network_calls": 0,
        "passed": sum(x["status"] == "PASS" for x in rows),
        "failed": sum(x["status"] == "FAIL" for x in rows),
        "cases": rows, "generated_pairs_in_one_case": 250,
        "billion_event_replay_executed": False,
        "runtime_dedup_margin_recovery_telegram": "NOT TESTED",
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(f"NUMERIC-1 spec checker: {result['passed']} PASS, {result['failed']} FAIL; NOT Bot 1")
    for row in rows:
        if row["status"] == "FAIL":
            print(row)
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
