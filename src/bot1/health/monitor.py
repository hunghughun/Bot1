from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

from bot1.database.store import Store
from bot1.ledger.engine import now_ms


class SafeJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Deliberately no exception text, arbitrary message interpolation or raw payload.
        return json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(),
                           "level": record.levelname, "component": record.name,
                           "action": record.msg if record.msg in {"event_processed", "event_quarantined"} else "diagnostic",
                           **{k: getattr(record, k) for k in ("event_id", "inbox_id", "code") if hasattr(record, k)}})


class Health:
    def __init__(self, store: Store) -> None:
        self.store = store

    def snapshot(self, at_ms: int | None = None) -> dict[str, Any]:
        at_ms = now_ms() if at_ms is None else at_ms
        result: dict[str, Any] = {r["key"]: json.loads(r["value"]) for r in self.store.rows("SELECT * FROM system_health") if not r["key"].startswith("internal.")}
        result["database"] = self.store.connection.execute("PRAGMA quick_check").fetchone()[0]
        for name, sql in {
            "processed": "SELECT count(*) FROM inbox WHERE status='processed'",
            "pending": "SELECT count(*) FROM inbox WHERE active=1 AND status='pending'",
            "quarantine": "SELECT count(*) FROM quarantine WHERE resolved=0",
            "reconciliation_gap": "SELECT count(*) FROM reconciliations WHERE status!='MATCH'",
            "history_gap": "SELECT count(*) FROM recovery_windows WHERE status!='complete'",
            "notification_backlog": "SELECT count(*) FROM outbox WHERE status!='sent'",
            "notification_retries": "SELECT coalesce(sum(CASE WHEN attempts>1 THEN attempts-1 ELSE 0 END),0) FROM outbox",
            "event_failures": "SELECT count(*) FROM quarantine",
            "missing_openings": "SELECT count(*) FROM (SELECT DISTINCT l.account,l.wallet,l.asset FROM ledger l LEFT JOIN openings o ON o.account=l.account AND o.wallet=l.wallet AND o.asset=l.asset WHERE o.account IS NULL)",
        }.items():
            result[name] = self.store.connection.execute(sql).fetchone()[0]
        result["notifier_statuses"] = self.store.rows("SELECT status,count(*) AS count FROM outbox GROUP BY status")
        result["heartbeat_age_ms"] = None if "last_commit_ms" not in result else max(0, at_ms - result["last_commit_ms"])
        times = self.store.rows("SELECT e.received_time FROM events e JOIN inbox i ON e.inbox_id=i.id WHERE i.active=1 ORDER BY e.received_time DESC LIMIT 1")
        result["latest_received_time"] = times[0]["received_time"] if times else None
        if times:
            delta = datetime.fromisoformat(times[0]["received_time"]) - datetime(1970, 1, 1, tzinfo=timezone.utc)
            result["processing_lag_ms"] = max(0, at_ms - (delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000))
        else:
            result["processing_lag_ms"] = None
        result["network"] = "OFFLINE_ONLY"
        return result
