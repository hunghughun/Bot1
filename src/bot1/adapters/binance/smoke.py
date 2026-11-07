"""Balance smoke-test preparation, OFFLINE ONLY until API-docs review completes.

No HTTP library, environment/credential loading, DB, notifier or polling loop.
The signing candidate follows pinned SDK common-utils, NOT reviewed API docs.
It is deliberately unreachable from the live command. No key type is inferred.
"""
from dataclasses import dataclass, field
import hashlib
import hmac
import re
from typing import Protocol

from bot1.adapters.binance.balance import BalanceContext, MONEY, map_balance, validate_balance
from bot1.adapters.binance.contracts import UnsupportedContract, require_verified
from bot1.adapters.binance.parsing import RestResponseParser
from bot1.adapters.binance.trial import SDK_SNAPSHOT_CANDIDATE

MAX_RESPONSE_BYTES = 1_048_576


class SmokeError(ValueError):
    """Constant safe codes only; do not include exception/request/body details."""


def require_live_smoke(confirmed: bool, key_type: str | None) -> None:
    if confirmed is not True:
        raise SmokeError("SMOKE_OPERATOR_CONFIRMATION_REQUIRED")
    if key_type != "HMAC":
        raise SmokeError("SMOKE_KEY_TYPE_NOT_REVIEWED")
    # Mandatory, non-configurable live gate. A local flag or vendor file cannot
    # self-certify official docs, key scopes, signing or Windows readiness.
    require_verified("futures_balance_v3")
    raise UnsupportedContract("SMOKE_LIVE_TRANSPORT_NOT_IMPLEMENTED")


@dataclass(frozen=True, repr=False)
class CandidateRequest:
    """Sensitive in-memory SDK candidate, never print/log/serialize this object."""
    api_key: str = field(repr=False)
    signed_query: str = field(repr=False)
    method: str = field(init=False, default="GET")
    base_url: str = field(init=False, default="https://fapi.binance.com")
    path: str = field(init=False, default="/fapi/v3/balance")

    def __repr__(self) -> str:
        return "CandidateRequest(GET /fapi/v3/balance; SDK_ONLY; credentials=REDACTED)"

    @property
    def headers(self) -> dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    def check(self) -> None:
        if (self.method, self.base_url, self.path) != SDK_SNAPSHOT_CANDIDATE:
            raise SmokeError("SMOKE_ROUTE_FORBIDDEN")
        if (type(self.api_key) is not str or not 1 <= len(self.api_key) <= 256
                or not self.api_key.isascii() or not self.api_key.isprintable()
                or self.api_key.strip() != self.api_key):
            raise SmokeError("SMOKE_KEY_FORMAT")
        match = re.fullmatch(r"recvWindow=([1-9][0-9]{0,3})&timestamp=([1-9][0-9]{0,14})&signature=[a-f0-9]{64}", self.signed_query, re.ASCII) if type(self.signed_query) is str else None
        if match is None or int(match[1]) > 5000 or int(match[2]) > 253402300799999:
            raise SmokeError("SMOKE_QUERY_SCHEMA")


def prepare_sdk_hmac_candidate(*, api_key: str, secret: str, key_type: str,
                               timestamp_ms: int, recv_window_ms: int) -> CandidateRequest:
    """Pure offline SDK candidate; only synthetic credentials in this release.

    Local bounds: recvWindow 1..5000ms, not a claim about Binance's maximum;
    timestamp is an integer ms, no float. No secret retained on the request.
    RSA/Ed25519/unknown types explicitly unsupported, no HMAC fallback.
    """
    if key_type != "HMAC":
        raise SmokeError("SMOKE_KEY_TYPE_NOT_REVIEWED")
    if type(timestamp_ms) is not int or not 1 <= timestamp_ms <= 253402300799999:
        raise SmokeError("SMOKE_TIMESTAMP_MS")
    if type(recv_window_ms) is not int or not 1 <= recv_window_ms <= 5000:
        raise SmokeError("SMOKE_LOCAL_RECV_WINDOW")
    if type(secret) is not str or not 1 <= len(secret) <= 1024 or not secret.isascii() or not secret.isprintable():
        raise SmokeError("SMOKE_SECRET_FORMAT")
    query = f"recvWindow={recv_window_ms}&timestamp={timestamp_ms}"
    signature = hmac.new(secret.encode("ascii"), query.encode("ascii"), hashlib.sha256).hexdigest()
    request = CandidateRequest(api_key, query + "&signature=" + signature)
    request.check()
    return request


@dataclass(frozen=True, repr=False)
class SyntheticReply:
    status: int
    body: bytes = field(repr=False)
    elapsed_ms: int = 0

    def __repr__(self) -> str:
        return "SyntheticReply(body=REDACTED)"


class SyntheticExchange(Protocol):
    """Testing seam only. No production network implementation is supplied."""
    def request(self, request: CandidateRequest, *, timeout_ms: int,
                max_response_bytes: int) -> SyntheticReply: ...


def inspect_sdk_snapshot(reply: SyntheticReply, context: BalanceContext, *, timeout_ms: int = 10000) -> dict:
    """No side effects; return counts/codes only, never financial values or IDs."""
    if type(timeout_ms) is not int or not 1 <= timeout_ms <= 30000:
        raise SmokeError("SMOKE_TIMEOUT_CONFIG")
    if not isinstance(reply, SyntheticReply) or type(reply.status) is not int or type(reply.body) is not bytes:
        raise SmokeError("SMOKE_RESPONSE_TYPES")
    if type(reply.elapsed_ms) is not int or reply.elapsed_ms < 0:
        raise SmokeError("SMOKE_ELAPSED_TIME")
    if reply.elapsed_ms >= timeout_ms:
        raise SmokeError("SMOKE_TIMEOUT")
    if reply.status in (401, 403):
        raise SmokeError("SMOKE_AUTH_OR_PERMISSION_DENIED")
    if reply.status in (418, 429):
        raise SmokeError("SMOKE_RATE_LIMIT_STOP_NO_RETRY")
    if reply.status != 200:
        raise SmokeError("SMOKE_HTTP_STATUS_STOP_NO_RETRY")
    if len(reply.body) > MAX_RESPONSE_BYTES:
        raise SmokeError("SMOKE_RESPONSE_TOO_LARGE")
    frame = RestResponseParser().parse(reply.body, "futures_balance_v3")
    rows = validate_balance(frame, context)
    # Stricter local smoke acceptance, not an official required-fields claim:
    # all observed financial fields and flag must be present/non-null to report
    # a COMPLETE inspection. Existing mapper's Optional SDK profile is unchanged.
    for row in rows:
        if any(name not in row or row[name] is None for name in MONEY | {"marginAvailable"}):
            raise SmokeError("SMOKE_INCOMPLETE_OBSERVATION")
    events = map_balance(frame, context)
    return {"status": "PASS", "scope": "OFFLINE_SDK_PROFILE_ONLY",
            "official_api_docs_verified": False, "network_performed": False,
            "asset_rows_validated": len(rows), "snapshot_count": len(events),
            "financial_postings": 0, "database_writes": 0, "telegram_sends": 0}


class OfflineSmokeHarness:
    """One attempt for the lifetime of this harness, including failed attempts.

    Tests can check timeout propagation and hard stop on bans/rate errors. This
    is not an implemented live timeout or server quota controller.
    """
    def __init__(self, exchange: SyntheticExchange, *, timeout_ms: int = 10000) -> None:
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= 30000:
            raise SmokeError("SMOKE_TIMEOUT_CONFIG")
        self.exchange, self.timeout_ms, self.used = exchange, timeout_ms, False

    def run_once(self, request: CandidateRequest, context: BalanceContext) -> dict:
        if self.used:
            raise SmokeError("SMOKE_SINGLE_ATTEMPT_EXHAUSTED")
        if not isinstance(request, CandidateRequest) or not isinstance(context, BalanceContext):
            raise SmokeError("SMOKE_INPUT_TYPES")
        request.check()
        self.used = True
        try:
            reply = self.exchange.request(request, timeout_ms=self.timeout_ms,
                                          max_response_bytes=MAX_RESPONSE_BYTES)
        except Exception:
            raise SmokeError("SMOKE_EXCHANGE_STOP_NO_RETRY") from None
        return inspect_sdk_snapshot(reply, context, timeout_ms=self.timeout_ms)
