from __future__ import annotations

import copy
from decimal import Decimal
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from bot1.database.store import Store, DatabaseBusy
from bot1.domain.events import Event
from bot1.health.monitor import Health
from bot1.ledger.engine import Engine
from bot1.notifications.fake import FakeTelegram
from bot1.notifications.outbox import Outbox
from bot1.recovery.runner import Recovery
from bot1.sources.fake import FakeBinanceSource, sample_event, scenario
from tests.fixtures.helpers import with_records

ROOT = Path(__file__).resolve().parents[2]


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "db.sqlite"
        self.store = Store(self.path)
        self.engine = Engine(self.store)
        self.offset = 0

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def add(self, e, stream="local"):
        self.offset += 1
        i = self.engine.ingest(e, stream, self.offset)
        return self.engine.process(i)

    def opening(self, wallet="SPOT", amount="0", asset="USDT", account="demo", index=1):
        return self.add(sample_event(index, "BALANCE_SNAPSHOT", amount, wallet=wallet,
                                     asset=asset, account=account, metadata={"opening": True}))

    def balance(self, wallet="SPOT", asset="USDT", account="demo"):
        return self.engine.balance(account, wallet, asset)["ledger_balance"]

    def count(self, table):
        return self.store.connection.execute("SELECT count(*) FROM " + table).fetchone()[0]

    def test_full_scenario_and_no_network(self):
        with patch("socket.socket", side_effect=AssertionError("NETWORK_FORBIDDEN")):
            result = Recovery(self.engine).run(FakeBinanceSource(scenario()))
            fake = FakeTelegram()
            Outbox(self.store, fake).drain()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(self.balance(), "9")
        self.assertEqual(self.balance("FUTURES"), "76.5")
        self.assertEqual(self.count("ledger"), 10)
        self.assertEqual(self.engine.gaps(), {"quarantine": [], "reconciliation": [], "windows": []})
        self.assertTrue(fake.deliveries)
        summary = self.engine.summaries("demo")
        self.assertEqual([x["net_amount"] for x in summary if x["kind"] == "DEPOSIT"], ["100"])

    def test_pending_completed_duplicate_stale(self):
        self.opening()
        pending = sample_event(10, amount="100", status="pending")
        self.add(pending)
        self.assertEqual(self.balance(), "0")
        completed = dict(pending, status="completed", version=2)
        self.add(completed); self.add(completed); self.add(pending)
        self.assertEqual(self.balance(), "100")
        self.assertEqual(self.count("ledger"), 1)
        self.assertEqual(self.count("outbox"), 1)

    def test_failed_cancelled_are_not_cashflow(self):
        self.opening(amount="100")
        for i, status in enumerate(["failed", "cancelled"], 10):
            pending = sample_event(i, "WITHDRAWAL", "20", status="pending")
            self.add(pending)
            self.add(dict(pending, status=status, version=2))
        self.assertEqual(self.balance(), "100")
        self.assertEqual(self.count("ledger"), 0)

    def test_terminal_change_requires_correction(self):
        self.opening()
        e = sample_event(10)
        self.add(e)
        self.assertEqual(self.add(dict(e, status="failed", version=2)), "quarantined")
        self.assertEqual(self.balance(), "1")

    def test_same_identity_financial_conflict(self):
        self.opening(); self.add(sample_event(10, amount="10"))
        self.assertEqual(self.add(sample_event(10, amount="20")), "quarantined")
        self.assertEqual(self.balance(), "10")
        self.assertEqual(self.engine.gaps()["quarantine"][0]["code"], "IDENTITY_FINANCIAL_CONFLICT")

    def test_same_identity_changed_economic_id_conflicts(self):
        self.opening()
        e = sample_event(10, amount="10", metadata={"economic_id": "e1", "correlation_evidence": "fixture"})
        self.add(e)
        changed = copy.deepcopy(e); changed["version"] = 2; changed["metadata"]["economic_id"] = "e2"
        self.assertEqual(self.add(changed), "quarantined")
        self.assertEqual(self.balance(), "10")

    def test_same_time_amount_different_ids_are_distinct(self):
        self.opening()
        e = sample_event(10, amount="10")
        self.add(e); self.add(dict(e, source_event_id="other-id"))
        self.assertEqual(self.balance(), "20")

    def test_cross_source_verified_correlation(self):
        self.opening()
        meta = {"economic_id": "income-01", "correlation_evidence": "synthetic-verified-link"}
        a = sample_event(10, "TRADING_FEE", "-1", metadata=meta)
        self.add(a)
        self.add(dict(a, source="fake-stream", source_event_id="stream-1"))
        self.assertEqual(self.balance(), "-1")
        self.assertEqual(self.count("ledger"), 1)
        self.assertEqual(self.count("events"), 3)
        self.assertEqual(self.count("outbox"), 1)

    def test_secondary_source_unverified_is_gap(self):
        self.opening()
        self.assertEqual(self.add(sample_event(10, source="secondary")), "quarantined")
        self.assertEqual(self.balance(), "0")

    def test_economic_conflict_is_not_ignored(self):
        self.opening()
        meta = {"economic_id": "same", "correlation_evidence": "fixture"}
        self.add(sample_event(10, amount="10", metadata=meta))
        self.assertEqual(self.add(sample_event(10, amount="20", source="secondary", metadata=meta)), "quarantined")
        self.assertEqual(self.balance(), "10")

    def test_wallet_asset_account_namespaces(self):
        self.opening(); self.opening(asset="BTC"); self.opening(account="other")
        e = sample_event(10, amount="10")
        self.add(e); self.add(dict(e, asset="BTC")); self.add(dict(e, account="other"))
        self.assertEqual(self.balance(), "10")
        self.assertEqual(self.balance(asset="BTC"), "10")
        self.assertEqual(self.balance(account="other"), "10")
        self.assertEqual(len(self.engine.summaries("demo")), 2)

    def test_normalized_symbol_qualified_source_ids(self):
        self.opening()
        e = sample_event(10, amount="1", source_event_id="BTCUSDT:trade-123")
        self.add(e); self.add(dict(e, source_event_id="ETHUSDT:trade-123"))
        self.assertEqual(self.balance(), "2")
        self.assertEqual(self.count("ledger"), 2)

    def test_margin_unrealized_snapshot_do_not_post(self):
        self.opening(wallet="FUTURES", amount="100")
        for i, metric, amount in [(10, "available", "80"), (11, "available", "60"), (12, "margin", "104"), (13, "initial_margin", "20")]:
            self.add(sample_event(i, "BALANCE_SNAPSHOT", amount, wallet="FUTURES", metadata={"metric": metric}))
        self.add(sample_event(14, "UNREALIZED_PNL_SNAPSHOT", "4", wallet="FUTURES"))
        self.assertEqual(self.balance("FUTURES"), "100")
        self.assertEqual(self.count("ledger"), 0)
        self.assertEqual(self.count("snapshots"), 6)
        metrics = self.engine.latest_metrics("demo", "FUTURES", "USDT")
        self.assertEqual(metrics["margin"]["amount"], "104")
        self.assertEqual(metrics["available"]["amount"], "60")
        self.assertEqual(metrics["unrealized"]["amount"], "4")

    def test_snapshot_asof_late_event_reconciles_without_adjustment(self):
        self.opening()
        self.add(sample_event(20, "BALANCE_SNAPSHOT", "10"))
        self.assertEqual(self.engine.gaps()["reconciliation"][0]["residual"], "10")
        self.assertEqual(self.balance(), "0")
        self.add(sample_event(10, amount="10"))
        self.assertFalse(self.engine.gaps()["reconciliation"])
        alerts = [json.loads(row["payload"]) for row in self.store.rows("SELECT payload FROM outbox")]
        self.assertTrue(any(a["type"] == "RECONCILIATION_RESOLVED" and a["expected"] == "10" for a in alerts))
        self.assertEqual(self.balance(), "10")
        self.add(sample_event(30, amount="5"))
        self.assertEqual(self.balance(), "15")
        self.assertEqual(self.store.rows("SELECT expected FROM reconciliations")[0]["expected"], "10")

    def test_snapshot_duplicate_time_conflict(self):
        self.opening()
        self.add(sample_event(10, "BALANCE_SNAPSHOT", "0"))
        self.assertEqual(self.add(sample_event(10, "BALANCE_SNAPSHOT", "1", source_event_id="other")), "quarantined")
        self.assertEqual(self.engine.balance("demo", "SPOT", "USDT")["latest_observed"]["amount"], "0")

    def test_baseline_already_contains_old_history(self):
        self.opening(amount="100", index=20)
        self.add(sample_event(10, amount="100"))
        self.add(sample_event(30, "BALANCE_SNAPSHOT", "100"))
        self.assertEqual(self.balance(), "100")
        self.assertEqual(self.count("ledger"), 0)
        self.assertFalse(self.engine.gaps()["reconciliation"])

    def test_opening_cannot_hide_existing_ledger(self):
        self.add(sample_event(10, amount="10"))
        self.assertEqual(self.engine.gaps()["reconciliation"][0]["status"], "MISSING_OPENING")
        self.assertEqual(Health(self.store).snapshot()["missing_openings"], 1)
        self.assertEqual(self.opening(amount="10", index=20), "quarantined")
        self.assertIsNone(self.balance())

    def test_transfer_two_legs_rollback_and_funding(self):
        self.opening(amount="100"); self.opening("FUTURES"); self.opening("FUNDING")
        self.add(sample_event(10, "INTERNAL_TRANSFER", "30", metadata={"to_wallet": "FUTURES"}))
        self.add(sample_event(11, "INTERNAL_TRANSFER", "10", wallet="FUTURES", metadata={"to_wallet": "FUNDING"}))
        self.assertEqual([self.balance(w) for w in ["SPOT", "FUTURES", "FUNDING"]], ["70", "20", "10"])
        self.assertEqual(self.count("ledger"), 4)
        alerts = [json.loads(row["payload"]) for row in self.store.rows("SELECT payload FROM outbox")]
        self.assertEqual(alerts[0]["balance_changes"], [{"wallet": "SPOT", "asset": "USDT", "ledger_delta": "-30"},
                                                       {"wallet": "FUTURES", "asset": "USDT", "ledger_delta": "30"}])

    def test_withdrawal_and_separate_fee(self):
        self.opening(amount="100")
        self.add(sample_event(10, "WITHDRAWAL", "20")); self.add(sample_event(11, "WITHDRAWAL_FEE", "-1"))
        self.assertEqual(self.balance(), "79")
        self.assertEqual({r["kind"] for r in self.engine.summaries("demo")}, {"WITHDRAWAL", "WITHDRAWAL_FEE"})

    def test_realized_pnl_commission_funding_exact_balance(self):
        self.opening("FUTURES", "100")
        for index, kind, amount in [(10, "REALIZED_PNL", "8"), (11, "TRADING_FEE", "-1"), (12, "FUNDING_FEE", "-0.5")]:
            self.add(sample_event(index, kind, amount, wallet="FUTURES"))
        self.assertEqual(self.balance("FUTURES"), "106.5")
        self.assertEqual({r["kind"]: r["net_amount"] for r in self.engine.summaries("demo")},
                         {"REALIZED_PNL": "8", "TRADING_FEE": "-1", "FUNDING_FEE": "-0.5"})

    def test_signed_funding_and_non_usdt_fee(self):
        self.opening("FUTURES", "100"); self.opening("FUTURES", "1", "BNB")
        self.add(sample_event(10, "FUNDING_FEE", "0.5", wallet="FUTURES"))
        self.add(sample_event(11, "TRADING_FEE", "-0.01", wallet="FUTURES", asset="BNB"))
        self.assertEqual(self.balance("FUTURES"), "100.5")
        self.assertEqual(self.balance("FUTURES", "BNB"), "0.99")

    def test_correction_reversal_audit(self):
        self.opening()
        self.add(sample_event(10, amount="10"))
        target = self.store.rows("SELECT id FROM events WHERE kind='DEPOSIT'")[0]["id"]
        reversal = sample_event(11, "ACCOUNT_ADJUSTMENT", "-10", status="correction", metadata={"reverses": target})
        self.add(reversal); self.add(reversal)
        self.assertEqual(self.balance(), "0")
        self.assertEqual(self.count("ledger"), 2)
        self.assertEqual(self.count("reversals"), 1)
        self.assertEqual(self.engine.summaries("demo")[0]["net_amount"], "0")
        self.assertEqual(self.add(dict(reversal, source_event_id="second-reversal")), "quarantined")

    def test_transfer_reversal_both_legs(self):
        self.opening(amount="100"); self.opening("FUTURES")
        self.add(sample_event(10, "INTERNAL_TRANSFER", "30", metadata={"to_wallet": "FUTURES"}))
        target = self.store.rows("SELECT id FROM events WHERE kind='INTERNAL_TRANSFER'")[0]["id"]
        self.add(sample_event(11, "ACCOUNT_ADJUSTMENT", "-30", status="correction", metadata={"reverses": target}))
        self.assertEqual((self.balance(), self.balance("FUTURES")), ("100", "0"))

    def test_invalid_between_valid_checkpoint_and_replacement(self):
        self.opening()
        bad = self.engine.ingest(sample_event(10, amount="NaN"), "local", 2)
        self.offset = 2; self.engine.process(bad)
        self.add(sample_event(11, amount="5"))
        self.assertEqual(self.store.rows("SELECT processed_offset FROM checkpoints")[0]["processed_offset"], 1)
        replacement = self.engine.replace_quarantined(bad, sample_event(10, amount="10"))
        self.engine.process(replacement)
        self.assertEqual(self.balance(), "15")
        self.assertEqual(self.store.rows("SELECT processed_offset FROM checkpoints")[0]["processed_offset"], 3)
        self.assertFalse(self.engine.gaps()["quarantine"])
        self.assertEqual(self.count("inbox"), 4)

    def test_invalid_types_quarantine_without_zero(self):
        self.opening()
        for i, change in enumerate([{"amount": None}, {"amount": 0.1}, {"event_type": []}, {"wallet": []}, {"event_time": "bad"}, {"id_trusted": False}, {"event_type": "PLACE_ORDER"}], 10):
            self.assertEqual(self.add(sample_event(i, **change)), "quarantined")
        self.assertEqual(self.count("ledger"), 0)
        self.assertEqual(self.balance(), "0")

    def test_no_trustworthy_id_is_not_timestamp_deduped(self):
        self.opening()
        self.assertEqual(self.add(sample_event(10, source_event_id="", id_trusted=False)), "quarantined")

    def test_sensitive_unknown_fields_redacted(self):
        self.opening()
        e = sample_event(10, metadata={"token": "SECRET_SENTINEL"})
        self.assertEqual(self.add(e), "quarantined")
        text = json.dumps(self.store.rows("SELECT * FROM inbox")) + json.dumps(self.store.rows("SELECT * FROM outbox"))
        self.assertNotIn("SECRET_SENTINEL", text)

    def test_source_offset_conflict_preserves_committed_event(self):
        self.opening()
        self.add(sample_event(10, amount="5"))
        self.engine.ingest(sample_event(10, amount="6"), "local", 2)
        self.assertEqual(self.balance(), "5")
        self.assertEqual(self.engine.gaps()["quarantine"][0]["code"], "SOURCE_OFFSET_CONFLICT")

    def test_replay_and_restart_persistence(self):
        result = Recovery(self.engine).run(FakeBinanceSource(scenario()))
        counts = (self.count("ledger"), self.count("outbox"), self.count("inbox"))
        self.store.close(); self.store = Store(self.path); self.engine = Engine(self.store)
        again = Recovery(self.engine).run(FakeBinanceSource(scenario()))
        self.assertEqual(again["status"], result["status"])
        self.assertEqual((self.count("ledger"), self.count("outbox"), self.count("inbox")), counts)
        self.assertEqual(self.balance("FUTURES"), "76.5")

    def test_disconnect_resume_and_gap_completion(self):
        partial = Recovery(self.engine).run(FakeBinanceSource(scenario(), disconnect_after=5))
        self.assertEqual(partial["reason"], "SOURCE_DISCONNECTED")
        self.assertTrue(self.engine.gaps()["windows"])
        self.store.close(); self.store = Store(self.path); self.engine = Engine(self.store)
        self.assertEqual(Recovery(self.engine).run(FakeBinanceSource(scenario()))["status"], "complete")
        self.assertEqual(self.balance(), "9")

    def test_missing_offset_even_net_zero_is_gap(self):
        data = scenario()
        data["records"] = [r for r in data["records"] if r["offset"] not in (5, 6)]
        result = Recovery(self.engine).run(FakeBinanceSource(data))
        self.assertEqual(result["reason"], "MISSING_OFFSETS")
        self.assertEqual(self.store.rows("SELECT processed_offset FROM checkpoints")[0]["processed_offset"], 4)

    def test_equal_opposite_missing_events_still_detected(self):
        records = [sample_event(1, "BALANCE_SNAPSHOT", "0", metadata={"opening": True}),
                   sample_event(2, "REALIZED_PNL", "5"), sample_event(3, "REALIZED_PNL", "-5"),
                   sample_event(4, "BALANCE_SNAPSHOT", "0")]
        data = with_records(records); data["records"] = [data["records"][0], data["records"][3]]
        result = Recovery(self.engine).run(FakeBinanceSource(data))
        self.assertEqual(result["reason"], "MISSING_OFFSETS")
        self.assertFalse(self.engine.gaps()["reconciliation"])

    def test_manifest_detects_substituted_id(self):
        data = scenario(); data["records"][4]["event"]["source_event_id"] = "substituted"
        result = Recovery(self.engine).run(FakeBinanceSource(data))
        self.assertEqual(result["reason"], "MANIFEST_MISMATCH")

    def test_new_reconciliation_gap_invalidates_completion(self):
        self.assertEqual(Recovery(self.engine).run(FakeBinanceSource(scenario()))["status"], "complete")
        self.add(sample_event(5, amount="1", source_event_id="late-extra"))
        self.assertEqual(self.balance(), "10")
        self.assertEqual(self.engine.gaps()["reconciliation"][0]["residual"], "-1")
        self.assertEqual(self.store.rows("SELECT complete_offset FROM checkpoints WHERE stream='demo-history'")[0]["complete_offset"], 0)
        self.assertEqual(self.store.rows("SELECT status FROM recovery_windows")[0]["status"], "incomplete")

    def test_out_of_order_history(self):
        data = scenario()
        # Baselines first; balance snapshots before cashflows, then late data.
        records = data["records"]
        data["records"] = records[:2] + records[11:] + list(reversed(records[2:11]))
        self.assertEqual(Recovery(self.engine).run(FakeBinanceSource(data))["status"], "complete")
        self.assertEqual(self.balance("FUTURES"), "76.5")

    def test_db_lock_is_retryable_not_quarantine(self):
        other = sqlite3.connect(self.path, isolation_level=None)
        other.execute("BEGIN IMMEDIATE")
        try:
            with self.assertRaises(DatabaseBusy): self.engine.ingest(sample_event(10), "lock", 1)
        finally:
            other.execute("ROLLBACK"); other.close()
        self.engine.process(self.engine.ingest(sample_event(10), "lock", 1))
        self.assertEqual(self.count("ledger"), 1)
        self.assertEqual(self.count("quarantine"), 0)

    def test_backup_restore_replay(self):
        Recovery(self.engine).run(FakeBinanceSource(scenario()))
        backup = Path(self.tmp.name) / "backup.sqlite"
        self.store.backup(backup)
        restored = Store(backup)
        try:
            e = Engine(restored)
            Recovery(e).run(FakeBinanceSource(scenario()))
            self.assertEqual(e.balance("demo", "FUTURES", "USDT")["ledger_balance"], "76.5")
            self.assertEqual(restored.connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(len(restored.rows("SELECT * FROM ledger")), self.count("ledger"))
        finally: restored.close()

    def test_schema_version_and_money_text(self):
        self.assertEqual(self.store.connection.execute("PRAGMA user_version").fetchone()[0], 1)
        for table in ("ledger", "events", "snapshots", "openings"):
            columns = self.store.rows("PRAGMA table_info(" + table + ")")
            self.assertEqual([c["type"] for c in columns if c["name"] == "amount"], ["TEXT"])

    def test_unknown_schema_version_rejected(self):
        other = Path(self.tmp.name) / "future.sqlite"
        with sqlite3.connect(other) as db: db.execute("PRAGMA user_version=9")
        with self.assertRaisesRegex(RuntimeError, "DB_SCHEMA_VERSION"): Store(other)

    def test_health_and_processing_lag(self):
        self.opening(); self.add(sample_event(10, amount="NaN"))
        health = Health(self.store).snapshot()
        self.assertEqual(health["database"], "ok")
        self.assertEqual(health["quarantine"], 1)
        self.assertEqual(health["processed"], 1)
        self.assertIsInstance(health["processing_lag_ms"], int)
        self.assertEqual(health["network"], "OFFLINE_ONLY")

    def test_fake_notifier_success_and_logic_dedup(self):
        self.opening(); e = sample_event(10); self.add(e); self.add(e)
        fake = FakeTelegram()
        sender = Outbox(self.store, fake)
        self.assertEqual(sender.drain(), 1)
        self.assertEqual(sender.drain(), 0)
        self.assertEqual(len(fake.deliveries), 1)
        self.assertEqual(self.store.rows("SELECT status,attempts FROM outbox"), [{"status": "sent", "attempts": 1}])

    def test_notifier_retry_and_rate_limit(self):
        self.opening(); self.add(sample_event(10))
        now = [100000]
        fake = FakeTelegram(["rate_limit", "ok"])
        sender = Outbox(self.store, fake, clock=lambda: now[0])
        sender.send_one()
        row = self.store.rows("SELECT * FROM outbox")[0]
        self.assertEqual((row["status"], row["next_attempt"]), ("retry", 130000))
        self.assertFalse(sender.send_one())
        now[0] = 130000; self.assertTrue(sender.send_one())
        self.assertEqual(len(fake.deliveries), 1)
        self.assertEqual(self.store.rows("SELECT attempts FROM outbox")[0]["attempts"], 2)

    def test_notifier_transient_retry_then_success(self):
        self.opening(); self.add(sample_event(10))
        now = [0]; fake = FakeTelegram(["transient", "ok"])
        sender = Outbox(self.store, fake, clock=lambda: now[0])
        sender.send_one(); now[0] = 1000; sender.send_one()
        self.assertEqual(len(fake.deliveries), 1)
        self.assertEqual(Health(self.store).snapshot()["notification_retries"], 1)

    def test_ambiguous_delivery_not_automatically_resent(self):
        self.opening(); self.add(sample_event(10))
        fake = FakeTelegram(["ambiguous"])
        sender = Outbox(self.store, fake)
        sender.send_one(); self.assertFalse(sender.send_one())
        self.assertEqual(self.store.rows("SELECT status FROM outbox")[0]["status"], "ambiguous")
        self.assertEqual(len(fake.deliveries), 1)

    def test_permanent_notification_error_dead_letter(self):
        self.opening(); self.add(sample_event(10))
        Outbox(self.store, FakeTelegram(["permanent"])).send_one()
        self.assertEqual(self.store.rows("SELECT status FROM outbox")[0]["status"], "dead")

    def test_notification_retry_cap(self):
        self.opening(); self.add(sample_event(10))
        now = [0]; sender = Outbox(self.store, FakeTelegram(["transient"] * 6), clock=lambda: now[0])
        for _ in range(5): sender.send_one(); now[0] += 100000
        self.assertEqual(self.store.rows("SELECT status,attempts FROM outbox"), [{"status": "dead", "attempts": 5}])

    def test_notification_crash_after_send_is_ambiguous(self):
        self.opening(); self.add(sample_event(10))
        sink = Path(self.tmp.name) / "receipts.jsonl"
        def fail(point):
            if point == "after_send": raise RuntimeError("CRASH")
        with self.assertRaises(RuntimeError):
            Outbox(self.store, FakeTelegram(sink=sink), clock=lambda: 0, fault=fail).send_one()
        self.store.close(); self.store = Store(self.path); self.engine = Engine(self.store)
        sender = Outbox(self.store, FakeTelegram(sink=sink), clock=lambda: 60001)
        self.assertFalse(sender.send_one())
        self.assertEqual(self.store.rows("SELECT status FROM outbox")[0]["status"], "ambiguous")
        self.assertEqual(len(sink.read_text().splitlines()), 1)

    def test_two_workers_cannot_claim_same_lease(self):
        self.opening(); self.add(sample_event(10))
        second = Store(self.path)
        fake = FakeTelegram()
        other = Outbox(second, fake, clock=lambda: 0)
        def pause(point):
            if point == "after_claim": self.assertFalse(other.send_one())
        try:
            Outbox(self.store, fake, clock=lambda: 0, fault=pause).send_one()
            self.assertEqual(len(fake.deliveries), 1)
        finally: second.close()

    def test_second_ingest_worker_has_idempotent_financial_effect(self):
        self.opening(); e = sample_event(10)
        self.add(e)
        second = Store(self.path)
        try:
            other = Engine(second)
            other.process(other.ingest(e, "worker2", 1))
            self.assertEqual(self.balance(), "1")
            self.assertEqual(self.count("ledger"), 1)
        finally: second.close()

    def test_real_process_exit_before_commit_and_recovery(self):
        self.opening()
        code = '''import os,sys
from bot1.database.store import Store
from bot1.ledger.engine import Engine
from bot1.sources.fake import sample_event
s=Store(sys.argv[1])
def fault(point):
 if point == 'before_commit': os._exit(23)
e=Engine(s,fault=fault)
e.process(e.ingest(sample_event(10,amount='10'),'crash-process',1))
'''
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        p = subprocess.run([sys.executable, "-c", code, str(self.path)], env=env, capture_output=True)
        self.assertEqual(p.returncode, 23)
        self.assertEqual(self.count("ledger"), 0)
        Recovery(self.engine).replay_pending()
        self.assertEqual(self.balance(), "10")


def fault_test(point):
    def test(self):
        self.opening()
        def inject(at):
            if at == point: raise RuntimeError("INJECTED_CRASH")
        self.engine.fault = inject
        if point == "after_inbox_commit":
            with self.assertRaises(RuntimeError): self.engine.ingest(sample_event(10, amount="10"), "fault", 1)
        else:
            ident = self.engine.ingest(sample_event(10, amount="10"), "fault", 1)
            with self.assertRaises(RuntimeError): self.engine.process(ident)
        self.store.close(); self.store = Store(self.path); self.engine = Engine(self.store)
        if point != "after_commit": self.assertEqual(self.count("ledger"), 0)
        Recovery(self.engine).replay_pending()
        self.assertEqual(self.balance(), "10")
        self.assertEqual(self.count("ledger"), 1)
        self.assertEqual(self.count("outbox"), 1)
    return test


for point in ["after_inbox_commit", "after_event_insert", "after_ledger", "after_outbox", "before_commit", "after_commit"]:
    setattr(CoreTests, "test_fault_" + point, fault_test(point))
