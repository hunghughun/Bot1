"""Reviewable experiment plan only. Building this plan opens no connections."""
from pathlib import Path

# This is a reviewed SDK query candidate, NOT an active network allowlist entry.
SDK_SNAPSHOT_CANDIDATE = ("GET", "https://fapi.binance.com", "/fapi/v3/balance")


def balance_trial_plan(database: str | Path) -> dict:
    return {
        "mode": "offline", "live_readonly_enabled": False, "network_enabled": False,
        "snapshot_only": True, "database": str(Path(database)),
        "database_owner": "SnapshotSandbox", "write_business_ledger": False,
        "send_real_telegram": False, "credential_loading_enabled": False,
        "sdk_candidate": dict(zip(("method", "base_url", "path"), SDK_SNAPSHOT_CANDIDATE)),
        "active_allowlist": [],
        "required_before_live": ["API-docs/auth/permission review", "read-only key permission verification without trading/transfer/withdrawal",
                                 "reviewed signer/clock/rate/timeout/redirect/credential implementation",
                                 "explicit approval for a separate snapshot-only trial"],
    }
