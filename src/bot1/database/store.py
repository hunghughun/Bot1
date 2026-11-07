from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator, Any


class DatabaseBusy(RuntimeError):
    pass


SCHEMA = """
CREATE TABLE inbox(id INTEGER PRIMARY KEY, stream TEXT NOT NULL, offset INTEGER NOT NULL,
 revision INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1, payload TEXT NOT NULL,
 payload_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', event_id TEXT,
 UNIQUE(stream,offset,revision));
CREATE UNIQUE INDEX inbox_active ON inbox(stream,offset) WHERE active=1;
CREATE TABLE identities(identity TEXT PRIMARY KEY, financial_hash TEXT NOT NULL,
 latest_version INTEGER NOT NULL, latest_status TEXT NOT NULL);
CREATE TABLE events(id TEXT PRIMARY KEY, inbox_id INTEGER UNIQUE REFERENCES inbox(id),
 identity TEXT NOT NULL, economic_key TEXT NOT NULL, financial_hash TEXT NOT NULL,
 source TEXT NOT NULL, source_id TEXT NOT NULL, account TEXT NOT NULL, wallet TEXT NOT NULL,
 asset TEXT NOT NULL, amount TEXT NOT NULL, kind TEXT NOT NULL, event_time TEXT NOT NULL,
 received_time TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL,
 schema_version INTEGER NOT NULL, metadata TEXT NOT NULL, evidence TEXT NOT NULL,
 disposition TEXT NOT NULL);
CREATE TABLE economic_events(economic_key TEXT PRIMARY KEY, financial_hash TEXT NOT NULL,
 event_id TEXT NOT NULL REFERENCES events(id));
CREATE TABLE ledger(id INTEGER PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id),
 economic_key TEXT NOT NULL, leg INTEGER NOT NULL, account TEXT NOT NULL, wallet TEXT NOT NULL,
 asset TEXT NOT NULL, amount TEXT NOT NULL, kind TEXT NOT NULL, event_time TEXT NOT NULL,
 policy TEXT NOT NULL, UNIQUE(economic_key,leg));
CREATE TABLE reversals(target_event_id TEXT PRIMARY KEY REFERENCES events(id),
 correction_event_id TEXT UNIQUE NOT NULL REFERENCES events(id));
CREATE TABLE openings(account TEXT NOT NULL, wallet TEXT NOT NULL, asset TEXT NOT NULL,
 event_id TEXT NOT NULL REFERENCES events(id), amount TEXT NOT NULL, cutoff TEXT NOT NULL,
 PRIMARY KEY(account,wallet,asset));
CREATE TABLE snapshots(event_id TEXT PRIMARY KEY REFERENCES events(id), account TEXT NOT NULL,
 wallet TEXT NOT NULL, asset TEXT NOT NULL, metric TEXT NOT NULL, amount TEXT NOT NULL,
 event_time TEXT NOT NULL, opening INTEGER NOT NULL);
CREATE TABLE reconciliations(snapshot_id TEXT PRIMARY KEY REFERENCES snapshots(event_id),
 expected TEXT, observed TEXT NOT NULL, residual TEXT, status TEXT NOT NULL);
CREATE TABLE outbox(id TEXT PRIMARY KEY, logical_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
 next_attempt INTEGER NOT NULL DEFAULT 0, lease_owner TEXT, lease_until INTEGER,
 receipt TEXT, error TEXT, enqueued_at INTEGER NOT NULL, ack_at INTEGER);
CREATE TABLE checkpoints(stream TEXT PRIMARY KEY, processed_offset INTEGER NOT NULL DEFAULT 0,
 complete_offset INTEGER NOT NULL DEFAULT 0);
CREATE TABLE quarantine(id INTEGER PRIMARY KEY, inbox_id INTEGER REFERENCES inbox(id),
 code TEXT NOT NULL, resolved INTEGER NOT NULL DEFAULT 0, UNIQUE(inbox_id,code));
CREATE TABLE recovery_windows(stream TEXT PRIMARY KEY, expected_end INTEGER NOT NULL,
 status TEXT NOT NULL, reason TEXT NOT NULL);
CREATE TABLE recovery_members(stream TEXT NOT NULL, offset INTEGER NOT NULL,
 expected_hash TEXT NOT NULL, PRIMARY KEY(stream,offset));
CREATE TABLE manifest_revisions(id INTEGER PRIMARY KEY, stream TEXT NOT NULL, offset INTEGER NOT NULL,
 old_hash TEXT NOT NULL,new_hash TEXT NOT NULL,evidence TEXT NOT NULL);
CREATE TABLE system_health(key TEXT PRIMARY KEY, value TEXT NOT NULL);
PRAGMA user_version=1;
"""


class Store:
    """Repository boundary: business logic never relies on SQLite REAL or SQL SUM."""

    def __init__(self, path: str | Path, timeout_ms: int = 100) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, isolation_level=None, timeout=timeout_ms / 1000)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.close()
            raise RuntimeError("DB_SCHEMA_VERSION")
        if version == 0:
            self.connection.executescript("BEGIN IMMEDIATE;" + SCHEMA + "COMMIT;")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            yield self.connection
            self.connection.execute("COMMIT")
        except BaseException as exc:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            if isinstance(exc, sqlite3.OperationalError) and any(x in str(exc).lower() for x in ("locked", "busy")):
                raise DatabaseBusy("DB_BUSY_RETRY") from None
            raise

    def rows(self, sql: str, args: tuple = ()) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(sql, args)]

    def close(self) -> None:
        self.connection.close()

    def backup(self, destination: str | Path) -> None:
        if self.path != ":memory:" and Path(destination).resolve() == Path(self.path).resolve():
            raise ValueError("BACKUP_SAME_PATH")
        with sqlite3.connect(str(destination)) as target:
            self.connection.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("BACKUP_INTEGRITY")
