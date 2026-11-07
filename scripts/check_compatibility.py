"""Run real tests on the executing platform, or report missing target NOT TESTED."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-windows", action="store_true")
    parser.add_argument("--require-python314", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    unavailable = []
    if args.require_windows and platform.system() != "Windows":
        unavailable.append("Windows interpreter is required")
    if args.require_python314 and sys.version_info[:2] != (3, 14):
        unavailable.append("CPython 3.14 interpreter is required")
    result = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "system": platform.system(), "python": platform.python_version(),
              "required_windows": args.require_windows, "required_python314": args.require_python314,
              "status": "NOT TESTED", "reasons": unavailable}
    if not unavailable:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "runtime.json"
            run = subprocess.run([sys.executable, str(ROOT / "scripts/run_tests.py"), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
            result["test_exit_code"] = run.returncode
            if output.exists():
                result["runtime"] = json.loads(output.read_text(encoding="utf-8"))
            result["status"] = "PASS" if run.returncode == 0 and result.get("runtime", {}).get("executed", 0) > 0 else "FAIL"
            args.output.with_suffix(".log").parent.mkdir(parents=True, exist_ok=True)
            args.output.with_suffix(".log").write_text(run.stdout + run.stderr, encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "runtime"}))
    return 2 if unavailable else 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
