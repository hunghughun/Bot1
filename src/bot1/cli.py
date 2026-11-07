from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import subprocess
import sqlite3
import sys

from bot1.database.store import Store, DatabaseBusy
from bot1.domain.events import EventError
from bot1.health.monitor import Health, SafeJSONFormatter
from bot1.ledger.engine import Engine
from bot1.notifications.fake import FakeTelegram
from bot1.notifications.outbox import Outbox
from bot1.recovery.runner import Recovery
from bot1.sources.fake import FakeBinanceSource, scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bot 1 OFFLINE ONLY. No network adapters or keys.")
    parser.add_argument("--db", default="data/runtime/bot1.sqlite")
    parser.add_argument("--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    load = commands.add_parser("load-mock")
    load.add_argument("--output", default="data/mock/scenario.json")
    for command in ("simulate", "recover"):
        sub = commands.add_parser(command)
        sub.add_argument("--input", default="data/mock/scenario.json")
        sub.add_argument("--disconnect-after", type=int)
        sub.add_argument("--pace-ms", type=int, default=0)
    balances = commands.add_parser("balances")
    balances.add_argument("--account", default="demo")
    commands.add_parser("history")
    notifications = commands.add_parser("notifications")
    notifications.add_argument("--drain", action="store_true")
    notifications.add_argument("--sink", default="data/runtime/fake-telegram.jsonl")
    commands.add_parser("gaps")
    commands.add_parser("health")
    commands.add_parser("test")
    args = parser.parse_args(argv)
    if args.verbose:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeJSONFormatter())
        logging.getLogger("bot1").addHandler(handler)
        logging.getLogger("bot1").setLevel(logging.INFO)
    if args.command == "test":
        return subprocess.call([sys.executable, str(Path(__file__).resolve().parents[2] / "scripts/run_tests.py")])
    if args.command == "load-mock":
        target = Path(args.output)
        if target.exists():
            parser.error("MOCK_ALREADY_EXISTS (choose another --output)")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(scenario(), indent=2) + "\n")
        print(json.dumps({"mock_created": str(target), "schema": "INTERNAL_SYNTHETIC_ONLY"}))
        return 0
    store = None
    try:
        store = Store(args.db)
        engine = Engine(store)
        if args.command == "init":
            result = {"database": args.db, "schema_version": 1, "mode": "OFFLINE_ONLY"}
        elif args.command in ("simulate", "recover"):
            result = Recovery(engine).run(FakeBinanceSource.load(args.input, args.disconnect_after, args.pace_ms))
        elif args.command == "balances":
            groups = store.rows("SELECT account,wallet,asset FROM openings WHERE account=? UNION SELECT account,wallet,asset FROM ledger WHERE account=?", (args.account, args.account))
            result = {"balances": [engine.balance(r["account"], r["wallet"], r["asset"]) for r in groups], "totals_by_wallet_asset_kind": engine.summaries(args.account)}
        elif args.command == "history":
            result = {"events": store.rows("SELECT * FROM events ORDER BY event_time,id"), "ledger": store.rows("SELECT * FROM ledger ORDER BY event_time,id")}
        elif args.command == "notifications":
            sent = Outbox(store, FakeTelegram(sink=args.sink)).drain() if args.drain else 0
            result = {"fake_attempts_this_run": sent, "outbox": store.rows("SELECT * FROM outbox ORDER BY enqueued_at,id")}
        elif args.command == "gaps":
            result = engine.gaps()
        else:
            result = Health(store).snapshot()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (EventError, DatabaseBusy, ValueError, OSError, sqlite3.Error) as exc:
        # Known errors only; avoid logging raw paths, credentials or exception payloads.
        print(json.dumps({"error_type": type(exc).__name__, "action": "inspect offline input/database; no financial action taken"}), file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()
