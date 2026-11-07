from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import io
import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest

from bot1.database.store import Store
from bot1.domain.events import gmt7
from bot1.health.monitor import SafeJSONFormatter
from bot1.ledger.engine import Engine
from bot1.recovery.runner import Recovery
from bot1.sources.fake import FakeBinanceSource, scenario, sample_event

ROOT = Path(__file__).resolve().parents[2]


class SafetyTests(unittest.TestCase):
    def test_two_actual_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "concurrent.sqlite"
            initial = Store(path); initial.close()
            barrier = threading.Barrier(2)
            def worker(index):
                store = Store(path, timeout_ms=2000)
                try:
                    barrier.wait(timeout=5)
                    engine = Engine(store)
                    return engine.process(engine.ingest(sample_event(10), f"worker-{index}", 1))
                finally: store.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(worker, (1, 2)))
            self.assertNotIn("quarantined", results)
            store = Store(path)
            try:
                self.assertEqual(len(store.rows("SELECT * FROM ledger")), 1)
                self.assertEqual(len(store.rows("SELECT * FROM outbox")), 1)
            finally: store.close()

    def test_sqlite_error_rolls_back_and_can_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "failure.sqlite")
            def inject(point):
                if point == "after_ledger": raise sqlite3.OperationalError("simulated disk I/O failure")
            engine = Engine(store, fault=inject)
            try:
                i = engine.ingest(sample_event(10), "disk-fault", 1)
                with self.assertRaises(sqlite3.OperationalError): engine.process(i)
                self.assertFalse(store.rows("SELECT * FROM ledger"))
                self.assertFalse(store.rows("SELECT * FROM outbox"))
                self.assertEqual(store.rows("SELECT status FROM inbox")[0]["status"], "pending")
                Recovery(Engine(store)).replay_pending()
                self.assertEqual(len(store.rows("SELECT * FROM ledger")), 1)
            finally: store.close()

    def test_json_logger_redacts_unknown_message_and_exception(self):
        stream = io.StringIO(); handler = logging.StreamHandler(stream)
        handler.setFormatter(SafeJSONFormatter())
        logger = logging.getLogger("bot1.test"); logger.addHandler(handler)
        try:
            try: raise RuntimeError("SECRET_SENTINEL")
            except RuntimeError: logger.exception("SECRET_SENTINEL")
        finally: logger.removeHandler(handler)
        self.assertNotIn("SECRET_SENTINEL", stream.getvalue())
        self.assertEqual(json.loads(stream.getvalue())["action"], "diagnostic")
        self.assertTrue(json.loads(stream.getvalue())["time_utc"].endswith("+00:00"))

    def test_utc_gmt7_day_boundary(self):
        self.assertEqual(gmt7("2026-11-06T20:30:00Z"), "2026-11-07T03:30:00+07:00")

    def test_fake_source_pacing_and_disconnect(self):
        ticks = []
        source = FakeBinanceSource(scenario(), disconnect_after=2, pace_ms=10, sleeper=ticks.append)
        iterator = source.history()
        self.assertEqual(next(iterator)[0], 1); self.assertEqual(next(iterator)[0], 2)
        from bot1.sources.fake import SourceDisconnected
        with self.assertRaises(SourceDisconnected): next(iterator)
        self.assertEqual(len(ticks), 2)

    def test_cli_end_to_end_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "cli.sqlite"; mock = Path(tmp) / "mock.json"; sink = Path(tmp) / "sink.jsonl"
            command = [sys.executable, str(ROOT / "scripts/bot1.py"), "--db", str(db)]
            def run(*args):
                p = subprocess.run(command + list(args), cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                return json.loads(p.stdout)
            self.assertEqual(run("init")["schema_version"], 1)
            run("load-mock", "--output", str(mock))
            self.assertEqual(run("simulate", "--input", str(mock), "--disconnect-after", "4")["status"], "incomplete")
            self.assertEqual(run("recover", "--input", str(mock))["status"], "complete")
            balances = run("balances")["balances"]
            self.assertEqual({x["wallet"]: x["ledger_balance"] for x in balances}, {"SPOT": "9", "FUTURES": "76.5"})
            self.assertEqual(len(run("history")["ledger"]), 10)
            self.assertTrue(run("notifications", "--drain", "--sink", str(sink))["fake_attempts_this_run"])
            self.assertEqual(run("notifications", "--drain", "--sink", str(sink))["fake_attempts_this_run"], 0)
            self.assertEqual(run("gaps"), {"quarantine": [], "reconciliation": [], "windows": []})
            self.assertEqual(run("health")["database"], "ok")

    def test_no_network_or_credentials_dependencies_in_source(self):
        # Architectural guard plus socket-denied full scenario test, not a live permission test.
        import ast
        for path in (ROOT / "src/bot1").rglob("*.py"):
            tree = ast.parse(path.read_text())
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import): modules.extend(n.name.split(".")[0] for n in node.names)
                if isinstance(node, ast.ImportFrom): modules.append((node.module or "").split(".")[0])
            self.assertFalse(set(modules) & {"requests", "urllib", "http", "socket", "websockets", "binance", "telegram"}, path)

    def test_financial_action_cli_commands_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "must-not-be-created.sqlite"
            for action in ("enable-trading", "withdraw", "transfer", "change-leverage"):
                p = subprocess.run([sys.executable, str(ROOT / "scripts/bot1.py"), "--db", str(db), action], capture_output=True, text=True)
                self.assertEqual(p.returncode, 2)
                self.assertFalse(db.exists())
