"""Offline intake/quarantine journal, not a live Binance client or verified mapper."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sqlite3
from typing import Iterator, Protocol

from bot1.adapters.binance.mapper import AccountEventMapper
from bot1.adapters.binance.parsing import RestResponseParser, ParseError, ParsedFrame
from bot1.adapters.binance.websocket import WebSocketEventParser
from bot1.adapters.binance.contracts import UnsupportedContract, REVIEWS
from bot1.adapters.binance.safety import AdapterConfig
from bot1.core.numeric import NumericError


@dataclass(frozen=True)
class OfflineEnvelope:
    contract_id: str
    channel: str
    payload: bytes

    def __post_init__(self) -> None:
        if type(self.payload) is not bytes or type(self.channel) is not str or type(self.contract_id) is not str:
            raise ValueError("OFFLINE_ENVELOPE_TYPES")


class BinanceSourceInterface(Protocol):
    def events(self) -> Iterator[dict]: ...


class AdapterQuarantine:
    """Separate DB: do not migrate or mutate an existing core database."""
    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        tables = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        app_id = self.db.execute("PRAGMA application_id").fetchone()[0]
        if tables and (tables != {"rejected_frames"} or app_id != 1111560529):
            self.db.close()
            raise ValueError("NOT_AN_ADAPTER_QUARANTINE_DATABASE")
        self.db.execute("CREATE TABLE IF NOT EXISTS rejected_frames (id INTEGER PRIMARY KEY, contract_id TEXT NOT NULL, channel TEXT NOT NULL, payload_sha256 TEXT NOT NULL, error_code TEXT NOT NULL, received_at TEXT NOT NULL, UNIQUE(contract_id,channel,payload_sha256,error_code))")
        self.db.execute("PRAGMA application_id=1111560529")
        self.db.execute("PRAGMA user_version=1")
        self.db.commit()

    def reject(self, envelope: OfflineEnvelope, code: str) -> None:
        # Raw payloads, signed headers, URLs and credentials are never stored here.
        self.db.execute("INSERT OR IGNORE INTO rejected_frames(contract_id,channel,payload_sha256,error_code,received_at) VALUES(?,?,?,?,?)",
                        (envelope.contract_id if envelope.contract_id in REVIEWS else "UNKNOWN_CONTRACT",
                         envelope.channel if envelope.channel in ("rest", "websocket") else "UNKNOWN_CHANNEL",
                         hashlib.sha256(envelope.payload).hexdigest(), code, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def rows(self) -> list[tuple]:
        return self.db.execute("SELECT contract_id,channel,payload_sha256,error_code FROM rejected_frames ORDER BY id").fetchall()

    def close(self) -> None:
        self.db.close()


class OfflineBinanceSource:
    def __init__(self, envelopes: list[OfflineEnvelope], quarantine: AdapterQuarantine,
                 config: AdapterConfig | None = None) -> None:
        self.config = config or AdapterConfig()
        self.envelopes, self.quarantine = envelopes, quarantine
        self.stream = "binance-offline-unverified"
        self.expected_end = len(envelopes)

    @property
    def expected_manifest(self) -> dict[int, str]:
        # Implements the core source boundary without fabricating Binance sequence IDs.
        raise UnsupportedContract("BINANCE_CURSOR_COVERAGE_NOT_VERIFIED")

    def history(self) -> Iterator[tuple[int, dict]]:
        raise UnsupportedContract("BINANCE_SOURCE_NOT_READY")

    def events(self) -> Iterator[dict]:
        for envelope in self.envelopes:
            try:
                if envelope.channel not in ("rest", "websocket"):
                    raise ParseError("CHANNEL_UNSUPPORTED")
                parser = RestResponseParser() if envelope.channel == "rest" else WebSocketEventParser()
                frame = parser.parse(envelope.payload, envelope.contract_id)
                yield from AccountEventMapper().map(frame)
            except (ParseError, UnsupportedContract, NumericError) as exc:
                self.quarantine.reject(envelope, str(exc))

    @property
    def complete(self) -> bool:
        # There is no verified normalization/cursor/coverage contract to certify.
        return False
