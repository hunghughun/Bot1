"""Review inventory, not an invented Binance contract registry."""
from dataclasses import dataclass
from types import MappingProxyType


class UnsupportedContract(ValueError):
    pass


@dataclass(frozen=True)
class ContractReview:
    name: str
    status: str = "NOT VERIFIED"
    official_content_sha256: str | None = None
    verified_at: str | None = None
    sdk_commit: str = "f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179"
    sdk_evidence: bool = True
    offline_mapping_supported: bool = False


REVIEWS = MappingProxyType({name: ContractReview(name, offline_mapping_supported=name == "futures_balance_v3") for name in (
    "futures_balance_v3", "futures_income", "futures_account", "futures_positions",
    "deposit_history", "withdraw_history", "universal_transfer_history",
    "spot_funding_balances", "futures_user_stream",
)})


def require_verified(name: str) -> None:
    # Full API-docs/permission review remains incomplete. This is the LIVE gate.
    raise UnsupportedContract("BINANCE_CONTRACT_NOT_VERIFIED")


def require_sdk_mapping(name: str) -> None:
    if name not in REVIEWS or not REVIEWS[name].offline_mapping_supported:
        raise UnsupportedContract("BINANCE_SDK_MAPPING_NOT_VERIFIED")
