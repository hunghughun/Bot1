"""Verify the initial PC handoff snapshot, without network, keys or writes."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        manifest = json.loads((ROOT / "HANDOFF-MANIFEST.json").read_text(encoding="utf-8"))
        records = manifest["files"]
        if not isinstance(records, list) or not records:
            raise ValueError("INVALID_MANIFEST")
        bad, seen = [], set()
        for record in records:
            name = record["path"]
            if type(name) is not str:
                raise ValueError("INVALID_PATH")
            relative = PurePosixPath(name)
            path = ROOT.joinpath(*relative.parts)
            if (relative.is_absolute() or ".." in relative.parts or "\\" in name
                    or not path.resolve().is_relative_to(ROOT.resolve())
                    or name.casefold() in seen):
                raise ValueError("INVALID_PATH")
            seen.add(name.casefold())
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
                bad.append(name)
        print(json.dumps({"status": "FAIL" if bad else "PASS", "files_checked": len(records),
                          "changed_or_missing": bad, "network_used": False}))
        return 1 if bad else 0
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status": "FAIL", "error": "HANDOFF_MANIFEST_UNREADABLE_OR_INVALID"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
