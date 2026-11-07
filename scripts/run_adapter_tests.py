"""Full offline regression plus honest capability-status metadata."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bot1.adapters.binance.contracts import REVIEWS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs/test-reports/adapter-offline-tests.json")
    args = parser.parse_args()
    env = dict(os.environ, BOT1_TEST_OFFLINE="1", PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT))
    with tempfile.TemporaryDirectory() as tmp:
        fresh_output = Path(tmp) / "new-results.json"
        run = subprocess.run([sys.executable, str(ROOT / "scripts/run_tests.py"), "--output", str(fresh_output)], cwd=ROOT, env=env, capture_output=True, text=True)
        result = json.loads(fresh_output.read_text(encoding="utf-8")) if fresh_output.exists() else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if result is None:
        args.output.write_text(json.dumps({"status": "FAIL", "executed": 0, "pass": 0,
                                          "fail": 0, "not_tested": 0, "bootstrap_failed": True,
                                          "reason": "No fresh test-run output; old results not reused"}) + "\n", encoding="utf-8")
        print("TEST_RUN_DID_NOT_PRODUCE_RESULTS", file=sys.stderr)
        return 1
    result["core_regression"] = {"executed": sum(not r["id"].startswith("tests.adapter_offline.") for r in result["cases"]),
                                 "pass": sum(r["status"] == "PASS" and not r["id"].startswith("tests.adapter_offline.") for r in result["cases"])}
    def group(prefix):
        cases = [r for r in result["cases"] if r["id"].startswith(prefix)]
        return {"executed": len(cases), "pass": sum(r["status"] == "PASS" for r in cases),
                "fail": sum(r["status"] == "FAIL" for r in cases), "test_ids": [r["id"] for r in cases]}
    result["adapter_foundations"] = group("tests.adapter_offline.test_foundations.")
    result["sdk_balance_contract_and_reliability"] = group("tests.adapter_offline.test_balance_contract.")
    result["balance_smoke_offline_preparation"] = {
        **group("tests.adapter_offline.test_balance_smoke."),
        "scope": "Offline SDK candidate, fake exchange and blocked live CLI; NOT a live timeout/auth/permission test",
        "official_api_docs_verified": False, "official_api_golden_fixtures": [],
        "live_query_executed": False, "windows_python314_verified": False,
        "live_status": "NOT VERIFIED"}
    positive = group("tests.adapter_offline.test_balance_contract.BalancePositiveContractTests.")
    result["binance_positive_contract_tests"] = {
        **positive, "scope": "Pinned SDK offline profile, includes provenance and synthetic schema mutations; no live API tests",
        "official_verified_fixtures": [],
        "sdk_mock_fixtures": ["tests/fixtures/binance_sdk/balance_v3_response.json"],
        "capabilities": [{"contract": name,
                          "offline_sdk_mapping_status": ("PASS" if positive["executed"] and positive["pass"] == positive["executed"] else "FAIL") if review.offline_mapping_supported else "NOT TESTED",
                          "full_api_verification": review.status, "sdk_commit": review.sdk_commit,
                          "reason": "Snapshot wallet/available only" if review.offline_mapping_supported else "SDK evidence retained; financial mapping/correlation incomplete"}
                         for name, review in REVIEWS.items()]}
    result["live_readonly_enabled"] = False
    result["status"] = "PASS" if run.returncode == 0 and result["executed"] > 0 else "FAIL"
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runtime_pass": result["pass"], "runtime_fail": result["fail"],
                      "runtime_skipped": result["not_tested"], "core": result["core_regression"],
                      "adapter_foundations": {k: v for k, v in result["adapter_foundations"].items() if k != "test_ids"},
                      "sdk_balance": {k: v for k, v in result["sdk_balance_contract_and_reliability"].items() if k != "test_ids"},
                      "smoke_preparation": {k: result["balance_smoke_offline_preparation"][k] for k in ("executed", "pass", "fail")},
                      "full_api_families_not_verified": len(REVIEWS)}))
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
