"""
Run All Tests — Executes every test file in the tests/ directory.

Usage:
    python tests/run_all_tests.py

Runs each test file as a subprocess and aggregates results.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"

TESTS_DIR = Path(__file__).resolve().parent

# Test files in execution order (sync tests first, then async)
TEST_FILES = [
    "test_ui.py",
    "test_agent.py",
    "test_app.py",
    "test_system1.py",
    "test_switcher.py",
    "test_selector.py",
    "test_clingo_server.py",
    "test_z3_server.py",
    "test_vampire_server.py",
]


def run_test_file(filename: str) -> tuple[bool, str, float]:
    """Run a single test file and return (success, output, duration)."""
    filepath = TESTS_DIR / filename
    if not filepath.exists():
        return False, f"File not found: {filepath}", 0.0

    start = time.time()
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(filepath)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            cwd=str(filepath.parent.parent),
            env=env,
        )
        duration = time.time() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output, duration
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return False, f"TIMEOUT after {duration:.1f}s", duration
    except Exception as e:
        duration = time.time() - start
        return False, f"ERROR: {e}", duration


def extract_results(output: str) -> tuple[int, int]:
    """Extract passed/failed counts from test output."""
    import re
    # Match patterns like "182/182 passed" or "181 passed, 1 failed / 182 total"
    passed_match = re.search(r"(\d+)/(\d+) passed", output)
    if passed_match:
        passed = int(passed_match.group(1))
        total = int(passed_match.group(2))
        failed = total - passed
        return passed, failed

    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    return passed, failed


def main():
    print(f"\n{BOLD}{'='*60}")
    print(f"  NeSygma — Run All Tests")
    print(f"{'='*60}{RESET}\n")

    total_passed = 0
    total_failed = 0
    total_duration = 0.0
    results = []

    for filename in TEST_FILES:
        print(f"{CYAN}▶ Running {filename}...{RESET}")
        success, output, duration = run_test_file(filename)
        total_duration += duration

        passed, failed = extract_results(output)
        total_passed += passed
        total_failed += failed

        status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
        count_str = f"{passed} passed"
        if failed > 0:
            count_str += f", {RED}{failed} failed{RESET}"

        print(f"  {status}  {count_str}  ({duration:.1f}s)")
        results.append((filename, success, passed, failed, duration))

        # Print last few lines of output for failed tests
        if not success:
            lines = output.strip().split("\n")
            # Find the results line
            for line in lines:
                if "failed" in line.lower() or "error" in line.lower():
                    print(f"    {YELLOW}{line.strip()}{RESET}")

    # Summary
    print(f"\n{BOLD}{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}{RESET}\n")

    for filename, success, passed, failed, duration in results:
        status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        name = filename.replace("test_", "").replace(".py", "").ljust(20)
        print(f"  {status} {name} {passed:>4} passed" + (f", {RED}{failed} failed{RESET}" if failed else "") + f"  ({duration:.1f}s)")

    print(f"\n{'─'*60}")
    all_pass = total_failed == 0
    if all_pass:
        print(f"  {GREEN}{BOLD}ALL TESTS PASSED{RESET}")
    else:
        print(f"  {RED}{BOLD}SOME TESTS FAILED{RESET}")

    print(f"  Total: {total_passed} passed, {total_failed} failed ({total_passed + total_failed} tests)")
    print(f"  Duration: {total_duration:.1f}s")
    print(f"{'─'*60}\n")

    return 0 if all_pass else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)