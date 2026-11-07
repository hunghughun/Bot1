"""Internal schema only. No assumption that these are Binance response fields."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from bot1.core.numeric import parse, serialize

TYPES = frozenset({"BALANCE_SNAPSHOT", "DEPOSIT", "WITHDRAWAL", "INTERNAL_TRANSFER",
                   "REALIZED_PNL", "UNREALIZED_PNL_SNAPSHOT", "TRADING_FEE",
                   "FUNDING_FEE", "WITHDRAWAL_FEE", "ACCOUNT_ADJUSTMENT"})
WALLETS = frozenset({"SPOT", "FUTURES", "FUNDING"})
STATUSES = frozenset({"pending", "completed", "failed", "cancelled", "correction"})
META = frozenset({"to_wallet", "metric", "opening", "reverses", "economic_id",
                  "correlation_evidence", "network"})
FIELDS = frozenset({"source", "source_event_id", "id_trusted", "account", "wallet",
                    "asset", "amount", "event_type", "event_time", "received_time",
                    "status", "version", "schema_version", "metadata", "evidence"})


class EventError(ValueError):
    pass


def utc(raw: object) -> str:
    if not isinstance(raw, str) or len(raw) > 40:
        raise EventError("EVENT_TIME")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise EventError("EVENT_TIME") from None
    if value.tzinfo is None:
        raise EventError("EVENT_TIME")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def label(value: object, field: str) -> str:
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", value, re.ASCII) is None:
        raise EventError("EVENT_" + field.upper())
    return value


def gmt7(raw: str) -> str:
    return datetime.fromisoformat(utc(raw)).astimezone(timezone(timedelta(hours=7))).isoformat()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def safe_payload(raw: object) -> Any:
    """Allowlist storage. Unknown keys/secret metadata are never retained."""
    if not isinstance(raw, dict):
        return {"invalid": "NON_OBJECT"}
    result: dict[str, Any] = {}
    for key in FIELDS:
        if key not in raw:
            continue
        value = raw[key]
        if key == "metadata":
            result[key] = {k: v[:256] if isinstance(v, str) else v
                           for k, v in value.items() if k in META and type(v) in (str, bool, int, type(None))} if isinstance(value, dict) else "INVALID"
            if isinstance(value, dict) and (set(value) - META or any(type(v) not in (str, bool, int, type(None)) for v in value.values())):
                result[key]["unknown_metadata"] = "REDACTED"
        elif type(value) is str:
            result[key] = value[:256]
        elif type(value) in (int, bool, type(None)):
            result[key] = value
        else:
            result[key] = "INVALID_TYPE"
    if set(raw) - FIELDS:
        result["unknown_fields"] = "REDACTED"
    return result


@dataclass(frozen=True)
class Event:
    source: str
    source_event_id: str
    account: str
    wallet: str
    asset: str
    amount: Decimal
    event_type: str
    event_time: str
    received_time: str
    status: str
    version: int
    metadata: dict[str, Any]
    evidence: str

    @classmethod
    def from_dict(cls, raw: object) -> Event:
        if not isinstance(raw, dict) or set(raw) - FIELDS:
            raise EventError("EVENT_SCHEMA")
        if raw.get("schema_version") != 1 or type(raw.get("schema_version")) is not int:
            raise EventError("EVENT_SCHEMA_VERSION")
        if raw.get("id_trusted") is not True:
            raise EventError("EVENT_UNTRUSTED_ID")
        kind, status = raw.get("event_type"), raw.get("status")
        if type(kind) is not str or type(status) is not str or kind not in TYPES or status not in STATUSES:
            raise EventError("EVENT_TYPE_OR_STATUS")
        if type(raw.get("wallet")) is not str or raw.get("wallet") not in WALLETS:
            raise EventError("EVENT_WALLET")
        asset = raw.get("asset")
        if type(asset) is not str or re.fullmatch(r"[A-Z0-9]{2,16}", asset, re.ASCII) is None:
            raise EventError("EVENT_ASSET")
        meta = raw.get("metadata", {})
        if not isinstance(meta, dict) or set(meta) - META:
            raise EventError("EVENT_METADATA")
        meta = dict(meta)
        for k, v in meta.items():
            if k == "opening":
                if type(v) is not bool:
                    raise EventError("EVENT_METADATA")
            elif type(v) is not str or len(v) > 120:
                raise EventError("EVENT_METADATA")
        if kind == "INTERNAL_TRANSFER" and (meta.get("to_wallet") not in WALLETS or meta["to_wallet"] == raw["wallet"]):
            raise EventError("EVENT_TRANSFER_DESTINATION")
        if kind == "BALANCE_SNAPSHOT" and meta.get("metric", "wallet") not in {"wallet", "available", "margin", "initial_margin"}:
            raise EventError("EVENT_METRIC")
        if meta.get("opening") and (kind != "BALANCE_SNAPSHOT" or meta.get("metric", "wallet") != "wallet"):
            raise EventError("EVENT_OPENING")
        if "economic_id" in meta and not meta.get("correlation_evidence"):
            raise EventError("EVENT_CORRELATION_EVIDENCE")
        if status == "correction" and (kind != "ACCOUNT_ADJUSTMENT" or not meta.get("reverses")):
            raise EventError("EVENT_CORRECTION")
        version = raw.get("version")
        if type(version) is not int or not 0 <= version <= 1_000_000:
            raise EventError("EVENT_VERSION")
        evidence = raw.get("evidence")
        if type(evidence) is not str or not 1 <= len(evidence) <= 256:
            raise EventError("EVENT_EVIDENCE")
        domain = "positive" if kind in {"DEPOSIT", "WITHDRAWAL", "INTERNAL_TRANSFER"} else "signed"
        return cls(label(raw.get("source"), "source"), label(raw.get("source_event_id"), "source_id"),
                   label(raw.get("account"), "account"), raw["wallet"], asset,
                   parse(raw.get("amount"), domain), kind, utc(raw.get("event_time")),
                   utc(raw.get("received_time")), status, version, meta, evidence)

    @property
    def identity(self) -> str:
        return digest([self.source, self.account, self.wallet, self.asset, self.event_type, self.source_event_id])

    @property
    def financial_hash(self) -> str:
        return digest([self.account, self.wallet, self.asset, self.event_type,
                       serialize(self.amount), self.event_time, {k: self.metadata[k] for k in
                       ("to_wallet", "metric", "opening", "reverses", "economic_id") if k in self.metadata}])

    @property
    def economic_key(self) -> str:
        if "economic_id" in self.metadata:
            return digest([self.account, self.event_type, self.metadata["economic_id"]])
        return self.identity
