import sys
from pathlib import Path

README_PATH = Path(__file__).resolve().parent / "README.md"

if README_PATH.exists():
    print(README_PATH.read_text(encoding="utf-8"))
else:
    print("NeSygma Benchmark Modular Test Suite - Execution Guide")

sys.exit(1)
