"""Separate Balance smoke-test command. Live path always gated in this release."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bot1.adapters.binance.balance import BalanceContext
from bot1.adapters.binance.contracts import UnsupportedContract
from bot1.adapters.binance.smoke import SyntheticReply, SmokeError, inspect_sdk_snapshot, require_live_smoke, MAX_RESPONSE_BYTES
from bot1.adapters.binance.trial import balance_trial_plan


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes rejected args; those could contain a secret.
        print(json.dumps({"status": "BLOCKED", "error": "SMOKE_ARGUMENTS_INVALID"}), file=sys.stderr)
        raise SystemExit(2)


def main(argv=None) -> int:
    parser = SafeParser(description="Offline preparation only; live Binance queries remain disabled.", allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--offline-fixture", type=Path)
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-readonly", action="store_true", help="Required operator action for a future live query; does not bypass review gates")
    parser.add_argument("--key-type", choices=("HMAC", "RSA", "ED25519"))
    parser.add_argument("--account")
    parser.add_argument("--expected-account-alias")
    parser.add_argument("--poll-id")
    parser.add_argument("--received-time")
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        if args.plan:
            print(json.dumps({**balance_trial_plan("data/experiments/balance-snapshot-only.sqlite"),
                              "smoke_test_live_status": "NOT VERIFIED", "max_attempts": 1,
                              "official_vendor_docs_present_at_review": False,
                              "signing": "SDK_ONLY HMAC offline candidate; actual key type and API-doc review pending"}, indent=2))
            return 0
        if args.live:
            # BEFORE credential access, network construction, signing or writes.
            require_live_smoke(args.confirm_readonly, args.key_type)
            return 2
        if any(x is None for x in (args.account, args.expected_account_alias, args.poll_id, args.received_time)):
            raise SmokeError("SMOKE_OFFLINE_CONTEXT_REQUIRED")
        context = BalanceContext(args.account, args.expected_account_alias, args.poll_id, args.received_time)
        with args.offline_fixture.open("rb") as handle:
            raw = handle.read(MAX_RESPONSE_BYTES + 1)
        result = inspect_sdk_snapshot(SyntheticReply(200, raw), context, timeout_ms=args.timeout_ms)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError) as exc:
        code = "SMOKE_SCHEMA_OR_CONTEXT_REJECTED"
        if isinstance(exc, UnsupportedContract):
            code = "BINANCE_CONTRACT_NOT_VERIFIED"
        elif isinstance(exc, OSError):
            code = "SMOKE_LOCAL_FIXTURE_IO"
        elif isinstance(exc, SmokeError) and str(exc) in {
                "SMOKE_OPERATOR_CONFIRMATION_REQUIRED", "SMOKE_KEY_TYPE_NOT_REVIEWED",
                "SMOKE_OFFLINE_CONTEXT_REQUIRED", "SMOKE_TIMEOUT_CONFIG",
                "SMOKE_RESPONSE_TOO_LARGE", "SMOKE_INCOMPLETE_OBSERVATION"}:
            code = str(exc)
        # Whitelisted codes only. Never echo arbitrary filesystem/parser inputs.
        print(json.dumps({"status": "BLOCKED", "error": code,
                          "official_api_docs_verified": False,
                          "action": "inspect local documentation and input; do not increase API permissions"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
