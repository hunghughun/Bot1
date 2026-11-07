from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol


class DeliveryError(Exception):
    def __init__(self, code: str, retry_after: int = 0) -> None:
        self.code, self.retry_after = code, retry_after
        super().__init__(code)


class Notifier(Protocol):
    def send(self, key: str, payload: dict) -> str: ...


class FakeTelegram:
    def __init__(self, outcomes: list[str] | None = None, sink: str | Path | None = None) -> None:
        self.outcomes = list(outcomes or [])
        self.deliveries: list[dict] = []
        self.sink = Path(sink) if sink is not None else None

    def send(self, key: str, payload: dict) -> str:
        outcome = self.outcomes.pop(0) if self.outcomes else "ok"
        if outcome in {"transient", "rate_limit", "permanent"}:
            raise DeliveryError(outcome, 30 if outcome == "rate_limit" else 0)
        item = {"key": key, "payload": payload, "transport": "FAKE_ONLY"}
        self.deliveries.append(item)
        if self.sink:
            self.sink.parent.mkdir(parents=True, exist_ok=True)
            with self.sink.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(item, sort_keys=True) + "\n")
                handle.flush(); os.fsync(handle.fileno())
        if outcome == "ambiguous":
            raise DeliveryError("ambiguous")
        return "fake:" + key
