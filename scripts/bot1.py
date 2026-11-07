"""Run without installation or dependency downloads."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bot1.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
