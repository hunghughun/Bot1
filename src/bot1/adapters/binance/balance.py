"""Futures Balance V3, pinned SDK 18.3.0 profile, OFFLINE SNAPSHOTS ONLY.

The endpoint supplies no transaction ID. Observation IDs below are LOCAL IDs,
bound to an explicitly supplied account and durable poll ID, not Binance IDs.
updateTime is the last account update in ms, not snapshot acquisition time.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from bot1.adapters.binance.contracts import REVIEWS, require_sdk_mapping
from bot1.adapters.binance.parsing import JsonNumber, ParsedFrame
from bot1.core.numeric import parse, serialize
from bot1.domain.events import Event, digest, label, utc

CONTRACT = "futures_balance_v3"
MONEY = frozenset({"balance", "crossWalletBalance", "crossUnPnl",
                   "availableBalance", "maxWithdrawAmount"})
ALLOWED = MONEY | {"accountAlias", "asset", "marginAvailable", "updateTime"}
REQUIRED = {"accountAlias", "asset", "balance", "availableBalance", "updateTime"}


class BalanceError(ValueError):
    """Safe fixed error codes only, never reflect raw account data."""


@dataclass(frozen=True)
class BalanceContext:
    account: str
    expected_account_alias: str
    poll_id: str
    received_time: str

    def __post_init__(self) -> None:
        label(self.account, "account")
        label(self.poll_id, "poll_id")
        # SDK StrictStr has no alias syntax constraint; this is a local bound.
        if (type(self.expected_account_alias) is not str
                or not 1 <= len(self.expected_account_alias) <= 120
                or not self.expected_account_alias.isascii()
                or not self.expected_account_alias.isprintable()):
            raise BalanceError("BALANCE_ACCOUNT_BINDING")
        object.__setattr__(self, "received_time", utc(self.received_time))


def validate_balance(frame: ParsedFrame, context: BalanceContext) -> tuple[dict, ...]:
    require_sdk_mapping(frame.contract_id)
    if frame.channel != "rest":
        raise BalanceError("BALANCE_REST_REQUIRED")
    if not isinstance(frame.data, list) or not frame.data:
        # Empty is not proof of zero assets or account-history coverage.
        raise BalanceError("BALANCE_NONEMPTY_ARRAY_REQUIRED")
    result, assets = [], set()
    for row in frame.data:
        if not isinstance(row, dict) or set(row) - ALLOWED or not REQUIRED <= set(row):
            raise BalanceError("BALANCE_FIELD_SCHEMA")
        if type(row["accountAlias"]) is not str or row["accountAlias"] != context.expected_account_alias:
            raise BalanceError("BALANCE_ACCOUNT_BINDING")
        asset = row["asset"]
        if type(asset) is not str or re.fullmatch(r"[A-Z0-9]{2,16}", asset, re.ASCII) is None:
            raise BalanceError("BALANCE_ASSET")
        if asset in assets:
            raise BalanceError("BALANCE_DUPLICATE_ASSET")
        assets.add(asset)
        for field in MONEY:
            if field not in row or row[field] is None:
                if field in REQUIRED:
                    raise BalanceError("BALANCE_REQUIRED_MONEY")
                continue
            # StrictStr in SDK; JsonNumber is NOT accepted for these fields.
            if type(row[field]) is not str:
                raise BalanceError("BALANCE_MONEY_STRING_REQUIRED")
            parse(row[field], "signed")
        if "marginAvailable" in row and row["marginAvailable"] is not None and type(row["marginAvailable"]) is not bool:
            raise BalanceError("BALANCE_MARGIN_FLAG")
        stamp = row["updateTime"]
        if (not isinstance(stamp, JsonNumber)
                or re.fullmatch(r"[1-9][0-9]{0,14}", stamp.lexeme, re.ASCII) is None):
            raise BalanceError("BALANCE_UPDATE_TIME_MS")
        try:
            event_time = (datetime(1970, 1, 1, tzinfo=timezone.utc)
                          + timedelta(milliseconds=int(stamp.lexeme))).isoformat(timespec="microseconds")
        except (OverflowError, ValueError):
            raise BalanceError("BALANCE_UPDATE_TIME_MS") from None
        # Future last-update times relative to acquisition are contradictory.
        if event_time > context.received_time:
            raise BalanceError("BALANCE_FUTURE_UPDATE")
        result.append({**row, "updateTime": stamp.lexeme, "event_time": event_time})
    return tuple(result)


def map_balance(frame: ParsedFrame, context: BalanceContext) -> tuple[dict, ...]:
    rows = validate_balance(frame, context)
    events = []
    for row in rows:
        for field, metric in (("balance", "wallet"), ("availableBalance", "available")):
            local_id = "balance-observation:" + digest([
                CONTRACT, context.account, context.expected_account_alias,
                context.poll_id, row["asset"], metric])
            event = {
                "schema_version": 1, "source": "binance-rest-sdk",
                "source_event_id": local_id, "id_trusted": True,
                "account": context.account, "wallet": "FUTURES", "asset": row["asset"],
                "amount": serialize(parse(row[field])), "event_type": "BALANCE_SNAPSHOT",
                "event_time": row["event_time"], "received_time": context.received_time,
                "status": "completed", "version": 1, "metadata": {"metric": metric},
                "evidence": "sdk:" + REVIEWS[CONTRACT].sdk_commit + ";body-sha256:" + frame.sha256,
            }
            Event.from_dict(event)  # Actual Internal Schema v1 validation.
            events.append(event)
    return tuple(events)
