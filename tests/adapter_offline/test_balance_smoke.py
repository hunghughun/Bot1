"""SDK-only preparation tests. No claim of official API-doc or live coverage."""
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from decimal import localcontext
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bot1.adapters.binance.balance import BalanceContext, BalanceError, validate_balance
from bot1.adapters.binance.contracts import UnsupportedContract
from bot1.adapters.binance.parsing import RestResponseParser
from bot1.adapters.binance.smoke import (
    CandidateRequest, OfflineSmokeHarness, SmokeError, SyntheticReply,
    inspect_sdk_snapshot, prepare_sdk_hmac_candidate, require_live_smoke,
)
from bot1.core.numeric import NumericError

ROOT = Path(__file__).resolve().parents[2]
RAW = (ROOT / "tests/fixtures/binance_sdk/balance_v3_response.json").read_bytes()
CONTEXT = BalanceContext("offline-test-account", "SgsR", "smoke-001", "2026-11-06T18:00:00Z")


def candidate(**overrides):
    # Entirely synthetic, never a Binance credential or production signature.
    args = dict(api_key="SYNTHETIC_KEY_SENTINEL", secret="offline-test-secret",
                key_type="HMAC", timestamp_ms=1617939110373, recv_window_ms=5000)
    return prepare_sdk_hmac_candidate(**{**args, **overrides})


def reply_mutation(**fields):
    rows = json.loads(RAW)
    rows[0].update(fields)
    return SyntheticReply(200, json.dumps(rows).encode())


class RecordingExchange:
    def __init__(self, reply=None, error=None):
        self.reply = reply or SyntheticReply(200, RAW)
        self.error, self.calls = error, []

    def request(self, request, *, timeout_ms, max_response_bytes):
        self.calls.append((request.method, request.base_url, request.path, timeout_ms, max_response_bytes))
        if self.error:
            raise self.error
        return self.reply


class SmokeSdkPreparationTests(unittest.TestCase):
    def test_hmac_matches_independent_openssl_oracle(self):
        # Oracle computed separately with OpenSSL dgst -sha256 -hmac using
        # public synthetic key offline-test-secret, bytes below, no newline.
        req = candidate()
        self.assertEqual(req.signed_query,
            "recvWindow=5000&timestamp=1617939110373&signature="
            "bc7c7a2feda0443de5b1b5b69c73593f25560025d5e2ebefb6f22450b86fc0c3")
        self.assertEqual(req.headers, {"X-MBX-APIKEY": "SYNTHETIC_KEY_SENTINEL"})

    def test_candidate_has_one_immutable_endpoint(self):
        req = candidate()
        self.assertEqual((req.method, req.base_url, req.path),
                         ("GET", "https://fapi.binance.com", "/fapi/v3/balance"))
        with self.assertRaises(TypeError): CandidateRequest("key", req.signed_query, path="/other")
        for field, value in [("method", "POST"), ("base_url", "https://example.invalid"),
                             ("path", "/fapi/v1/order"), ("path", "/sapi/v1/asset/transfer"),
                             ("path", "/fapi/v3/balance?next=evil")]:
            altered = candidate()
            object.__setattr__(altered, field, value)
            with self.subTest(field=field, value=value), self.assertRaisesRegex(SmokeError, "SMOKE_ROUTE_FORBIDDEN"):
                altered.check()

    def test_unsupported_key_types_have_no_fallback(self):
        for key_type in ("RSA", "ED25519", "UNKNOWN", "hmac", None):
            with self.subTest(key_type=key_type), self.assertRaisesRegex(SmokeError, "SMOKE_KEY_TYPE_NOT_REVIEWED"):
                candidate(key_type=key_type)

    def test_invalid_key_secret_and_header_injection_rejected(self):
        for key in ("", "a\r\nX-Evil: x", " key", "key ", "a" * 257, "🔑", None):
            with self.subTest(key=key), self.assertRaises(SmokeError): candidate(api_key=key)
        for secret in ("", "a\n", "a" * 1025, None):
            with self.subTest(secret=secret), self.assertRaises(SmokeError): candidate(secret=secret)

    def test_repr_never_contains_key_secret_signature_or_body(self):
        req = candidate()
        text = repr(req) + repr(SyntheticReply(200, b'SENSITIVE_BODY_SENTINEL'))
        for sentinel in ("SYNTHETIC_KEY_SENTINEL", "offline-test-secret", req.signed_query, "SENSITIVE_BODY_SENTINEL"):
            self.assertNotIn(sentinel, text)

    def test_timestamp_and_local_recv_window_bounds(self):
        for stamp in (True, 0, -1, "1617939110373", 1.25, 253402300800000):
            with self.subTest(stamp=stamp), self.assertRaises(SmokeError): candidate(timestamp_ms=stamp)
        for window in (True, 0, -1, 5001, 60000, "5000", 5.25):
            with self.subTest(window=window), self.assertRaises(SmokeError): candidate(recv_window_ms=window)
        forged = candidate().signed_query.replace("recvWindow=5000", "recvWindow=9999")
        with self.assertRaises(SmokeError): CandidateRequest("key", forged).check()

    def test_query_cannot_carry_other_endpoint_parameters(self):
        for query in (candidate().signed_query + "&symbol=BTCUSDT", "signature=secret", "recvWindow=1&timestamp=1&signature=" + "A" * 64):
            with self.subTest(query=query), self.assertRaises(SmokeError): CandidateRequest("key", query).check()

    def test_single_attempt_and_timeout_size_propagation(self):
        exchange = RecordingExchange()
        harness = OfflineSmokeHarness(exchange, timeout_ms=4321)
        result = harness.run_once(candidate(), CONTEXT)
        self.assertEqual(exchange.calls, [("GET", "https://fapi.binance.com", "/fapi/v3/balance", 4321, 1048576)])
        self.assertEqual(result["snapshot_count"], 2)
        self.assertEqual(result["financial_postings"], 0)
        with self.assertRaisesRegex(SmokeError, "SMOKE_SINGLE_ATTEMPT_EXHAUSTED"):
            harness.run_once(candidate(), CONTEXT)
        self.assertEqual(len(exchange.calls), 1)

    def test_http_auth_rate_server_redirect_errors_stop_without_retry(self):
        for status, code in [(401, "SMOKE_AUTH_OR_PERMISSION_DENIED"), (403, "SMOKE_AUTH_OR_PERMISSION_DENIED"),
                             (418, "SMOKE_RATE_LIMIT_STOP_NO_RETRY"), (429, "SMOKE_RATE_LIMIT_STOP_NO_RETRY"),
                             (500, "SMOKE_HTTP_STATUS_STOP_NO_RETRY"), (302, "SMOKE_HTTP_STATUS_STOP_NO_RETRY")]:
            exchange = RecordingExchange(SyntheticReply(status, b'{"msg":"SECRET_SENTINEL"}'))
            harness = OfflineSmokeHarness(exchange)
            with self.subTest(status=status), self.assertRaisesRegex(SmokeError, code) as error:
                harness.run_once(candidate(), CONTEXT)
            self.assertNotIn("SECRET_SENTINEL", str(error.exception))
            with self.assertRaises(SmokeError): harness.run_once(candidate(), CONTEXT)
            self.assertEqual(len(exchange.calls), 1)

    def test_exchange_failure_redacted_and_consumes_attempt(self):
        exchange = RecordingExchange(error=RuntimeError("SECRET_SENTINEL signature=secret"))
        harness = OfflineSmokeHarness(exchange)
        with self.assertRaisesRegex(SmokeError, "SMOKE_EXCHANGE_STOP_NO_RETRY") as error:
            harness.run_once(candidate(), CONTEXT)
        self.assertNotIn("SECRET_SENTINEL", str(error.exception))
        with self.assertRaises(SmokeError): harness.run_once(candidate(), CONTEXT)
        self.assertEqual(len(exchange.calls), 1)

    def test_timeout_config_and_synthetic_elapsed_time(self):
        for timeout in (True, 0, -1, 30001, 1.5):
            with self.subTest(timeout=timeout), self.assertRaises(SmokeError): OfflineSmokeHarness(RecordingExchange(), timeout_ms=timeout)
        with self.assertRaisesRegex(SmokeError, "SMOKE_TIMEOUT"):
            inspect_sdk_snapshot(SyntheticReply(200, RAW, elapsed_ms=10000), CONTEXT)
        for elapsed in (-1, True, 0.5):
            with self.subTest(elapsed=elapsed), self.assertRaises(SmokeError): inspect_sdk_snapshot(SyntheticReply(200, RAW, elapsed), CONTEXT)

    def test_invalid_inputs_and_route_rejected_before_exchange(self):
        exchange = RecordingExchange()
        for request, context in [(None, CONTEXT), (candidate(), None)]:
            with self.assertRaises(SmokeError): OfflineSmokeHarness(exchange).run_once(request, context)
        tampered = candidate()
        object.__setattr__(tampered, "path", "/fapi/v1/order")
        with self.assertRaises(SmokeError): OfflineSmokeHarness(exchange).run_once(tampered, CONTEXT)
        self.assertEqual(exchange.calls, [])

    def test_operator_confirmation_cannot_override_doc_gate(self):
        with self.assertRaisesRegex(SmokeError, "SMOKE_OPERATOR_CONFIRMATION_REQUIRED"):
            require_live_smoke(False, "HMAC")
        with self.assertRaisesRegex(SmokeError, "SMOKE_OPERATOR_CONFIRMATION_REQUIRED"):
            require_live_smoke(1, "HMAC")
        with self.assertRaisesRegex(SmokeError, "SMOKE_KEY_TYPE_NOT_REVIEWED"):
            require_live_smoke(True, "RSA")
        with self.assertRaisesRegex(UnsupportedContract, "BINANCE_CONTRACT_NOT_VERIFIED"):
            require_live_smoke(True, "HMAC")


class SmokeFinancialProfileTests(unittest.TestCase):
    def test_all_fields_inspected_but_no_financial_payload_returned(self):
        result = inspect_sdk_snapshot(SyntheticReply(200, RAW), CONTEXT)
        self.assertEqual(result, {"status": "PASS", "scope": "OFFLINE_SDK_PROFILE_ONLY",
            "official_api_docs_verified": False, "network_performed": False,
            "asset_rows_validated": 1, "snapshot_count": 2,
            "financial_postings": 0, "database_writes": 0, "telegram_sends": 0})
        text = json.dumps(result)
        for sentinel in ("SgsR", "122607.35137903", "23.72469206", "offline-test-account"):
            self.assertNotIn(sentinel, text)

    def test_all_five_money_fields_preserve_extreme_precision(self):
        for name in ("balance", "availableBalance", "crossWalletBalance", "crossUnPnl", "maxWithdrawAmount"):
            for value in ("999999999999999999999999999999.123456789012345678", "-1.000000000000000001", "0", "0.000000000000000001"):
                with self.subTest(field=name, value=value), localcontext() as ctx:
                    ctx.prec = 2
                    reply = reply_mutation(**{name: value})
                    self.assertEqual(inspect_sdk_snapshot(reply, CONTEXT)["snapshot_count"], 2)
                    rows = validate_balance(RestResponseParser().parse(reply.body, "futures_balance_v3"), CONTEXT)
                    self.assertEqual(rows[0][name], value)

    def test_all_five_money_fields_reject_nonfinite_and_out_of_bounds(self):
        for name in ("balance", "availableBalance", "crossWalletBalance", "crossUnPnl", "maxWithdrawAmount"):
            for value in ("NaN", "sNaN", "Infinity", "-Infinity", "Inf", "-Inf", "1" * 97, "1e30", "1e-19", "0." + "1" * 19):
                with self.subTest(field=name, value=value), self.assertRaises(NumericError):
                    inspect_sdk_snapshot(reply_mutation(**{name: value}), CONTEXT)

    def test_all_five_money_fields_reject_json_numbers(self):
        for name in ("balance", "availableBalance", "crossWalletBalance", "crossUnPnl", "maxWithdrawAmount"):
            with self.subTest(field=name), self.assertRaises(BalanceError):
                inspect_sdk_snapshot(reply_mutation(**{name: 123}), CONTEXT)

    def test_strict_smoke_requires_all_fields_without_altering_mapper_profile(self):
        for name in ("asset", "accountAlias", "balance", "availableBalance", "crossWalletBalance", "crossUnPnl", "maxWithdrawAmount", "marginAvailable", "updateTime"):
            for null in (True, False):
                rows = json.loads(RAW)
                if null:
                    rows[0][name] = None
                else:
                    del rows[0][name]
                with self.subTest(field=name, null=null), self.assertRaises(ValueError):
                    inspect_sdk_snapshot(SyntheticReply(200, json.dumps(rows).encode()), CONTEXT)

    def test_flag_asset_and_timestamp_types(self):
        for name, value in [("asset", "usdt"), ("asset", True), ("marginAvailable", 1), ("marginAvailable", "true"), ("updateTime", "1617939110373"), ("updateTime", 1617939110373.5)]:
            with self.subTest(field=name), self.assertRaises(ValueError): inspect_sdk_snapshot(reply_mutation(**{name: value}), CONTEXT)
        self.assertEqual(inspect_sdk_snapshot(reply_mutation(marginAvailable=False), CONTEXT)["asset_rows_validated"], 1)

    def test_duplicate_keys_rows_unknown_fields_and_malformed_json(self):
        rows = json.loads(RAW)
        samples = [b'{bad json', b'[]', b'{"asset":"USDT","asset":"USDC"}',
                   json.dumps(rows + rows).encode(), json.dumps({"code": -1}).encode(),
                   json.dumps([{**rows[0], "futureField": "1"}]).encode()]
        for raw in samples:
            with self.subTest(raw=raw), self.assertRaises(ValueError): inspect_sdk_snapshot(SyntheticReply(200, raw), CONTEXT)

    def test_oversize_body_fail_closed(self):
        with self.assertRaisesRegex(SmokeError, "SMOKE_RESPONSE_TOO_LARGE"):
            inspect_sdk_snapshot(SyntheticReply(200, b' ' * 1048577), CONTEXT)

    def test_stateless_fixture_replay_has_no_persistent_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = Path.cwd()
            try:
                os.chdir(tmp)
                first = inspect_sdk_snapshot(SyntheticReply(200, RAW), CONTEXT)
                second = inspect_sdk_snapshot(SyntheticReply(200, RAW), CONTEXT)
                self.assertEqual(first, second)
                self.assertEqual(list(Path(tmp).iterdir()), [])
            finally:
                os.chdir(previous)


class SmokeCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/balance-smoke-test.py"), *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=15)

    def test_plan_is_inert(self):
        result = self.run_cli("--plan")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["max_attempts"], 1)
        self.assertFalse(plan["network_enabled"])
        self.assertFalse(plan["live_readonly_enabled"])
        self.assertEqual(plan["active_allowlist"], [])

    def test_offline_fixture_positive_and_safe_summary(self):
        result = self.run_cli("--offline-fixture", str(ROOT / "tests/fixtures/binance_sdk/balance_v3_response.json"),
                              "--account", CONTEXT.account, "--expected-account-alias", "SgsR", "--poll-id", "smoke-001",
                              "--received-time", "2026-11-06T18:00:00Z")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["scope"], "OFFLINE_SDK_PROFILE_ONLY")
        self.assertNotIn("122607", result.stdout + result.stderr)

    def test_live_without_confirmation_stops(self):
        result = self.run_cli("--live", "--key-type", "HMAC")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["error"], "SMOKE_OPERATOR_CONFIRMATION_REQUIRED")

    def test_live_with_confirmation_still_fails_official_review(self):
        result = self.run_cli("--live", "--key-type", "HMAC", "--confirm-readonly")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["error"], "BINANCE_CONTRACT_NOT_VERIFIED")
        self.assertEqual(result.stdout, "")

    def test_cli_unknown_args_do_not_echo_secret(self):
        for flag in ("--api-key", "--api-secret", "--url", "--db", "--token"):
            result = self.run_cli("--plan", flag, "SECRET_SENTINEL")
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("SECRET_SENTINEL", result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stderr)["error"], "SMOKE_ARGUMENTS_INVALID")

    def test_cli_invalid_paths_context_and_flag_values_are_redacted(self):
        for args in [("--plan", "--timeout-ms", "SECRET_SENTINEL"),
                     ("--live", "--key-type", "SECRET_SENTINEL"),
                     ("--offline-fixture", "SECRET_SENTINEL")]:
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("SECRET_SENTINEL", result.stdout + result.stderr)

    def test_no_credential_provider_or_environment_lookup_on_live_attempt(self):
        spec = importlib.util.spec_from_file_location("smoke_cli_test", ROOT / "scripts/balance-smoke-test.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from unittest.mock import patch
        with patch.dict(os.environ, {"BINANCE_API_KEY": "SECRET_SENTINEL", "BINANCE_API_SECRET": "SECRET_SENTINEL"}), \
             patch.object(os, "getenv", side_effect=AssertionError("credential access")):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(module.main(["--live", "--key-type", "HMAC", "--confirm-readonly"]), 2)
            self.assertNotIn("SECRET_SENTINEL", out.getvalue() + err.getvalue())
