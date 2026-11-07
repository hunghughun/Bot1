from __future__ import annotations

import json
from typing import Callable
from uuid import uuid4

from bot1.database.store import Store
from bot1.ledger.engine import now_ms
from bot1.notifications.fake import Notifier, DeliveryError


class Outbox:
    def __init__(self, store: Store, notifier: Notifier, clock: Callable[[], int] = now_ms,
                 fault: Callable[[str], None] | None = None) -> None:
        self.store, self.notifier, self.clock = store, notifier, clock
        self.fault = fault or (lambda point: None)

    def send_one(self) -> bool:
        now, owner = self.clock(), str(uuid4())
        with self.store.transaction() as db:
            # Expired send leases are ambiguous: never automatically resend them.
            db.execute("UPDATE outbox SET status='ambiguous',error='LEASE_EXPIRED_DELIVERY_UNKNOWN' WHERE status='inflight' AND lease_until<=?", (now,))
            row = db.execute("SELECT * FROM outbox WHERE status IN ('pending','retry') AND next_attempt<=? ORDER BY enqueued_at,id LIMIT 1", (now,)).fetchone()
            if row is None:
                return False
            db.execute("UPDATE outbox SET status='inflight',lease_owner=?,lease_until=?,attempts=attempts+1 WHERE id=?", (owner, now + 60_000, row["id"]))
        self.fault("after_claim")
        receipt = None
        try:
            receipt = self.notifier.send(row["logical_key"], json.loads(row["payload"]))
            self.fault("after_send")
            status, error, delay = "sent", None, 0
        except DeliveryError as exc:
            error = exc.code if exc.code in {"transient", "rate_limit", "permanent", "ambiguous"} else "TRANSPORT_ERROR"
            status = "ambiguous" if error == "ambiguous" else "dead" if error == "permanent" or row["attempts"] + 1 >= 5 else "retry"
            delay = max(exc.retry_after * 1000, min(60_000, 1000 * 2 ** row["attempts"]))
        with self.store.transaction() as db:
            changed = db.execute("UPDATE outbox SET status=?,receipt=?,error=?,next_attempt=?,ack_at=? WHERE id=? AND status='inflight' AND lease_owner=?",
                                (status, receipt, error, self.clock() + delay, self.clock() if status == "sent" else None, row["id"], owner)).rowcount
            if changed != 1:
                raise RuntimeError("OUTBOX_LEASE_LOST")
        return True

    def drain(self, limit: int = 1000) -> int:
        count = 0
        while count < limit and self.send_one():
            count += 1
        return count
