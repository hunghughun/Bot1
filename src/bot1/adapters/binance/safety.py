"""Offline is the only executable mode; no credentials or signing performed."""
from dataclasses import dataclass
from typing import Protocol


class LiveModeDisabled(RuntimeError):
    pass


@dataclass(frozen=True)
class AdapterConfig:
    mode: str = "offline"
    timeout_ms: int = 10000

    def __post_init__(self) -> None:
        if self.mode != "offline":
            raise LiveModeDisabled("LIVE_READONLY_DISABLED")
        if type(self.timeout_ms) is not int or not 1 <= self.timeout_ms <= 60000:
            raise ValueError("CONNECTION_TIMEOUT_CONFIG")


class EndpointAllowlist:
    @property
    def entries(self) -> frozenset[tuple[str, str, str]]:
        return frozenset()

    def authorize(self, method: str, base_url: str, path: str) -> None:
        # GET/POST semantics cannot be inferred without official documentation.
        raise LiveModeDisabled("ENDPOINT_NOT_VERIFIED")


class OfflineTransport:
    def request(self, method: str, base_url: str, path: str) -> bytes:
        raise LiveModeDisabled("OFFLINE_NETWORK_DISABLED")


class CredentialsProvider(Protocol):
    """Future secure-provider boundary. No environment/file reads in this release."""
    def credential_reference(self) -> str: ...


class RequestSigner(Protocol):
    def sign(self, request_bytes: bytes) -> bytes: ...


class DisabledSigner:
    def sign(self, request_bytes: bytes) -> bytes:
        raise LiveModeDisabled("SIGNING_NOT_VERIFIED_OR_ENABLED")
