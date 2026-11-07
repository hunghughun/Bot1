from __future__ import annotations

import json
from typing import Any

from bot1.ledger.engine import Engine, enqueue
from bot1.sources.fake import EventSource, SourceDisconnected


class Recovery:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def replay_pending(self) -> int:
        rows = self.engine.store.rows("SELECT id FROM inbox WHERE active=1 AND status!='processed' ORDER BY stream,offset")
        for row in rows:
            self.engine.process(row["id"])
        return len(rows)

    def run(self, source: EventSource) -> dict[str, Any]:
        dbstore = self.engine.store
        with dbstore.transaction() as db:
            previous = db.execute("SELECT expected_end FROM recovery_windows WHERE stream=?", (source.stream,)).fetchone()
            if previous and source.expected_end < previous["expected_end"]:
                raise ValueError("HISTORY_MANIFEST_TRUNCATED")
            old_members = {r["offset"]: r["expected_hash"] for r in db.execute("SELECT * FROM recovery_members WHERE stream=?", (source.stream,))}
            if any(k in source.expected_manifest and source.expected_manifest[k] != v for k, v in old_members.items()):
                raise ValueError("HISTORY_MANIFEST_CONFLICT")
            db.execute("INSERT INTO recovery_windows VALUES(?,?,'syncing','REPLAY') ON CONFLICT(stream) DO UPDATE SET expected_end=excluded.expected_end,status='syncing',reason='REPLAY'",
                       (source.stream, source.expected_end))
            for offset, fingerprint in source.expected_manifest.items():
                if type(offset) is not int or not 1 <= offset <= source.expected_end:
                    raise ValueError("HISTORY_MANIFEST_OFFSET")
                db.execute("INSERT OR IGNORE INTO recovery_members VALUES(?,?,?)", (source.stream, offset, fingerprint))
        try:
            for offset, event in source.history():
                if offset > source.expected_end:
                    raise ValueError("HISTORY_OFFSET_OUTSIDE_MANIFEST")
                self.engine.process(self.engine.ingest(event, source.stream, offset))
            self.replay_pending()
        except SourceDisconnected:
            with dbstore.transaction() as db:
                db.execute("UPDATE recovery_windows SET status='incomplete',reason='SOURCE_DISCONNECTED' WHERE stream=?", (source.stream,))
                self.engine._health(db, "state", "DEGRADED")
                enqueue(db, f"disconnect:{source.stream}:{source.expected_end}", {"type": "SOURCE_DISCONNECTED", "stream": source.stream})
            return {"status": "incomplete", "reason": "SOURCE_DISCONNECTED"}
        return self.complete(source.stream)

    def accept_manifest_revision(self, stream: str, offset: int, evidence: str) -> None:
        """Explicit operator action after verified replacement; retains old/new hashes."""
        if not isinstance(evidence, str) or not 1 <= len(evidence) <= 256:
            raise ValueError("MANIFEST_REVISION_EVIDENCE")
        with self.engine.store.transaction() as db:
            old = db.execute("SELECT expected_hash FROM recovery_members WHERE stream=? AND offset=?", (stream, offset)).fetchone()
            active = db.execute("SELECT payload_hash,revision FROM inbox WHERE stream=? AND offset=? AND active=1 AND status='processed'", (stream, offset)).fetchone()
            if not old or not active or active["revision"] < 2:
                raise ValueError("MANIFEST_REQUIRES_PROCESSED_REPLACEMENT")
            db.execute("INSERT INTO manifest_revisions(stream,offset,old_hash,new_hash,evidence) VALUES(?,?,?,?,?)", (stream, offset, old["expected_hash"], active["payload_hash"], evidence))
            db.execute("UPDATE recovery_members SET expected_hash=? WHERE stream=? AND offset=?", (active["payload_hash"], stream, offset))

    def complete(self, stream: str) -> dict[str, Any]:
        with self.engine.store.transaction() as db:
            window = db.execute("SELECT * FROM recovery_windows WHERE stream=?", (stream,)).fetchone()
            if window is None:
                raise ValueError("WINDOW_NOT_FOUND")
            processed = db.execute("SELECT count(*) FROM inbox WHERE stream=? AND active=1 AND status='processed' AND offset<=?", (stream, window["expected_end"])).fetchone()[0]
            quarantine = db.execute("SELECT count(*) FROM quarantine WHERE resolved=0").fetchone()[0]
            residual = db.execute("SELECT count(*) FROM reconciliations WHERE status!='MATCH'").fetchone()[0]
            members = db.execute("SELECT count(*) FROM recovery_members m JOIN inbox i ON i.stream=m.stream AND i.offset=m.offset AND i.payload_hash=m.expected_hash AND i.active=1 AND i.status='processed' WHERE m.stream=? AND m.offset<=?", (stream, window["expected_end"])).fetchone()[0]
            coverage = True
            for group in db.execute("SELECT account,wallet,asset,max(event_time) AS last_time FROM ledger GROUP BY account,wallet,asset").fetchall():
                match = db.execute("SELECT 1 FROM snapshots s JOIN reconciliations r ON r.snapshot_id=s.event_id WHERE s.account=? AND s.wallet=? AND s.asset=? AND s.event_time>=? AND r.status='MATCH'", (group["account"], group["wallet"], group["asset"], group["last_time"])).fetchone()
                coverage = coverage and match is not None
            reason = ("MISSING_OFFSETS" if processed != window["expected_end"] else "MANIFEST_MISMATCH" if members != window["expected_end"] else "QUARANTINE" if quarantine else "RECONCILIATION" if residual or not coverage else "VERIFIED_FAKE_MANIFEST")
            status = "complete" if reason == "VERIFIED_FAKE_MANIFEST" else "incomplete"
            db.execute("UPDATE recovery_windows SET status=?,reason=? WHERE stream=?", (status, reason, stream))
            if status == "complete":
                db.execute("UPDATE checkpoints SET complete_offset=? WHERE stream=?", (window["expected_end"], stream))
                self.engine._health(db, "state", "SYNCED_OFFLINE")
                enqueue(db, f"restored:{stream}:{window['expected_end']}", {"type": "HISTORY_RECONCILED", "stream": stream})
            else:
                db.execute("UPDATE checkpoints SET complete_offset=0 WHERE stream=?", (stream,))
            return {"status": status, "reason": reason, "expected_end": window["expected_end"], "processed": processed}
