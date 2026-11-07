"""Transactional inbox → immutable events → ledger/snapshots/outbox/checkpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from typing import Callable, Any
from uuid import uuid4

from bot1.core.numeric import (NumericError, Aggregate, parse, total, serialize,
                               difference, POLICY)
from bot1.database.store import Store
from bot1.domain.events import Event, EventError, digest, safe_payload, label, gmt7

Fault = Callable[[str], None]
LOG = logging.getLogger("bot1")


def now_ms() -> int:
    delta = datetime.now(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000


def enqueue(db: Any, key: str, payload: dict, clock: int | None = None) -> None:
    db.execute("INSERT OR IGNORE INTO outbox(id,logical_key,payload,enqueued_at) VALUES(?,?,?,?)",
               (str(uuid4()), key, json.dumps(payload, sort_keys=True), now_ms() if clock is None else clock))


class Engine:
    def __init__(self, store: Store, primary_source: str = "fake", fault: Fault | None = None) -> None:
        self.store = store
        self.primary_source = primary_source
        self.fault = fault or (lambda point: None)

    def ingest(self, raw: object, stream: str, offset: int) -> int:
        label(stream, "stream")
        if type(offset) is not int or not 1 <= offset <= 1_000_000_000:
            raise EventError("SOURCE_OFFSET")
        payload = json.dumps(safe_payload(raw), sort_keys=True, allow_nan=False)
        fingerprint = digest(payload)
        with self.store.transaction() as db:
            old = db.execute("SELECT * FROM inbox WHERE stream=? AND offset=? ORDER BY revision DESC", (stream, offset)).fetchall()
            for item in old:
                if item["payload_hash"] == fingerprint:
                    return item["id"]
            if old:
                self._quarantine(db, old[0]["id"], "SOURCE_OFFSET_CONFLICT")
                return old[0]["id"]
            row = db.execute("INSERT INTO inbox(stream,offset,revision,payload,payload_hash) VALUES(?,?,1,?,?)",
                             (stream, offset, payload, fingerprint))
            ident = row.lastrowid
        self.fault("after_inbox_commit")
        return ident

    @staticmethod
    def _health(db: Any, key: str, value: object) -> None:
        db.execute("INSERT INTO system_health(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                   (key, json.dumps(value)))

    def _quarantine(self, db: Any, inbox_id: int, code: str) -> None:
        db.execute("INSERT OR IGNORE INTO quarantine(inbox_id,code) VALUES(?,?)", (inbox_id, code))
        # Do not erase committed financial processing if a later offset conflict arrives.
        db.execute("UPDATE inbox SET status='quarantined' WHERE id=? AND status!='processed'", (inbox_id,))
        enqueue(db, f"quarantine:{inbox_id}:{code}", {"type": "SYSTEM_ERROR", "code": code, "inbox_id": inbox_id})
        self._health(db, "last_error", code)
        db.execute("UPDATE recovery_windows SET status='incomplete',reason='QUARANTINE'")
        db.execute("UPDATE checkpoints SET complete_offset=0")

    def replace_quarantined(self, inbox_id: int, corrected: dict) -> int:
        """Append a revision. Original bytes/quarantine remain until success; no in-place edit."""
        with self.store.transaction() as db:
            row = db.execute("SELECT * FROM inbox WHERE id=? AND active=1 AND status='quarantined'", (inbox_id,)).fetchone()
            if row is None:
                raise EventError("REPLACEMENT_REQUIRES_QUARANTINE")
            payload = json.dumps(safe_payload(corrected), sort_keys=True, allow_nan=False)
            db.execute("UPDATE inbox SET active=0 WHERE id=?", (inbox_id,))
            cursor = db.execute("INSERT INTO inbox(stream,offset,revision,payload,payload_hash) VALUES(?,?,?,?,?)",
                                (row["stream"], row["offset"], row["revision"] + 1, payload, digest(payload)))
            return cursor.lastrowid

    def process(self, inbox_id: int) -> str:
        try:
            with self.store.transaction() as db:
                row = db.execute("SELECT * FROM inbox WHERE id=?", (inbox_id,)).fetchone()
                if row is None:
                    raise EventError("INBOX_NOT_FOUND")
                if not row["active"] or row["status"] == "processed":
                    return "duplicate"
                event = Event.from_dict(json.loads(row["payload"]))
                identity = db.execute("SELECT * FROM identities WHERE identity=?", (event.identity,)).fetchone()
                disposition = "observed"
                if identity:
                    if identity["financial_hash"] != event.financial_hash:
                        raise EventError("IDENTITY_FINANCIAL_CONFLICT")
                    if event.version < identity["latest_version"]:
                        disposition = "stale"
                    elif event.version == identity["latest_version"]:
                        if event.status != identity["latest_status"]:
                            raise EventError("EVENT_VERSION_CONFLICT")
                        disposition = "duplicate"
                    elif identity["latest_status"] != "pending" and event.status != identity["latest_status"]:
                        raise EventError("TERMINAL_STATUS_REQUIRES_CORRECTION")
                if disposition not in ("stale", "duplicate"):
                    db.execute("INSERT INTO identities VALUES(?,?,?,?) ON CONFLICT(identity) DO UPDATE SET latest_version=excluded.latest_version,latest_status=excluded.latest_status",
                               (event.identity, event.financial_hash, event.version, event.status))
                eid = str(uuid4())
                db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (eid, inbox_id, event.identity, event.economic_key, event.financial_hash,
                            event.source, event.source_event_id, event.account, event.wallet,
                            event.asset, serialize(event.amount), event.event_type, event.event_time,
                            event.received_time, event.status, event.version, 1,
                            json.dumps(event.metadata, sort_keys=True), event.evidence, disposition))
                self.fault("after_event_insert")
                if disposition not in ("stale", "duplicate") and event.status in ("completed", "correction"):
                    economic = db.execute("SELECT * FROM economic_events WHERE economic_key=?", (event.economic_key,)).fetchone()
                    if economic and economic["financial_hash"] != event.financial_hash:
                        raise EventError("ECONOMIC_FINANCIAL_CONFLICT")
                    if event.source != self.primary_source and not economic:
                        raise EventError("UNVERIFIED_SECONDARY_SOURCE")
                    if not economic:
                        self._apply(db, event, eid)
                        db.execute("INSERT INTO economic_events VALUES(?,?,?)", (event.economic_key, event.financial_hash, eid))
                self.fault("after_ledger")
                self._reconcile(db)
                self.fault("after_outbox")
                db.execute("UPDATE inbox SET status='processed',event_id=? WHERE id=?", (eid, inbox_id))
                # Resolve only quarantines for the same logical cursor after successful replay.
                db.execute("UPDATE quarantine SET resolved=1 WHERE inbox_id IN (SELECT id FROM inbox WHERE stream=? AND offset=?) AND code!='SOURCE_OFFSET_CONFLICT'", (row["stream"], row["offset"]))
                self._advance(db, row["stream"])
                self._health(db, "last_commit_ms", now_ms())
                self._health(db, "state", "RUNNING")
                self.fault("before_commit")
            self.fault("after_commit")
            LOG.info("event_processed", extra={"event_id": eid, "code": disposition})
            return disposition
        except (NumericError, EventError) as exc:
            code = str(exc)
            if code == "INBOX_NOT_FOUND":
                raise
            with self.store.transaction() as db:
                self._quarantine(db, inbox_id, code)
            LOG.warning("event_quarantined", extra={"inbox_id": inbox_id, "code": code})
            return "quarantined"

    def _apply(self, db: Any, event: Event, eid: str) -> None:
        if event.event_type in {"BALANCE_SNAPSHOT", "UNREALIZED_PNL_SNAPSHOT"}:
            metric = "unrealized" if event.event_type == "UNREALIZED_PNL_SNAPSHOT" else event.metadata.get("metric", "wallet")
            opening = event.metadata.get("opening", False)
            previous = db.execute("SELECT amount FROM snapshots WHERE account=? AND wallet=? AND asset=? AND metric=? AND event_time=?", (event.account, event.wallet, event.asset, metric, event.event_time)).fetchall()
            if any(Decimal(item["amount"]) != event.amount for item in previous):
                raise EventError("SNAPSHOT_CONFLICT")
            if opening:
                if db.execute("SELECT 1 FROM openings WHERE account=? AND wallet=? AND asset=?", (event.account, event.wallet, event.asset)).fetchone():
                    raise EventError("OPENING_ALREADY_DEFINED")
                if db.execute("SELECT 1 FROM ledger WHERE account=? AND wallet=? AND asset=? AND event_time<=?", (event.account, event.wallet, event.asset, event.event_time)).fetchone():
                    raise EventError("OPENING_OVERLAPS_POSTED_HISTORY")
                db.execute("INSERT INTO openings VALUES(?,?,?,?,?,?)", (event.account, event.wallet, event.asset, eid, serialize(event.amount), event.event_time))
            db.execute("INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?)", (eid, event.account, event.wallet, event.asset, metric, serialize(event.amount), event.event_time, int(opening)))
            return
        if event.status == "correction":
            target = db.execute("SELECT * FROM events WHERE id=?", (event.metadata["reverses"],)).fetchone()
            legs = db.execute("SELECT * FROM ledger WHERE event_id=? ORDER BY leg", (event.metadata["reverses"],)).fetchall()
            if not target or not legs or (target["account"], target["wallet"], target["asset"]) != (event.account, event.wallet, event.asset):
                raise EventError("CORRECTION_TARGET")
            if db.execute("SELECT 1 FROM reversals WHERE target_event_id=?", (target["id"],)).fetchone():
                raise EventError("ALREADY_REVERSED")
            if event.amount != Decimal(target["amount"]).copy_negate() or event.event_time < target["event_time"]:
                raise EventError("CORRECTION_AMOUNT_OR_TIME")
            db.execute("INSERT INTO reversals VALUES(?,?)", (target["id"], eid))
            postings = [(leg["wallet"], Decimal(leg["amount"]).copy_negate()) for leg in legs]
        elif event.event_type == "INTERNAL_TRANSFER":
            postings = [(event.wallet, event.amount.copy_negate()), (event.metadata["to_wallet"], event.amount)]
        else:
            amount = event.amount.copy_negate() if event.event_type == "WITHDRAWAL" else event.amount
            postings = [(event.wallet, amount)]
        changes = []
        for index, (wallet, amount) in enumerate(postings):
            opening = db.execute("SELECT cutoff FROM openings WHERE account=? AND wallet=? AND asset=?", (event.account, wallet, event.asset)).fetchone()
            if opening and event.event_time <= opening["cutoff"]:
                # Baseline covers this leg already. Preserve event but do not add money twice.
                continue
            category = legs[index]["kind"] if event.status == "correction" else event.event_type
            db.execute("INSERT INTO ledger(event_id,economic_key,leg,account,wallet,asset,amount,kind,event_time,policy) VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (eid, event.economic_key, index, event.account, wallet, event.asset, serialize(amount), category, event.event_time, POLICY))
            self._projection(db, event.account, wallet, event.asset)
            changes.append({"wallet": wallet, "asset": event.asset, "ledger_delta": serialize(amount)})
        enqueue(db, f"economic:{event.economic_key}", {"type": event.event_type, "event_id": eid,
                "account": event.account, "wallet": event.wallet, "asset": event.asset,
                "amount": serialize(event.amount), "status": event.status, "event_time": event.event_time,
                "event_time_gmt7": gmt7(event.event_time), "balance_changes": changes,
                "balance_kind": "PROJECTED_LEDGER_CASHFLOW", "historical_only": not bool(changes)})

    @staticmethod
    def _projection(db: Any, account: str, wallet: str, asset: str, at: str | None = None) -> Aggregate | None:
        opening = db.execute("SELECT * FROM openings WHERE account=? AND wallet=? AND asset=?", (account, wallet, asset)).fetchone()
        if not opening or (at is not None and at < opening["cutoff"]):
            return None
        sql = "SELECT amount FROM ledger WHERE account=? AND wallet=? AND asset=? AND event_time>?"
        args: tuple = (account, wallet, asset, opening["cutoff"])
        if at is not None:
            sql += " AND event_time<=?"; args += (at,)
        values = [parse(opening["amount"])]
        values.extend(Decimal(row["amount"]) for row in db.execute(sql, args))
        return total(values)

    def _reconcile(self, db: Any) -> None:
        for snap in db.execute("SELECT * FROM snapshots WHERE metric='wallet' AND opening=0").fetchall():
            previous = db.execute("SELECT status,residual FROM reconciliations WHERE snapshot_id=?", (snap["event_id"],)).fetchone()
            expected = self._projection(db, snap["account"], snap["wallet"], snap["asset"], snap["event_time"])
            residual = None if expected is None else difference(Aggregate(parse(snap["amount"]), 1), expected).value
            status = "MISSING_OPENING" if expected is None else "MATCH" if residual == 0 else "UNKNOWN_BALANCE_CHANGE"
            if status != "MATCH":
                db.execute("UPDATE recovery_windows SET status='incomplete',reason='RECONCILIATION'")
                db.execute("UPDATE checkpoints SET complete_offset=0")
            db.execute("INSERT INTO reconciliations VALUES(?,?,?,?,?) ON CONFLICT(snapshot_id) DO UPDATE SET expected=excluded.expected,residual=excluded.residual,status=excluded.status",
                       (snap["event_id"], None if expected is None else serialize(expected.value), snap["amount"], None if residual is None else serialize(residual), status))
            residual_text = None if residual is None else serialize(residual)
            if previous is None or (previous["status"], previous["residual"]) != (status, residual_text):
                key = "internal.reconciliation_revision." + snap["event_id"]
                revision = db.execute("SELECT value FROM system_health WHERE key=?", (key,)).fetchone()
                version = 1 if revision is None else json.loads(revision["value"]) + 1
                self._health(db, key, version)
                if status != "MATCH" or (previous is not None and previous["status"] != "MATCH"):
                    enqueue(db, f"reconciliation:{snap['event_id']}:{version}", {
                        "type": status if status != "MATCH" else "RECONCILIATION_RESOLVED",
                        "snapshot_id": snap["event_id"], "account": snap["account"],
                        "wallet": snap["wallet"], "asset": snap["asset"], "status": status,
                        "snapshot_time": snap["event_time"], "observed": snap["amount"],
                        "expected": None if expected is None else serialize(expected.value),
                        "residual": residual_text, "revision": version})

    @staticmethod
    def _advance(db: Any, stream: str) -> None:
        db.execute("INSERT OR IGNORE INTO checkpoints(stream) VALUES(?)", (stream,))
        offset = db.execute("SELECT processed_offset FROM checkpoints WHERE stream=?", (stream,)).fetchone()[0]
        while db.execute("SELECT 1 FROM inbox WHERE stream=? AND offset=? AND active=1 AND status='processed'", (stream, offset + 1)).fetchone():
            offset += 1
        db.execute("UPDATE checkpoints SET processed_offset=? WHERE stream=?", (offset, stream))

    def balance(self, account: str, wallet: str, asset: str) -> dict[str, Any]:
        aggregate = self._projection(self.store.connection, account, wallet, asset)
        observed = self.store.rows("SELECT amount,event_time,metric FROM snapshots WHERE account=? AND wallet=? AND asset=? AND metric='wallet' ORDER BY event_time DESC,event_id DESC LIMIT 1", (account, wallet, asset))
        return {"account": account, "wallet": wallet, "asset": asset,
                "ledger_balance": None if aggregate is None else serialize(aggregate.value),
                "leaf_terms": None if aggregate is None else aggregate.terms,
                "latest_observed": observed[0] if observed else None,
                "metrics": self.latest_metrics(account, wallet, asset),
                "data_status": "MISSING_OPENING" if aggregate is None else "PROJECTED"}

    def latest_metrics(self, account: str, wallet: str, asset: str) -> dict[str, Any]:
        result = {}
        for row in self.store.rows("SELECT metric,amount,event_time FROM snapshots WHERE account=? AND wallet=? AND asset=? ORDER BY event_time,event_id", (account, wallet, asset)):
            result[row["metric"]] = {"amount": row["amount"], "event_time": row["event_time"]}
        return result

    def summaries(self, account: str) -> list[dict[str, Any]]:
        # Asset and wallet are never implicitly summed into a USDT portfolio value.
        groups = self.store.rows("SELECT DISTINCT wallet,asset,kind FROM ledger WHERE account=? ORDER BY wallet,asset,kind", (account,))
        for group in groups:
            amounts = self.store.rows("SELECT amount FROM ledger WHERE account=? AND wallet=? AND asset=? AND kind=?", (account, group["wallet"], group["asset"], group["kind"]))
            group["net_amount"] = serialize(total(Decimal(r["amount"]) for r in amounts).value)
            group["credits"] = serialize(total(Decimal(r["amount"]) for r in amounts if Decimal(r["amount"]) > 0).value)
            group["debits"] = serialize(total(Decimal(r["amount"]) for r in amounts if Decimal(r["amount"]) < 0).value)
        return groups

    def gaps(self) -> dict[str, Any]:
        reconciliation = self.store.rows("SELECT * FROM reconciliations WHERE status!='MATCH'")
        # A missing baseline is already a data gap even before a snapshot arrives.
        missing = self.store.rows("SELECT DISTINCT l.account,l.wallet,l.asset FROM ledger l LEFT JOIN openings o ON o.account=l.account AND o.wallet=l.wallet AND o.asset=l.asset WHERE o.account IS NULL AND NOT EXISTS (SELECT 1 FROM snapshots s WHERE s.account=l.account AND s.wallet=l.wallet AND s.asset=l.asset AND s.metric='wallet' AND s.opening=0)")
        reconciliation.extend({**scope, "status": "MISSING_OPENING", "expected": None, "observed": None, "residual": None} for scope in missing)
        return {"quarantine": self.store.rows("SELECT * FROM quarantine WHERE resolved=0"),
                "reconciliation": reconciliation,
                "windows": self.store.rows("SELECT * FROM recovery_windows WHERE status!='complete'")}
