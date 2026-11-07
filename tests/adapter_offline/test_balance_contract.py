"""Offline contracts against a pinned OFFICIAL SDK mock, not live API results.

Mutations and multi-asset rows are synthetic test inputs, never API fixtures.
"""
import ast
from dataclasses import replace
from decimal import localcontext
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from bot1.adapters.binance.balance import BalanceContext, BalanceError, map_balance
from bot1.adapters.binance.contracts import UnsupportedContract, require_verified
from bot1.adapters.binance.correlation import BinanceEventCorrelation
from bot1.adapters.binance.mapper import AccountEventMapper
from bot1.adapters.binance.parsing import RestResponseParser
from bot1.adapters.binance.safety import AdapterConfig, EndpointAllowlist, LiveModeDisabled
from bot1.adapters.binance.snapshot_store import SnapshotSandbox
from bot1.adapters.binance.trial import balance_trial_plan
from bot1.adapters.binance.websocket import WebSocketEventParser
from bot1.core.numeric import NumericError
from bot1.database.store import Store
from bot1.domain.events import Event
from bot1.ledger.engine import Engine

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/binance_sdk"
EVIDENCE = ROOT / "docs/api-evidence/f75b4a52c5ae"
RAW = (FIXTURES / "balance_v3_response.json").read_bytes()
CONTEXT = BalanceContext("offline-test-account", "SgsR", "poll-001", "2026-11-06T18:00:00+00:00")


def frame(raw=RAW, contract="futures_balance_v3"):
    return RestResponseParser().parse(raw, contract)


def mutation(**fields):
    rows = json.loads(RAW)
    rows[0].update(fields)
    return json.dumps(rows).encode()


class BalancePositiveContractTests(unittest.TestCase):
    def test_sdk_golden_values_and_internal_schema(self):
        events = AccountEventMapper().map(frame(), context=CONTEXT)
        self.assertEqual(len(events), 2)
        self.assertEqual([(e["metadata"]["metric"], e["amount"]) for e in events],
                         [("wallet", "122607.35137903"), ("available", "23.72469206")])
        for event in events:
            validated = Event.from_dict(event)
            self.assertEqual(validated.wallet, "FUTURES")
            self.assertEqual(validated.asset, "USDT")
            self.assertEqual(validated.event_type, "BALANCE_SNAPSHOT")
            # Independently checked: GNU date -u -d @1617939110.373.
            self.assertEqual(validated.event_time, "2021-04-09T03:31:50.373000+00:00")
            self.assertNotIn("opening", validated.metadata)
            self.assertNotIn("economic_id", validated.metadata)

    def test_golden_provenance_and_source_literal(self):
        meta = json.loads((FIXTURES / "balance_v3_metadata.json").read_text())
        self.assertEqual(hashlib.sha256(RAW).hexdigest(), meta["fixture_sha256"])
        self.assertFalse(meta["is_official_api_example"])
        self.assertFalse(meta["is_real_account_data"])
        source = ROOT / meta["source"]["retained_file"]
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), meta["source"]["retained_sha256"])
        tree = ast.parse(source.read_text())
        expected = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "expected_response" for t in n.targets))
        self.assertEqual(ast.literal_eval(expected), json.loads(RAW))

    def test_all_retained_evidence_hashes_match(self):
        manifest = json.loads((EVIDENCE / "source-manifest.json").read_text())
        self.assertEqual(manifest["commit"], "f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179")
        self.assertFalse(manifest["api_docs_crosschecked"])
        self.assertFalse(manifest["sdk_executed_or_installed"])
        for item in manifest["files"]:
            self.assertEqual(hashlib.sha256((ROOT / item["retained_file"]).read_bytes()).hexdigest(), item["retained_sha256"])

    def test_profile_matches_sdk_array_inheritance_and_field_types(self):
        text = (EVIDENCE / "model-futures_account_balance_v3_response.txt").read_text()
        tree = ast.parse(text)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        self.assertEqual(ast.unparse(klass.bases[0]), "FuturesAccountBalanceV2ResponseInner")
        is_array = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "is_array")
        self.assertIs(is_array.body[-1].value.value, True)
        models = json.loads((EVIDENCE / "model-fields.json").read_text())
        fields = next(m["fields"] for m in models if m["path"].endswith("/futures_account_balance_v2_response_inner.py"))
        by_alias = {f["alias"]: f for f in fields}
        for name in ("balance", "availableBalance", "crossUnPnl", "crossWalletBalance", "maxWithdrawAmount"):
            self.assertEqual(by_alias[name]["type"], "Optional[StrictStr]")
        self.assertEqual(by_alias["updateTime"]["type"], "Optional[StrictInt]")

    def test_local_observation_identity_is_stable_and_amount_independent(self):
        original = map_balance(frame(), CONTEXT)
        changed = map_balance(frame(mutation(balance="1")), CONTEXT)
        self.assertEqual([e["source_event_id"] for e in original], [e["source_event_id"] for e in changed])
        self.assertNotEqual(Event.from_dict(original[0]).financial_hash, Event.from_dict(changed[0]).financial_hash)
        self.assertTrue(original[0]["source_event_id"].startswith("balance-observation:"))
        self.assertIn(frame().sha256, original[0]["evidence"])

    def test_new_poll_and_metrics_have_distinct_observation_ids(self):
        first = map_balance(frame(), CONTEXT)
        second = map_balance(frame(), replace(CONTEXT, poll_id="poll-002"))
        self.assertEqual(len({e["source_event_id"] for e in first + second}), 4)

    def test_negative_zero_and_tiny_signed_money(self):
        for value, expected in [("-1.123456789012345678", "-1.123456789012345678"),
                                ("0", "0"), ("-0", "0"), ("1e-18", "0.000000000000000001")]:
            with self.subTest(value=value):
                self.assertEqual(map_balance(frame(mutation(balance=value)), CONTEXT)[0]["amount"], expected)

    def test_precision_is_independent_of_ambient_context(self):
        value = "999999999999999999999999999999.123456789012345678"
        with localcontext() as ctx:
            ctx.prec = 2
            self.assertEqual(map_balance(frame(mutation(balance=value)), CONTEXT)[0]["amount"], value)

    def test_no_derivation_of_margin_or_total_unrealized(self):
        events = map_balance(frame(mutation(crossUnPnl="-4.25", crossWalletBalance="3", maxWithdrawAmount="2")), CONTEXT)
        self.assertEqual({e["metadata"]["metric"] for e in events}, {"wallet", "available"})
        self.assertEqual(len(events), 2)

    def test_optional_fields_can_be_absent_without_zero_fill(self):
        rows = json.loads(RAW)
        for key in ("crossUnPnl", "crossWalletBalance", "maxWithdrawAmount", "marginAvailable"):
            del rows[0][key]
        self.assertEqual(len(map_balance(frame(json.dumps(rows)), CONTEXT)), 2)

    def test_synthetic_multi_asset_rows_remain_separate(self):
        rows = json.loads(RAW)
        rows.append({**rows[0], "asset": "USDC", "balance": "7.000001", "availableBalance": "6"})
        events = map_balance(frame(json.dumps(rows)), CONTEXT)
        self.assertEqual([(e["asset"], e["amount"]) for e in events],
                         [("USDT", "122607.35137903"), ("USDT", "23.72469206"), ("USDC", "7.000001"), ("USDC", "6")])


class BalanceNegativeContractTests(unittest.TestCase):
    def test_nonfinite_strings_rejected_in_every_money_field(self):
        for field in ("balance", "availableBalance", "crossWalletBalance", "crossUnPnl", "maxWithdrawAmount"):
            for value in ("NaN", "sNaN", "Infinity", "-Infinity", "Inf", "-Inf"):
                with self.subTest(field=field, value=value), self.assertRaises(NumericError):
                    map_balance(frame(mutation(**{field: value})), CONTEXT)

    def test_length_scale_exponent_magnitude_overflow_rejected(self):
        for value in ("1" * 97, "0." + "1" * 19, "1e19", "1e-19", "1e30", "1e999999", "9" * 49):
            with self.subTest(value=value), self.assertRaises(NumericError):
                map_balance(frame(mutation(balance=value)), CONTEXT)

    def test_money_numbers_bool_and_null_are_not_coerced(self):
        for value in (1, 1.25, True, None, [], {}):
            with self.subTest(value=value), self.assertRaises(BalanceError):
                map_balance(frame(mutation(balance=value)), CONTEXT)

    def test_missing_required_fields_fail(self):
        for field in ("accountAlias", "asset", "balance", "availableBalance", "updateTime"):
            rows = json.loads(RAW)
            del rows[0][field]
            with self.subTest(field=field), self.assertRaises(BalanceError):
                map_balance(frame(json.dumps(rows)), CONTEXT)

    def test_unknown_fields_fail_closed(self):
        with self.assertRaises(BalanceError):
            map_balance(frame(mutation(unverifiedNewMoneyField="8")), CONTEXT)

    def test_non_array_empty_and_pagination_wrappers_fail(self):
        for raw in (b'[]', b'{}', json.dumps(json.loads(RAW)[0]), json.dumps({"rows": json.loads(RAW), "total": 1})):
            with self.subTest(raw=raw), self.assertRaises(BalanceError):
                map_balance(frame(raw), CONTEXT)

    def test_duplicate_asset_rows_fail_whole_batch(self):
        row = json.loads(RAW)[0]
        with self.assertRaises(BalanceError):
            map_balance(frame(json.dumps([row, row])), CONTEXT)

    def test_timestamps_require_integer_ms_and_valid_past_date(self):
        for stamp in (0, -1, 1617939110373.5, "1617939110373", True, None, 999999999999999, 9999999999999):
            with self.subTest(stamp=stamp), self.assertRaises(BalanceError):
                map_balance(frame(mutation(updateTime=stamp)), CONTEXT)
        with self.assertRaises(BalanceError):
            map_balance(frame(RAW.replace(b'1617939110373', b'1.617939110373e12')), CONTEXT)

    def test_account_asset_and_margin_flag_must_match_schema(self):
        for field, value in [("accountAlias", "other"), ("asset", "usdt"), ("asset", None), ("marginAvailable", "true"), ("marginAvailable", 1)]:
            with self.subTest(field=field, value=value), self.assertRaises(BalanceError):
                map_balance(frame(mutation(**{field: value})), CONTEXT)

    def test_ws_channel_and_other_contracts_rejected(self):
        with self.assertRaises(BalanceError):
            map_balance(WebSocketEventParser().parse('{"e":"ACCOUNT_UPDATE"}', "futures_balance_v3"), CONTEXT)
        for contract in ("futures_income", "futures_account", "deposit_history", "unknown"):
            with self.subTest(contract=contract), self.assertRaises(UnsupportedContract):
                map_balance(frame(contract=contract), CONTEXT)

    def test_context_does_not_bypass_full_verification_gate(self):
        with self.assertRaises(UnsupportedContract): require_verified("futures_balance_v3")
        with self.assertRaises(UnsupportedContract): AccountEventMapper().map(frame(), context={"verified": True})


class SnapshotReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "separate-snapshot.sqlite"
        self.sandbox = SnapshotSandbox(self.path)

    def tearDown(self):
        self.sandbox.close()
        self.tmp.cleanup()

    def test_duplicate_delivery_and_restart_preserve_first_record(self):
        first = self.sandbox.ingest(RAW, CONTEXT)
        self.sandbox.close()
        self.sandbox = SnapshotSandbox(self.path)
        for _ in range(10):
            replay = self.sandbox.ingest(RAW, replace(CONTEXT, received_time="2026-11-06T19:00:00Z"))
            self.assertEqual({e["source_event_id"]: e for e in replay}, {e["source_event_id"]: e for e in first})
        self.assertEqual(len(self.sandbox.observations()), 2)
        self.assertEqual(self.sandbox.db.execute("SELECT count(*) FROM deliveries").fetchone()[0], 1)

    def test_poll_conflict_quarantined_without_overwrite(self):
        self.sandbox.ingest(RAW, CONTEXT)
        with self.assertRaisesRegex(BalanceError, "SNAPSHOT_POLL_BODY_CONFLICT"):
            self.sandbox.ingest(mutation(balance="99"), CONTEXT)
        self.assertEqual(len(self.sandbox.observations()), 2)
        self.assertEqual(self.sandbox.db.execute("SELECT count(*) FROM rejections").fetchone()[0], 1)
        self.assertEqual(self.sandbox.db.execute("SELECT body_sha256 FROM deliveries").fetchone()[0], hashlib.sha256(RAW).hexdigest())

    def test_later_poll_is_observation_not_cashflow_or_history_coverage(self):
        self.sandbox.ingest(RAW, CONTEXT)
        self.sandbox.ingest(mutation(balance="122707.35137903"), replace(CONTEXT, poll_id="poll-002"))
        self.assertEqual(len(self.sandbox.observations()), 4)
        self.assertEqual({e["event_type"] for e in self.sandbox.observations()}, {"BALANCE_SNAPSHOT"})
        tables = {r[0] for r in self.sandbox.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("ledger", tables)
        self.assertNotIn("outbox", tables)
        self.assertNotIn("checkpoints", tables)

    def test_source_alias_and_update_time_retained_without_numeric_coercion(self):
        self.sandbox.ingest(RAW, CONTEXT)
        row = json.loads(self.sandbox.db.execute("SELECT sdk_row_json FROM observations LIMIT 1").fetchone()[0])
        self.assertEqual(row["accountAlias"], "SgsR")
        self.assertEqual(row["updateTime"], "1617939110373")
        self.assertEqual(row["crossUnPnl"], "0.00000000")
        self.assertEqual(row["balance"], "122607.35137903")

    def test_malformed_batch_has_zero_partial_observations(self):
        rows = json.loads(RAW)
        rows.append({**rows[0], "asset": "USDC", "balance": "NaN"})
        with self.assertRaises(NumericError): self.sandbox.ingest(json.dumps(rows).encode(), CONTEXT)
        self.assertEqual(self.sandbox.observations(), ())
        self.assertEqual(self.sandbox.db.execute("SELECT count(*) FROM deliveries").fetchone()[0], 0)

    def test_quarantine_does_not_retain_unknown_payload(self):
        with self.assertRaises(BalanceError): self.sandbox.ingest(mutation(secret="SECRET_SENTINEL"), CONTEXT)
        self.assertNotIn("SECRET_SENTINEL", repr(self.sandbox.db.execute("SELECT * FROM rejections").fetchall()))

    def test_account_binding_cannot_be_swapped_between_polls(self):
        self.sandbox.ingest(RAW, CONTEXT)
        changed = replace(CONTEXT, expected_account_alias="other", poll_id="poll-002")
        with self.assertRaisesRegex(BalanceError, "SNAPSHOT_ACCOUNT_BINDING_CONFLICT"):
            self.sandbox.ingest(mutation(accountAlias="other"), changed)

    def test_two_local_accounts_cannot_claim_same_sdk_alias(self):
        self.sandbox.ingest(RAW, CONTEXT)
        with self.assertRaisesRegex(BalanceError, "SNAPSHOT_ACCOUNT_BINDING_CONFLICT"):
            self.sandbox.ingest(RAW, replace(CONTEXT, account="other-local-account"))

    def test_core_database_rejected_without_schema_changes(self):
        path = Path(self.tmp.name) / "core.sqlite"
        core = Store(path)
        before = list(core.connection.execute("SELECT sql FROM sqlite_master ORDER BY name"))
        with self.assertRaises(BalanceError): SnapshotSandbox(path)
        after = list(core.connection.execute("SELECT sql FROM sqlite_master ORDER BY name"))
        self.assertEqual([tuple(r) for r in before], [tuple(r) for r in after])
        core.close()

    def test_unsupported_database_version_rejected(self):
        self.sandbox.db.execute("PRAGMA user_version=2")
        with self.assertRaises(BalanceError): SnapshotSandbox(self.path)

    def test_precommit_rollback_and_replay(self):
        def fault(stage):
            if stage == "before_commit": raise RuntimeError("injected failure")
        with self.assertRaises(RuntimeError): self.sandbox.ingest(RAW, CONTEXT, fault=fault)
        self.assertEqual(self.sandbox.observations(), ())
        self.assertEqual(len(self.sandbox.ingest(RAW, CONTEXT)), 2)

    def _crash_child(self, stage):
        # Real child-process death: SQLite recovery, no simulated success status.
        code = """
import os, sys
from bot1.adapters.binance.balance import BalanceContext
from bot1.adapters.binance.snapshot_store import SnapshotSandbox
from pathlib import Path
s=SnapshotSandbox(sys.argv[1])
c=BalanceContext('offline-test-account','SgsR','poll-001','2026-11-06T18:00:00Z')
def die(stage):
    if stage == sys.argv[3]: os._exit(73)
s.ingest(Path(sys.argv[2]).read_bytes(),c,fault=die)
"""
        result = subprocess.run([sys.executable, "-c", code, str(self.path), str(FIXTURES / "balance_v3_response.json"), stage], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 73, result.stderr.decode())

    def test_process_death_before_commit_then_recovery(self):
        self._crash_child("before_commit")
        self.assertEqual(self.sandbox.observations(), ())
        self.sandbox.ingest(RAW, CONTEXT)
        self.assertEqual(len(self.sandbox.observations()), 2)

    def test_process_death_after_commit_then_recovery(self):
        self._crash_child("after_commit")
        self.assertEqual(len(self.sandbox.observations()), 2)
        self.sandbox.ingest(RAW, CONTEXT)
        self.assertEqual(len(self.sandbox.observations()), 2)

    def test_realized_fee_funding_and_unknown_income_remain_blocked(self):
        # Synthetic mutations of the SDK income model, NOT official fixtures.
        for income_type in ("REALIZED_PNL", "COMMISSION", "FUNDING_FEE", "TRANSFER", "UNKNOWN_TYPE"):
            raw = json.dumps([{"symbol": "BTCUSDT", "incomeType": income_type, "income": "1", "asset": "USDT", "time": 1617939110373, "tranId": 7}]).encode()
            with self.subTest(income_type=income_type), self.assertRaises(UnsupportedContract):
                self.sandbox.ingest(raw, CONTEXT, contract_id="futures_income")
        self.assertEqual(self.sandbox.observations(), ())

    def test_rest_ws_overlap_cannot_double_post(self):
        self.sandbox.ingest(RAW, CONTEXT)
        ws = WebSocketEventParser().parse('{"e":"ACCOUNT_UPDATE","E":1617939110373,"T":1617939110373,"a":{"m":"DEPOSIT","B":[{"a":"USDT","wb":"122607.35137903","cw":"23.72469206","bc":"100"}]}}', "futures_user_stream")
        with self.assertRaises(UnsupportedContract): BinanceEventCorrelation().link(frame(), ws)
        with self.assertRaises(UnsupportedContract): AccountEventMapper().map(ws, context=CONTEXT)
        self.assertEqual(len(self.sandbox.observations()), 2)
        # This proves denial, NOT successful Binance REST/WS economic correlation.

    def test_internal_schema_core_integration_adds_zero_cashflow(self):
        core = Store(Path(self.tmp.name) / "synthetic-core.sqlite")
        try:
            engine = Engine(core, primary_source="binance-rest-sdk")
            for offset, event in enumerate(map_balance(frame(), CONTEXT), 1):
                engine.process(engine.ingest(event, "offline-sdk-probe", offset))
            self.assertEqual(core.connection.execute("SELECT count(*) FROM ledger").fetchone()[0], 0)
            self.assertEqual(core.connection.execute("SELECT count(*) FROM openings").fetchone()[0], 0)
            self.assertEqual(core.connection.execute("SELECT count(*) FROM snapshots").fetchone()[0], 2)
            row = core.connection.execute("SELECT status FROM reconciliations").fetchone()
            self.assertEqual(row[0], "MISSING_OPENING")
        finally:
            core.close()

    def test_trial_plan_is_inert_and_active_allowlist_empty(self):
        plan = balance_trial_plan(Path(self.tmp.name) / "future-trial.sqlite")
        self.assertTrue(plan["snapshot_only"])
        for field in ("live_readonly_enabled", "network_enabled", "write_business_ledger", "send_real_telegram", "credential_loading_enabled"):
            self.assertFalse(plan[field])
        self.assertEqual(plan["active_allowlist"], [])
        self.assertEqual(EndpointAllowlist().entries, frozenset())
        self.assertFalse(Path(plan["database"]).exists())
        with self.assertRaises(LiveModeDisabled): AdapterConfig(mode="live_readonly")
        with self.assertRaises(LiveModeDisabled): EndpointAllowlist().authorize(**plan["sdk_candidate"])
