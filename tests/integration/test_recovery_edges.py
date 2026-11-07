import copy
from pathlib import Path
import tempfile
import unittest

from bot1.database.store import Store
from bot1.ledger.engine import Engine
from bot1.recovery.runner import Recovery
from bot1.sources.fake import FakeBinanceSource, scenario, sample_event
from tests.fixtures.helpers import with_records


class RecoveryEdgeTests(unittest.TestCase):
    def test_explicit_manifest_revision_after_quarantine_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "replace.sqlite")
            engine = Engine(store); recovery = Recovery(engine)
            records = [sample_event(1, "BALANCE_SNAPSHOT", "0", metadata={"opening": True}),
                       sample_event(2, amount="NaN"), sample_event(3, "BALANCE_SNAPSHOT", "10")]
            try:
                self.assertEqual(recovery.run(FakeBinanceSource(with_records(records)))["status"], "incomplete")
                bad = store.rows("SELECT id FROM inbox WHERE status='quarantined'")[0]["id"]
                fixed = engine.replace_quarantined(bad, sample_event(2, amount="10"))
                engine.process(fixed)
                self.assertEqual(recovery.complete("test")["reason"], "MANIFEST_MISMATCH")
                recovery.accept_manifest_revision("test", 2, "synthetic-operator-verified-replacement")
                self.assertEqual(recovery.complete("test")["status"], "complete")
                self.assertEqual(len(store.rows("SELECT * FROM manifest_revisions")), 1)
                self.assertEqual(engine.balance("demo", "SPOT", "USDT")["ledger_balance"], "10")
            finally: store.close()

    def test_pending_before_watermark_completed_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.sqlite"
            store = Store(path); engine = Engine(store)
            opening = sample_event(1, "BALANCE_SNAPSHOT", "0", metadata={"opening": True})
            pending = sample_event(2, amount="10", status="pending")
            for offset, e in enumerate([opening, pending], 1): engine.process(engine.ingest(e, "pending", offset))
            store.close(); store = Store(path); engine = Engine(store)
            try:
                completed = dict(pending, status="completed", version=2)
                engine.process(engine.ingest(completed, "pending", 3))
                self.assertEqual(engine.balance("demo", "SPOT", "USDT")["ledger_balance"], "10")
                self.assertEqual(store.rows("SELECT processed_offset FROM checkpoints")[0]["processed_offset"], 3)
            finally: store.close()

    def test_late_snapshot_does_not_replace_latest_metric(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "metric.sqlite"); engine = Engine(store)
            try:
                for offset, e in enumerate([sample_event(10, "BALANCE_SNAPSHOT", "80", metadata={"metric": "available"}),
                                             sample_event(5, "BALANCE_SNAPSHOT", "50", metadata={"metric": "available"})], 1):
                    engine.process(engine.ingest(e, "metric", offset))
                self.assertEqual(engine.latest_metrics("demo", "SPOT", "USDT")["available"]["amount"], "80")
                self.assertFalse(store.rows("SELECT * FROM ledger"))
            finally: store.close()

    def test_no_financial_reconciliation_without_opening(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "opening.sqlite"); engine = Engine(store)
            try:
                records = [sample_event(1), sample_event(2, "BALANCE_SNAPSHOT", "1")]
                result = Recovery(engine).run(FakeBinanceSource(with_records(records)))
                self.assertEqual(result["reason"], "RECONCILIATION")
                self.assertIsNone(engine.balance("demo", "SPOT", "USDT")["ledger_balance"])
                self.assertEqual(engine.gaps()["reconciliation"][0]["status"], "MISSING_OPENING")
            finally: store.close()
