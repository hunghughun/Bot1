"""Offline implementation tests. Network guard also applies to direct unittest runs."""
import os
from pathlib import Path
import runpy
import sys

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))
os.environ["BOT1_TEST_OFFLINE"] = "1"
os.environ["PYTHONPATH"] = str(_root / "src") + os.pathsep + str(_root)
runpy.run_path(str(_root / "src/sitecustomize.py"))
