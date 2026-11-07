from decimal import Decimal, localcontext, Inexact, Rounded, Overflow, Underflow, DivisionByZero, FloatOperation
from fractions import Fraction
import random
import unittest

from bot1.core import numeric as n


class NumericTests(unittest.TestCase):
    def test_precision_regression(self):
        self.assertEqual(n.total([n.parse("1234567890123456789012345678.90"), n.parse("0.01")]).value,
                         Decimal("1234567890123456789012345678.91"))

    def test_ambient_context_isolation(self):
        with localcontext() as ambient:
            ambient.prec = 3
            value = n.total([n.parse("12345.67"), n.parse("0.01")]).value
            self.assertEqual(value, Decimal("12345.68"))
            self.assertEqual(n.serialize(value), "12345.68")
            self.assertEqual(ambient.prec, 3)

    def test_context_config(self):
        c = n.context()
        self.assertEqual((c.prec, c.Emin, c.Emax, c.clamp), (128, -999, 999, 0))
        self.assertTrue(all(c.traps[s] for s in n.SIGNALS))

    def test_exact_division_and_zero(self):
        with self.assertRaises(Inexact): n.divide_exact("1", "3")
        with self.assertRaises(DivisionByZero): n.divide_exact("1", "0")
        self.assertEqual(n.divide_exact("1", "8"), Decimal("0.125"))

    def test_overflow_underflow_rounded_float_traps(self):
        with localcontext(n.context()):
            with self.assertRaises(Overflow): Decimal("1e999") * Decimal(10)
            with self.assertRaises(Underflow): Decimal("1e-999") / Decimal(3)
            with self.assertRaises(Rounded): Decimal("1" + "0" * 128) + Decimal(0)
            with self.assertRaises(FloatOperation): Decimal(0.1)  # Negative test only.

    def test_tiny_sum(self):
        self.assertEqual(n.total(n.parse("1e-18") for _ in range(10000)).value, Decimal("1e-14"))

    def test_aggregate_limit_and_round_trip(self):
        x = n.parse("999999999999999999999999999999.999999999999999999")
        with localcontext(n.context()): value = x * Decimal(n.MAX_TERMS)
        aggregate = n.Aggregate(value, n.MAX_TERMS)
        self.assertEqual(n.deserialize_aggregate(n.serialize(value), n.MAX_TERMS), aggregate)
        with self.assertRaises(n.NumericError): aggregate.add(n.Aggregate(x, 1))
        self.assertEqual(n.Aggregate(Decimal(5), 7).add(n.Aggregate(Decimal(-5), 9)).terms, 16)
        self.assertEqual(Fraction(value), Fraction(x) * n.MAX_TERMS)

    def test_product_96_digits(self):
        x = "999999999999999999999999999999.999999999999999999"
        value = n.multiply(x, x)
        self.assertEqual(len(value.as_tuple().digits), 96)
        self.assertEqual(Fraction(value), Fraction(x) ** 2)

    def test_difference_retains_leaf_count_and_budget(self):
        result = n.difference(n.Aggregate(Decimal(10), 2), n.Aggregate(Decimal(8), 3))
        self.assertEqual((result.value, result.terms), (Decimal(2), 5))
        with self.assertRaises(n.NumericError):
            n.difference(n.Aggregate(Decimal(1), n.MAX_TERMS), n.Aggregate(Decimal(1), 1))

    def test_ratio_ties_and_metadata(self):
        self.assertEqual(n.ratio("1", "3", 8).value, Decimal("0.33333333"))
        self.assertTrue(n.ratio("1", "3", 8).was_rounded)
        self.assertFalse(n.ratio("1", "8", 3).was_rounded)
        for a, expected in [("1", "0.12"), ("3", "0.38"), ("-1", "-0.12")]:
            self.assertEqual(n.ratio(a, "8", 2).value, Decimal(expected))
        self.assertEqual(n.ratio("0.124999999999999999", "1", 2).value, Decimal("0.12"))
        self.assertEqual(n.ratio("0.125000000000000001", "1", 2).value, Decimal("0.13"))
        with self.assertRaises(n.NumericError): n.ratio("1", "0", 8)
        with self.assertRaises(n.NumericError): n.ratio("1", "3", 19)

    def test_ratio_independent_rational_oracle(self):
        rng = random.Random(20261106)
        for _ in range(250):
            a, b, scale = rng.randint(-10**18, 10**18), rng.randint(1, 10**18), rng.randint(0, 18)
            fraction = Fraction(a, b)
            q, rem = divmod(abs(fraction.numerator) * 10**scale, fraction.denominator)
            if 2 * rem > fraction.denominator or (2 * rem == fraction.denominator and q % 2): q += 1
            expected = Fraction(-q if fraction < 0 else q, 10**scale)
            self.assertEqual(Fraction(n.ratio(str(a), str(b), scale).value), expected)

    def test_display_does_not_mutate_ledger(self):
        value = n.parse("1.005")
        shown = n.display(value)
        self.assertEqual(shown.value, Decimal("1.00"))
        self.assertTrue(shown.was_rounded)
        self.assertEqual(value, Decimal("1.005"))


# Each boundary is an individually named unittest case, not imported document checks.
INVALID = [
    *[(s, "NUMERIC_NONFINITE") for s in ["NaN", "sNaN", "Infinity", "-Infinity", "Inf", "-Inf", "+NaN", "nan123", "-sNaN42"]],
    (True, "NUMERIC_TYPE"), (None, "NUMERIC_TYPE"), (1, "NUMERIC_TYPE"), (0.1, "NUMERIC_TYPE"), (Decimal(1), "NUMERIC_TYPE"),
    ("", "NUMERIC_LENGTH"), ("1" * 97, "NUMERIC_LENGTH"), ("1" * 96, "NUMERIC_DIGITS"), ("1" * 49, "NUMERIC_DIGITS"),
    ("0." + "1" * 19, "NUMERIC_SCALE"), ("1.1e-18", "NUMERIC_SCALE"), ("0.0e-18", "NUMERIC_SCALE"),
    ("1e19", "NUMERIC_EXPONENT"), ("1e-19", "NUMERIC_EXPONENT"), ("1e99", "NUMERIC_EXPONENT"),
    ("1" + "0" * 30, "NUMERIC_MAGNITUDE"), ("1_000", "NUMERIC_SYNTAX"), ("１", "NUMERIC_SYNTAX"),
    (".1", "NUMERIC_SYNTAX"), ("1.", "NUMERIC_SYNTAX"), ("01", "NUMERIC_SYNTAX"), ("+1", "NUMERIC_SYNTAX"),
    (" 1", "NUMERIC_SYNTAX"), ("1e01", "NUMERIC_SYNTAX"), ("abc", "NUMERIC_SYNTAX"),
]
for index, (raw, code) in enumerate(INVALID, 1):
    def invalid_test(self, raw=raw, code=code):
        with self.assertRaisesRegex(n.NumericError, code): n.parse(raw)
    setattr(NumericTests, f"test_reject_{index:02}", invalid_test)

VALID = ["0", "-0", "-1.25", "1e-18", "0.000000000000000001", "1e18", "1e+18",
         "999999999999999999999999999999.999999999999999999"]
for index, raw in enumerate(VALID, 1):
    def valid_test(self, raw=raw):
        self.assertEqual(n.parse(n.serialize(n.parse(raw))), Decimal(raw))
    setattr(NumericTests, f"test_valid_roundtrip_{index:02}", valid_test)


class DomainNumberTests(unittest.TestCase):
    def test_negative_zero_and_domains(self):
        for raw in ("-1", "-0"):
            with self.assertRaises(n.NumericError): n.parse(raw, "nonnegative")
        for raw in ("-1", "-0", "0"):
            with self.assertRaises(n.NumericError): n.parse(raw, "positive")
        self.assertEqual(n.parse("0", "nonnegative"), Decimal(0))
        self.assertEqual(n.parse("-8", "signed"), Decimal(-8))

    def test_bad_aggregate_storage(self):
        for raw, count in [("NaN", 1), ("1e3", 1), ("1" + "0" * 39, 1), ("0", -1), ("0", True)]:
            with self.assertRaises(n.NumericError): n.deserialize_aggregate(raw, count)
