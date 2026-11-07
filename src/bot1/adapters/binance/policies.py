"""Transport-neutral offline policies. No invented Binance codes/limits/headers."""
from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class HTTPDecision:
    category: str
    retryable: bool
    wait_ms: int = 0


def classify_http(status: int, retry_after_seconds: str | None = None) -> HTTPDecision:
    if type(status) is not int or not 100 <= status <= 599:
        raise ValueError("HTTP_STATUS")
    if status == 429:
        if retry_after_seconds is None:
            return HTTPDecision("RATE_LIMIT_DELAY_UNKNOWN_HALT", False)
        if (type(retry_after_seconds) is not str or not retry_after_seconds.isascii()
                or not retry_after_seconds.isdecimal() or len(retry_after_seconds) > 6):
            return HTTPDecision("RETRY_AFTER_UNSUPPORTED_HALT", False)
        return HTTPDecision("RATE_LIMIT", True, int(retry_after_seconds) * 1000)
    if status == 401:
        return HTTPDecision("AUTHENTICATION_HALT", False)
    if status == 403:
        return HTTPDecision("ACCESS_DENIED_HALT", False)
    if status >= 500:
        return HTTPDecision("SERVER_TRANSIENT", True)
    if 400 <= status < 500:
        return HTTPDecision("CLIENT_ERROR_HALT", False)
    if 200 <= status < 300:
        return HTTPDecision("HTTP_SUCCESS_SCHEMA_STILL_REQUIRED", False)
    return HTTPDecision("UNSUPPORTED_HTTP_STATE_HALT", False)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    base_ms: int = 1000
    cap_ms: int = 60000

    def __post_init__(self) -> None:
        if any(type(v) is not int for v in (self.max_attempts, self.base_ms, self.cap_ms)) or not 1 <= self.max_attempts <= 20 or not 1 <= self.base_ms <= self.cap_ms <= 60000:
            raise ValueError("RETRY_CONFIG")

    def delay(self, attempt: int, key: str, server_wait_ms: int = 0) -> int | None:
        if type(attempt) is not int or attempt < 1 or type(server_wait_ms) is not int or server_wait_ms < 0:
            raise ValueError("RETRY_INPUT")
        if attempt >= self.max_attempts:
            return None
        jitter = int.from_bytes(hashlib.sha256((key + str(attempt)).encode()).digest()[:2], "big") % 251
        return max(server_wait_ms, min(self.cap_ms, self.base_ms * 2 ** (attempt - 1) + jitter))


class RateBudget:
    """Parameters supplied by caller; never advertised as Binance's rate limits."""
    def __init__(self, capacity: int, window_ms: int) -> None:
        if type(capacity) is not int or type(window_ms) is not int or capacity <= 0 or window_ms <= 0:
            raise ValueError("RATE_BUDGET_CONFIG")
        self.capacity, self.window_ms = capacity, window_ms
        self.start: int | None = None
        self.used = 0
        self.last: int | None = None

    def reserve(self, weight: int, now_ms: int) -> bool:
        if type(weight) is not int or not 1 <= weight <= self.capacity or type(now_ms) is not int:
            raise ValueError("RATE_WEIGHT_OR_CLOCK")
        if self.last is not None and now_ms < self.last:
            raise ValueError("MONOTONIC_CLOCK_REGRESSION")
        self.last = now_ms
        if self.start is None or now_ms - self.start >= self.window_ms:
            self.start, self.used = now_ms, 0
        if self.used + weight > self.capacity:
            return False
        self.used += weight
        return True


def clock_observation(sent_utc_ms: int, received_utc_ms: int, server_utc_ms: int,
                      maximum_rtt_ms: int = 1000) -> tuple[int, int]:
    if any(type(v) is not int for v in (sent_utc_ms, received_utc_ms, server_utc_ms, maximum_rtt_ms)) or maximum_rtt_ms < 0:
        raise ValueError("CLOCK_INPUT")
    rtt = received_utc_ms - sent_utc_ms
    if not 0 <= rtt <= maximum_rtt_ms:
        raise ValueError("CLOCK_SAMPLE_UNRELIABLE")
    return server_utc_ms - (sent_utc_ms + received_utc_ms) // 2, rtt


def freshness(now_ms: int, last_transport_ms: int, last_snapshot_ms: int,
              transport_limit_ms: int, snapshot_limit_ms: int) -> dict[str, bool]:
    if any(type(v) is not int for v in (now_ms, last_transport_ms, last_snapshot_ms, transport_limit_ms, snapshot_limit_ms)) or min(transport_limit_ms, snapshot_limit_ms) <= 0 or min(now_ms - last_transport_ms, now_ms - last_snapshot_ms) < 0:
        raise ValueError("FRESHNESS_CLOCK")
    return {"transport_stale": now_ms - last_transport_ms > transport_limit_ms,
            "snapshot_stale": now_ms - last_snapshot_ms > snapshot_limit_ms}
