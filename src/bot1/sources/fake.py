"""Synthetic internal-schema history. Never a Binance REST/WebSocket client."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import time
from pathlib import Path
from typing import Iterator, Protocol, Callable

from bot1.domain.events import digest, safe_payload


class SourceDisconnected(RuntimeError):
    pass


class EventSource(Protocol):
    stream: str
    expected_end: int
    expected_manifest: dict[int, str]

    def history(self) -> Iterator[tuple[int, dict]]: ...


def sample_event(index: int, kind: str = "DEPOSIT", amount: str = "1", **overrides: object) -> dict:
    stamp = (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=index)).isoformat()
    result = {"source": "fake", "source_event_id": f"synthetic-{index}", "id_trusted": True,
              "account": "demo", "wallet": "SPOT", "asset": "USDT", "amount": amount,
              "event_type": kind, "event_time": stamp, "received_time": stamp,
              "status": "completed", "version": 1, "schema_version": 1,
              "metadata": {}, "evidence": "synthetic-fixture-not-binance"}
    result.update(overrides)
    return result


def scenario() -> dict:
    events = [
        sample_event(1, "BALANCE_SNAPSHOT", "0", metadata={"opening": True}),
        sample_event(2, "BALANCE_SNAPSHOT", "0", wallet="FUTURES", metadata={"opening": True}),
        sample_event(3, "DEPOSIT", "100"),
        sample_event(4, "INTERNAL_TRANSFER", "100", metadata={"to_wallet": "FUTURES"}),
        sample_event(5, "REALIZED_PNL", "8", wallet="FUTURES"),
        sample_event(6, "TRADING_FEE", "-1", wallet="FUTURES"),
        sample_event(7, "FUNDING_FEE", "-0.5", wallet="FUTURES"),
        sample_event(8, "UNREALIZED_PNL_SNAPSHOT", "4", wallet="FUTURES"),
        sample_event(9, "INTERNAL_TRANSFER", "30", wallet="FUTURES", metadata={"to_wallet": "SPOT"}),
        sample_event(10, "WITHDRAWAL", "20"),
        sample_event(11, "WITHDRAWAL_FEE", "-1"),
        sample_event(12, "BALANCE_SNAPSHOT", "9"),
        sample_event(13, "BALANCE_SNAPSHOT", "76.5", wallet="FUTURES"),
    ]
    return {"schema": "synthetic-history-v1", "stream": "demo-history", "expected_end": 13,
            "manifest": {str(i): digest(json.dumps(safe_payload(e), sort_keys=True)) for i, e in enumerate(events, 1)},
            "records": [{"offset": i, "event": e} for i, e in enumerate(events, 1)],
            "expected": {"SPOT.USDT": "9", "FUTURES.USDT": "76.5", "external_deposit": "100",
                         "external_withdrawal": "20", "net_trade_pnl_futures": "6.5"}}


class FakeBinanceSource:
    def __init__(self, data: dict, disconnect_after: int | None = None,
                 pace_ms: int = 0, sleeper: Callable[[float], None] = time.sleep) -> None:
        if data.get("schema") != "synthetic-history-v1":
            raise ValueError("FAKE_HISTORY_SCHEMA")
        self.stream = data["stream"]
        self.expected_end = data["expected_end"]
        if type(self.expected_end) is not int or not 0 <= self.expected_end <= 1_000_000_000:
            raise ValueError("FAKE_HISTORY_END")
        self.records = data["records"]
        self.expected_manifest = ({int(k): v for k, v in data["manifest"].items()} if "manifest" in data else
                                  {r["offset"]: digest(json.dumps(safe_payload(r["event"]), sort_keys=True)) for r in self.records})
        self.disconnect_after = disconnect_after
        if type(pace_ms) is not int or not 0 <= pace_ms <= 1000:
            raise ValueError("FAKE_PACING")
        self.pace_ms, self.sleeper = pace_ms, sleeper

    @classmethod
    def load(cls, path: str | Path, disconnect_after: int | None = None, pace_ms: int = 0) -> FakeBinanceSource:
        if Path(path).stat().st_size > 8_000_000:
            raise ValueError("FAKE_HISTORY_SIZE")
        return cls(json.loads(Path(path).read_text()), disconnect_after, pace_ms)

    def history(self) -> Iterator[tuple[int, dict]]:
        for i, record in enumerate(self.records):
            if self.disconnect_after is not None and i == self.disconnect_after:
                raise SourceDisconnected("FAKE_SOURCE_DISCONNECTED")
            if self.pace_ms:
                self.sleeper(self.pace_ms / 1000)  # Scheduler time only, never money.
            yield record["offset"], record["event"]
