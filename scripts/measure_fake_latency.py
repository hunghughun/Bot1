"""Local ingest→fake ack benchmark, never a Telegram latency claim."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bot1.database.store import Store
from bot1.ledger.engine import Engine
from bot1.notifications.fake import FakeTelegram
from bot1.notifications.outbox import Outbox
from bot1.sources.fake import sample_event


def main() -> None:
    durations = []
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "latency.sqlite")
        try:
            engine = Engine(store)
            base = sample_event(1, "BALANCE_SNAPSHOT", "0", metadata={"opening": True})
            engine.process(engine.ingest(base, "latency", 1))
            fake = FakeTelegram(); sender = Outbox(store, fake)
            for i in range(1000):
                event = sample_event(i + 10, amount="0.1", received_time=datetime.now(timezone.utc).isoformat())
                start = perf_counter_ns()
                engine.process(engine.ingest(event, "latency", i + 2))
                if not sender.send_one(): raise RuntimeError("BENCH_NO_NOTIFICATION")
                durations.append(perf_counter_ns() - start)
            if len(fake.deliveries) != 1000 or engine.balance("demo", "SPOT", "USDT")["ledger_balance"] != "100":
                raise RuntimeError("BENCH_INVARIANT")
        finally: store.close()
    values = sorted(durations)
    result = {"samples": len(values), "scope": "local internal-event ingestion through SQLite to fake ack; not Telegram/network/source latency",
              "unit": "nanoseconds", "clock": "perf_counter_ns", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "p50": values[499], "p95": values[949], "p99": values[989], "max": values[-1],
              "deliveries": 1000, "expected_balance": "100", "status": "PASS_FUNCTIONAL_INVARIANTS",
              "real_telegram": "NOT TESTED", "samples_ns": durations}
    target = ROOT / "docs/test-reports/fake-latency.json"
    target.parent.mkdir(exist_ok=True, parents=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "samples_ns"}))


if __name__ == "__main__":
    main()
