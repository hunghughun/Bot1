"""NUMERIC-1 implementation. All financial operations use isolated exact contexts."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import (Decimal, Context, localcontext, ROUND_HALF_EVEN,
                     InvalidOperation, DivisionByZero, Overflow, Underflow,
                     Subnormal, Clamped, FloatOperation, Inexact, Rounded)
import re
from typing import Iterable

POLICY = "NUMERIC-1"
MAX_TERMS = 1_000_000_000
SIGNALS = (InvalidOperation, DivisionByZero, Overflow, Underflow, Subnormal,
           Clamped, FloatOperation, Inexact, Rounded)
GRAMMAR = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?(?:0|[1-9][0-9]?))?", re.ASCII)


class NumericError(ValueError):
    """Safe code only: never include the input or a signed request."""


def context() -> Context:
    result = Context(prec=128, Emin=-999, Emax=999, rounding=ROUND_HALF_EVEN, clamp=0)
    for signal in SIGNALS:
        result.traps[signal] = True
    result.clear_flags()
    return result


def parse(raw: object, domain: str = "signed") -> Decimal:
    if type(raw) is not str:
        raise NumericError("NUMERIC_TYPE")
    if not 1 <= len(raw) <= 96:
        raise NumericError("NUMERIC_LENGTH")
    if not raw.isascii():
        raise NumericError("NUMERIC_SYNTAX")
    if re.fullmatch(r"[+-]?(?:s?nan[0-9]*|inf(?:inity)?)", raw, re.I):
        raise NumericError("NUMERIC_NONFINITE")
    if GRAMMAR.fullmatch(raw) is None:
        raise NumericError("NUMERIC_SYNTAX")
    parts = re.split("[eE]", raw)
    mantissa = parts[0].lstrip("-")
    if len(mantissa.replace(".", "")) > 48:
        raise NumericError("NUMERIC_DIGITS")
    if "." in mantissa and len(mantissa.split(".")[1]) > 18:
        raise NumericError("NUMERIC_SCALE")
    if len(parts) == 2 and abs(int(parts[1])) > 18:
        raise NumericError("NUMERIC_EXPONENT")
    value = Decimal(raw)
    if not value.is_finite():
        raise NumericError("NUMERIC_NONFINITE")
    if not -18 <= value.as_tuple().exponent <= 18:
        raise NumericError("NUMERIC_SCALE")
    if value.copy_abs() >= Decimal("1e30"):
        raise NumericError("NUMERIC_MAGNITUDE")
    if domain not in ("signed", "nonnegative", "positive"):
        raise NumericError("NUMERIC_DOMAIN")
    if domain == "nonnegative" and value.is_signed():
        raise NumericError("NUMERIC_DOMAIN")
    if domain == "positive" and value <= 0:
        raise NumericError("NUMERIC_DOMAIN")
    return Decimal(0) if value.is_zero() else value


def serialize(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise NumericError("NUMERIC_TYPE_OR_NONFINITE")
    # No normalize(): it would use the caller's ambient context and could round.
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return "0" if value.is_zero() else result


@dataclass(frozen=True)
class Aggregate:
    value: Decimal
    terms: int

    def __post_init__(self) -> None:
        if type(self.terms) is not int or not 0 <= self.terms <= MAX_TERMS:
            raise NumericError("ACCUMULATION_LIMIT")
        if (type(self.value) is not Decimal or not self.value.is_finite()
                or self.value.copy_abs() >= Decimal("1e39")
                or not -18 <= self.value.as_tuple().exponent <= 38
                or (self.terms == 0 and self.value != 0)):
            raise NumericError("NUMERIC_AGGREGATE")

    def add(self, other: Aggregate) -> Aggregate:
        if self.terms + other.terms > MAX_TERMS:
            raise NumericError("ACCUMULATION_LIMIT")
        with localcontext(context()):
            return Aggregate(self.value + other.value, self.terms + other.terms)


def total(values: Iterable[Decimal]) -> Aggregate:
    result = Aggregate(Decimal(0), 0)
    for value in values:
        result = result.add(Aggregate(value, 1))
    return result


def deserialize_aggregate(raw: str, terms: int) -> Aggregate:
    if type(raw) is not str or len(raw) > 96 or re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,18})?", raw, re.ASCII) is None:
        raise NumericError("NUMERIC_AGGREGATE")
    if len(raw.lstrip("-").replace(".", "")) > 57:
        raise NumericError("NUMERIC_AGGREGATE")
    return Aggregate(Decimal(raw), terms)


def difference(left: Aggregate, right: Aggregate) -> Aggregate:
    return left.add(Aggregate(right.value.copy_negate(), right.terms))


def multiply(left: str, right: str) -> Decimal:
    with localcontext(context()):
        return parse(left) * parse(right)


def divide_exact(left: str, right: str) -> Decimal:
    with localcontext(context()):
        return parse(left) / parse(right)


@dataclass(frozen=True)
class RoundedValue:
    value: Decimal
    was_rounded: bool
    scale: int
    mode: str = ROUND_HALF_EVEN


def ratio(numerator: str, denominator: str, scale: int) -> RoundedValue:
    if type(scale) is not int or not 0 <= scale <= 18:
        raise NumericError("NUMERIC_SCALE")
    n, d = parse(numerator), parse(denominator)
    if d.is_zero():
        raise NumericError("NUMERIC_DIV_ZERO")
    with localcontext(context()):
        nc = Decimal("".join(map(str, n.as_tuple().digits)))
        dc = Decimal("".join(map(str, d.as_tuple().digits)))
        power = n.as_tuple().exponent - d.as_tuple().exponent + scale
        q, r = divmod(nc * Decimal(10) ** max(0, power), dc * Decimal(10) ** max(0, -power))
        base = dc * Decimal(10) ** max(0, -power)
        if r * 2 > base or (r * 2 == base and q % 2 == 1):
            q += 1
        if n.is_signed() != d.is_signed():
            q = q.copy_negate()
        return RoundedValue(q.scaleb(-scale), r != 0, scale)


def display(value: Decimal, scale: int = 2) -> RoundedValue:
    if type(scale) is not int or not 0 <= scale <= 18 or not value.is_finite():
        raise NumericError("NUMERIC_SCALE_OR_NONFINITE")
    ctx = context()
    ctx.traps[Inexact] = ctx.traps[Rounded] = False
    with localcontext(ctx) as active:
        shown = value.quantize(Decimal(1).scaleb(-scale))
        return RoundedValue(shown, active.flags[Inexact], scale)
