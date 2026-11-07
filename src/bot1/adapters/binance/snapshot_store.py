"""Isolated offline snapshot experiment. No ledger, outbox, credential or transport.

Durable poll IDs are supplied by the caller before acquisition. Re-delivery of
the same poll must use the same bytes. A changed body under that ID quarantines
the entire delivery; partial rows are never committed. No Binance cursor claims.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from bot1.adapters.binance.balance import BalanceContext, BalanceError, map_balance, validate_balance
from bot1.adapters.binance.parsing import RestResponseParser

APPLICATION_ID = 1111577427
TABLES = {"bindings", "deliveries", "observations", "rejections"}


class SnapshotSandbox:
    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), isolation_level=None)
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        app = self.db.execute("PRAGMA application_id").fetchone()[0]
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if (tables and (tables != TABLES or app != APPLICATION_ID or version != 1)
                or not tables and (app != 0 or version != 0)):
            self.db.close()
            raise BalanceError("NOT_A_SNAPSHOT_SANDBOX_DATABASE")
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS bindings(account TEXT PRIMARY KEY, alias TEXT UNIQUE NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS deliveries(account TEXT, poll_id TEXT, body_sha256 TEXT NOT NULL, received_time TEXT NOT NULL, PRIMARY KEY(account,poll_id))")
            self.db.execute("CREATE TABLE IF NOT EXISTS observations(source_event_id TEXT PRIMARY KEY, account TEXT NOT NULL, poll_id TEXT NOT NULL, event_json TEXT NOT NULL, sdk_row_json TEXT NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS rejections(body_sha256 TEXT NOT NULL, code TEXT NOT NULL, received_time TEXT NOT NULL, PRIMARY KEY(body_sha256,code))")
            self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            self.db.execute("PRAGMA user_version=1")

    def ingest(self, payload: bytes, context: BalanceContext, *, contract_id="futures_balance_v3", fault=None) -> tuple[dict, ...]:
        if type(payload) is not bytes or not isinstance(context, BalanceContext):
            raise BalanceError("SNAPSHOT_INPUT_TYPES")
        body_hash = hashlib.sha256(payload).hexdigest()
        try:
            frame = RestResponseParser().parse(payload, contract_id)
            events = map_balance(frame, context)
            rows = {row["asset"]: row for row in validate_balance(frame, context)}
            self.db.execute("BEGIN IMMEDIATE")
            try:
                existing = self.db.execute("SELECT alias FROM bindings WHERE account=?", (context.account,)).fetchone()
                other = self.db.execute("SELECT account FROM bindings WHERE alias=?", (context.expected_account_alias,)).fetchone()
                if ((existing and existing[0] != context.expected_account_alias)
                        or (other and other[0] != context.account)):
                    raise BalanceError("SNAPSHOT_ACCOUNT_BINDING_CONFLICT")
                delivery = self.db.execute("SELECT body_sha256 FROM deliveries WHERE account=? AND poll_id=?", (context.account, context.poll_id)).fetchone()
                if delivery:
                    if delivery[0] != body_hash:
                        raise BalanceError("SNAPSHOT_POLL_BODY_CONFLICT")
                    original = self.db.execute("SELECT event_json FROM observations WHERE account=? AND poll_id=? ORDER BY source_event_id", (context.account, context.poll_id)).fetchall()
                    self.db.execute("COMMIT")
                    return tuple(json.loads(row[0]) for row in original)
                self.db.execute("INSERT OR IGNORE INTO bindings VALUES(?,?)", (context.account, context.expected_account_alias))
                self.db.execute("INSERT INTO deliveries VALUES(?,?,?,?)", (context.account, context.poll_id, body_hash, context.received_time))
                for event in events:
                    self.db.execute("INSERT INTO observations VALUES(?,?,?,?,?)", (
                        event["source_event_id"], context.account, context.poll_id,
                        json.dumps(event, sort_keys=True), json.dumps(rows[event["asset"]], sort_keys=True)))
                if fault:
                    fault("before_commit")
                self.db.execute("COMMIT")
            except BaseException:
                if self.db.in_transaction:
                    self.db.execute("ROLLBACK")
                raise
            if fault:
                fault("after_commit")
            return events
        except ValueError as exc:
            # Validation/conflict audit survives rollback; never retain raw inputs.
            code = str(exc)
            if re.fullmatch(r"[A-Z0-9_]{1,80}", code, re.ASCII) is None:
                code = "SNAPSHOT_REJECTED"
            self.db.execute("INSERT OR IGNORE INTO rejections VALUES(?,?,?)", (
                body_hash, code, datetime.now(timezone.utc).isoformat()))
            raise

    def observations(self) -> tuple[dict, ...]:
        return tuple(json.loads(r[0]) for r in self.db.execute("SELECT event_json FROM observations ORDER BY source_event_id"))

    def close(self) -> None:
        self.db.close()
