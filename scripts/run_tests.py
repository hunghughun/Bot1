"""Execute implementation tests and retain individual outcomes, never doc checks."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone
import platform
import argparse
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"id": test.id(), "status": "PASS"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"id": test.id(), "status": "FAIL"})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"id": test.id(), "status": "FAIL"})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append({"id": test.id(), "status": "NOT TESTED", "reason": reason})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs/test-reports/runtime-tests.json")
    parser.add_argument("--baseline-ids", type=Path, help="Run only previously recorded test IDs")
    args = parser.parse_args()
    os.environ["BOT1_TEST_OFFLINE"] = "1"
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + str(ROOT)
    import runpy
    runpy.run_path(str(ROOT / "src/sitecustomize.py"))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    if args.baseline_ids:
        baseline = json.loads(args.baseline_ids.read_text())
        suite = unittest.defaultTestLoader.loadTestsFromNames([row["id"] for row in baseline["cases"]])
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    output = args.output
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps({"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                                 "python": platform.python_version(), "platform": platform.platform(),
                                 "scope": "Bot 1 implementation, synthetic inputs only; no document checker tests",
                                 "offline_network_guard": True,
                                 "subprocess_guard": "BOT1_TEST_OFFLINE plus src/sitecustomize.py via PYTHONPATH",
                                 "executed": result.testsRun, "cases": result.records,
                                 "pass": sum(r["status"] == "PASS" for r in result.records),
                                 "fail": len(result.failures) + len(result.errors),
                                 "not_tested": len(result.skipped)}, indent=2) + "\n")
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun > 0 else 1)
