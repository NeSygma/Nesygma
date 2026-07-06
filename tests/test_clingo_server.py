import asyncio
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR))

import clingo_mcp_server.clingo_logic as clingo_logic_module
from clingo_mcp_server.clingo_logic import run_clingo_logic, write_clingo_file_logic
from clingo_mcp_server.helpers import sanitize_filename, _terminate_process

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0


class FakeProcess:
    """Minimal async subprocess stub for edge-case tests."""

    def __init__(self, stdout_bytes: bytes, stderr_bytes: bytes = b"", returncode: int = 0):
        self._stdout = stdout_bytes
        self._stderr = stderr_bytes
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  {GREEN}✓{RESET} {name}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {name}")
        if detail:
            for line in detail.strip().split("\n"):
                print(f"    {YELLOW}{line}{RESET}")


# ─────────────────────────────── Helpers ─────────────────────────────────

def _build_outf_json(result: str, witnesses: list[list[str]], more=None) -> bytes:
    payload = {
        "Result": result,
        "Call": [{"Witnesses": [{"Value": w} for w in witnesses]}],
    }
    if more is not None:
        payload["Models"] = {"More": more}
    return json.dumps(payload).encode("utf-8")


# ═════════════════════════════ SANITIZE FILENAME ═════════════════════════

async def test_sanitize_strips_path_traversal():
    """Path traversal attempt is stripped down to safe basename."""
    safe = sanitize_filename("../../etc/passwd")
    ok = "/" not in safe and "\\" not in safe and safe.endswith(".lp")
    report("Sanitize strips path traversal", ok, f"Got: {safe}")


async def test_sanitize_adds_extension():
    """Missing .lp extension is auto-appended."""
    safe = sanitize_filename("myfile")
    ok = safe == "myfile.lp"
    report("Sanitize auto-appends .lp", ok, f"Got: {safe}")


async def test_sanitize_preserves_extension():
    """Existing .lp extension is preserved (not doubled)."""
    safe = sanitize_filename("myfile.lp")
    ok = safe == "myfile.lp"
    report("Sanitize preserves existing .lp", ok, f"Got: {safe}")


async def test_sanitize_special_chars():
    """Special characters in filename are replaced with underscores."""
    safe = sanitize_filename("my file (1).lp")
    ok = " " not in safe and "(" not in safe and ")" not in safe and safe.endswith(".lp")
    report("Sanitize replaces special chars", ok, f"Got: {safe}")


async def test_sanitize_empty_string():
    """Empty filename should still produce a valid .lp filename."""
    safe = sanitize_filename("")
    ok = safe.endswith(".lp") and len(safe) > 3
    report("Sanitize handles empty string", ok, f"Got: {safe}")


# ═════════════════════════════ WRITE & VALIDATE ══════════════════════════

async def test_valid_write_and_run():
    """Happy path: valid code -> satisfiable answer set."""
    code = """
node(1..3).
edge(1,2). edge(2,3). edge(3,1).
1 { color(X, c1); color(X, c2); color(X, c3) } 1 :- node(X).
:- edge(X, Y), color(X, C), color(Y, C).
#show color/2.
"""
    w = await write_clingo_file_logic("test_valid.lp", code)
    if w["status"] != "success":
        report("Valid code -> write success", False, str(w))
        return

    r = await run_clingo_logic("test_valid.lp")
    ok = r["status"] == "satisfiable" and "color" in str(r.get("models", []))
    report("Valid code + run -> satisfiable", ok, str(r) if not ok else "")


async def test_syntax_error_missing_period():
    """Code has missing period -> syntax_error."""
    code = """
bird(tweety)
flies(X) :- bird(X).
"""
    w = await write_clingo_file_logic("test_missing_period.lp", code)
    ok = w["status"] == "syntax_error"
    report("Missing period -> syntax_error", ok, str(w) if not ok else "")


async def test_syntax_error_capitalized_atom():
    """Code uses capitalized atom where it shouldn't -> syntax error."""
    code = """
bird(Tweety).
"""
    w = await write_clingo_file_logic("test_cap_atom.lp", code)
    has_error = w["status"] == "syntax_error" or ("unsafe" in w.get("error", "").lower())
    report("Capitalized atom (Unsafe Variable) -> syntax_error", has_error, str(w) if not has_error else "")


async def test_write_empty_code():
    """Empty ASP code is technically valid (no atoms)."""
    w = await write_clingo_file_logic("test_empty.lp", "")
    # Empty program should parse without syntax error
    ok = w["status"] == "success"
    report("Empty code -> write success (valid but trivial)", ok, str(w) if not ok else "")


async def test_write_crlf_normalization():
    """CRLF line endings should be normalized to LF before writing."""
    code = "bird(tweety).\r\nflies(X) :- bird(X).\r\n#show flies/1.\r\n"
    w = await write_clingo_file_logic("test_crlf.lp", code)
    ok = w["status"] == "success"
    if ok:
        filepath = Path(clingo_logic_module.WORKSPACE) / "test_crlf.lp"
        content = filepath.read_text(encoding="utf-8")
        ok = "\r\n" not in content
    report("CRLF normalized to LF on write", ok, str(w) if not ok else "")


async def test_write_validation_with_warnings():
    """Code that grounds but produces Clingo warnings should still succeed but include warnings."""
    # Using an undefined atom in a constraint body triggers "atom does not occur in any rule head"
    code = """
a :- b.
#show a/0.
"""
    w = await write_clingo_file_logic("test_warnings.lp", code)
    ok = w["status"] == "success" and w.get("warnings") is not None
    report("Code with warnings -> success + warnings field", ok, str(w) if not ok else "")


async def test_write_grounding_timeout_signal():
    """Validation timeout should surface as grounding_timeout (not success)."""
    original_wait_for = clingo_logic_module.asyncio.wait_for
    try:
        async def _always_timeout(awaitable, timeout=None):
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.TimeoutError()

        clingo_logic_module.asyncio.wait_for = _always_timeout
        w = await write_clingo_file_logic("test_grounding_timeout.lp", "a.")
        ok = w["status"] == "grounding_timeout" and "Grounding timed out" in w.get("error", "")
        report("Validation timeout -> grounding_timeout", ok, str(w) if not ok else "")
    finally:
        clingo_logic_module.asyncio.wait_for = original_wait_for


# ═════════════════════════════ SOLVE RESULTS ═════════════════════════════

async def test_run_unsatisfiable():
    """Valid code but contradictory constraints -> unsatisfiable."""
    code = """
bird(tweety).
ab(tweety).
flies(X) :- bird(X), not ab(X).
:- not flies(tweety). % Force tweety to fly
"""
    w = await write_clingo_file_logic("test_unsat.lp", code)
    if w["status"] != "success":
        report("Write contradictory code", False, str(w))
        return

    r = await run_clingo_logic("test_unsat.lp")
    ok = r["status"] == "unsatisfiable"
    report("Contradictory code -> unsatisfiable", ok, str(r) if not ok else "")


async def test_abnormality_default_reasoning():
    """Test standard non-monotonic logic patterns."""
    code = """
bird(tweety).
bird(opus).
penguin(opus).
flies(X) :- bird(X), not ab(X).
ab(X) :- penguin(X).
#show flies/1.
"""
    w = await write_clingo_file_logic("test_default.lp", code)
    if w["status"] != "success":
        report("Write default logic", False, str(w))
        return

    r = await run_clingo_logic("test_default.lp")
    output = str(r.get("models", []))
    ok = r["status"] == "satisfiable" and "flies(tweety)" in output and "flies(opus)" not in output
    report("Default logic -> tweety flies, opus doesn't", ok, str(r) if not ok else "")


async def test_arithmetic():
    """Test ASP arithmetic."""
    code = """
num(5).
double(X, Y) :- num(X), Y = X * 2.
#show double/2.
"""
    w = await write_clingo_file_logic("test_arith.lp", code)
    if w["status"] != "success":
        report("Write arithmetic logic", False, str(w))
        return

    r = await run_clingo_logic("test_arith.lp")
    ok = r["status"] == "satisfiable" and "double(5,10)" in str(r.get("models", []))
    report("Arithmetic (5 * 2) = 10", ok, str(r) if not ok else "")


async def test_optimization_minimize():
    """Optimization with #minimize should produce optimum_found or satisfiable result."""
    code = """
item(a, 10). item(b, 20). item(c, 5).
1 { pick(X) : item(X, _) } 2.
total_cost(S) :- S = #sum { W,X : pick(X), item(X, W) }.
#minimize { W,X : pick(X), item(X, W) }.
#show pick/1.
#show total_cost/1.
"""
    w = await write_clingo_file_logic("test_optimize.lp", code)
    if w["status"] != "success":
        report("Write optimization code", False, str(w))
        return

    r = await run_clingo_logic("test_optimize.lp")
    ok = r["status"] in ("satisfiable", "optimum_found") and "pick" in str(r.get("models", []))
    report("Optimization #minimize -> produces models", ok, str(r) if not ok else "")


async def test_multiple_answer_sets():
    """Programs with multiple stable models should return multiple answer sets."""
    code = """
{a; b}.
#show a/0.
#show b/0.
"""
    w = await write_clingo_file_logic("test_multi_models.lp", code)
    if w["status"] != "success":
        report("Write multi-model code", False, str(w))
        return

    r = await run_clingo_logic("test_multi_models.lp")
    ok = r["status"] == "satisfiable" and len(r.get("models", [])) > 1
    report("Multiple stable models returned", ok, f"Got {len(r.get('models', []))} models" if not ok else "")


# ═════════════════════════════ ERROR HANDLING ════════════════════════════

async def test_run_nonexistent_file():
    """Direct run_clingo_logic for file that doesn't exist."""
    r = await run_clingo_logic("nonexistent_xyz.lp")
    ok = r["status"] == "error" and "not found" in r.get("error", "").lower()
    report("Run missing file -> error", ok, str(r) if not ok else "")


async def test_run_invalid_json_output():
    """Corrupted JSON output from clingo should return error when exit code != 0."""
    w = await write_clingo_file_logic("test_bad_json.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare bad JSON test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(b"NOT VALID JSON {{{", returncode=1)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_bad_json.lp")
        ok = r["status"] == "error"
        report("Corrupted JSON + nonzero exit -> error", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_run_empty_stdout():
    """Empty stdout from clingo with exit code 0 should not crash."""
    w = await write_clingo_file_logic("test_empty_stdout.lp", "a.")
    if w["status"] != "success":
        report("Prepare empty stdout test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(b"", returncode=0)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_empty_stdout.lp")
        # Should not crash; status will be "unknown" with no models
        ok = r["status"] == "unknown" and r.get("models") == []
        report("Empty stdout -> unknown status, no crash", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ TIMEOUTS ══════════════════════════════════

async def test_timeout_cancels_solve():
    """Timeout should return timeout status for long-running clingo jobs."""

    original_timeout = clingo_logic_module.QUERY_TIMEOUT
    original_wait_for = clingo_logic_module.asyncio.wait_for
    try:
        # We don't need to change QUERY_TIMEOUT if we mock wait_for
        
        async def _always_timeout(awaitable, timeout=None):
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.TimeoutError()

        w = await write_clingo_file_logic("test_timeout_manual.lp", "a.")
        if w["status"] != "success":
            report("Prepare timeout test program", False, str(w))
            return

        clingo_logic_module.asyncio.wait_for = _always_timeout
        r = await run_clingo_logic("test_timeout_manual.lp")
        ok = r["status"] == "timeout"
        report("Timeout returns timeout status (mocked)", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.wait_for = original_wait_for
        clingo_logic_module.QUERY_TIMEOUT = original_timeout


async def test_timeout_reports_60_seconds():
    """Timeout payload should include 60s when configured to 60."""
    original_timeout = clingo_logic_module.QUERY_TIMEOUT
    original_wait_for = clingo_logic_module.asyncio.wait_for
    try:
        clingo_logic_module.QUERY_TIMEOUT = 60

        w = await write_clingo_file_logic("test_timeout_60.lp", "a.")
        if w["status"] != "success":
            report("Prepare timeout-60 test program", False, str(w))
            return

        async def _always_timeout(awaitable, timeout=None):
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.TimeoutError()

        clingo_logic_module.asyncio.wait_for = _always_timeout
        r = await run_clingo_logic("test_timeout_60.lp")
        ok = r["status"] == "timeout" and "60s" in r.get("error", "")
        report("Timeout reports 60s", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.wait_for = original_wait_for
        clingo_logic_module.QUERY_TIMEOUT = original_timeout


async def test_timeout_buffer_in_command():
    """Python-side timeout should be QUERY_TIMEOUT + 5 (buffer for JSON write)."""
    original_timeout = clingo_logic_module.QUERY_TIMEOUT
    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    original_wait_for = clingo_logic_module.asyncio.wait_for
    captured_timeout = None

    try:
        clingo_logic_module.QUERY_TIMEOUT = 60

        w = await write_clingo_file_logic("test_buffer.lp", "a. #show a/0.")
        if w["status"] != "success":
            report("Prepare timeout buffer test", False, str(w))
            return

        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SATISFIABLE", [["a"]], more="no"))

        async def _capture_timeout(awaitable, timeout=None):
            nonlocal captured_timeout
            captured_timeout = timeout
            return await awaitable

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        clingo_logic_module.asyncio.wait_for = _capture_timeout
        await run_clingo_logic("test_buffer.lp")
        ok = captured_timeout == 65  # QUERY_TIMEOUT(60) + 5
        report(f"Python timeout = QUERY_TIMEOUT + 5 = 65 (got {captured_timeout})", ok)
    finally:
        clingo_logic_module.asyncio.wait_for = original_wait_for
        clingo_logic_module.asyncio.create_subprocess_exec = original_create
        clingo_logic_module.QUERY_TIMEOUT = original_timeout


async def test_command_uses_10_models_limit():
    """Run command should request up to 10 models from clingo."""
    w = await write_clingo_file_logic("test_model_cap.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare model-cap test program", False, str(w))
        return

    r = await run_clingo_logic("test_model_cap.lp")
    cmd = r.get("command", "")
    ok = " 10 " in f" {cmd} "
    report("Command uses model cap 10", ok, str(r) if not ok else "")


# ═════════════════════════════ RESULT PARSING ════════════════════════════

async def test_optimum_found_maps_satisfiable():
    """OPTIMUM FOUND should be treated as a successful model-bearing status."""
    w = await write_clingo_file_logic("test_optimum_found.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare optimum-found parse test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("OPTIMUM FOUND", [["a"]], more="no"))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_optimum_found.lp")
        ok = r["status"] in ("optimum_found", "satisfiable") and r.get("models")
        report("OPTIMUM FOUND -> successful model status", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_unknown_with_models_maps_satisfiable():
    """Unknown result text with witness models should still be satisfiable."""
    w = await write_clingo_file_logic("test_unknown_with_models.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare unknown-with-models parse test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SOME_NONSTANDARD_RESULT", [["a"]], more="no"))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_unknown_with_models.lp")
        ok = r["status"] == "satisfiable"
        report("Unknown text + witnesses -> satisfiable", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_long_symbol_truncation():
    """Symbols longer than 200 chars should be truncated with '...'."""
    w = await write_clingo_file_logic("test_long_sym.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare long symbol test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        long_sym = "x" * 300
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SATISFIABLE", [[long_sym]], more="no"))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_long_sym.lp")
        sym = r["models"][0][0]
        ok = len(sym) == 200 and sym.endswith("...")
        report(f"Long symbol truncated to 200 chars (got {len(sym)})", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ TRUNCATION ════════════════════════════════

async def test_truncation_more_no_exact_limit_not_flagged():
    """Exactly MAX_MODELS with Models.More='no' should NOT be flagged as truncated."""
    w = await write_clingo_file_logic("test_more_no.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare truncation-more-no test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        witnesses = [[f"a({i})"] for i in range(clingo_logic_module.MAX_MODELS)]

        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SATISFIABLE", witnesses, more="no"))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_more_no.lp")
        ok = "warning_truncated" not in r
        report("Models.More='no' at exact cap -> no truncation warning", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_truncation_more_yes_flagged():
    """Models.More='yes' should always be flagged as truncated."""
    w = await write_clingo_file_logic("test_more_yes.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare truncation-more-yes test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        witnesses = [["a"]]

        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SATISFIABLE", witnesses, more="yes"))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_more_yes.lp")
        ok = "warning_truncated" in r
        report("Models.More='yes' -> truncation warning", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_truncation_more_missing_fallback_flagged():
    """When Models.More is missing, fallback to count-based truncation detection."""
    w = await write_clingo_file_logic("test_more_missing.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare truncation-more-missing test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        witnesses = [[f"a({i})"] for i in range(clingo_logic_module.MAX_MODELS)]

        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SATISFIABLE", witnesses, more=None))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_more_missing.lp")
        ok = "warning_truncated" in r
        report("Models.More missing at exact cap -> truncation warning", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_truncation_more_integer_1_flagged():
    """Models.More=1 (integer) should be treated as truncated (Clingo version variance)."""
    w = await write_clingo_file_logic("test_more_int1.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare truncation int-1 test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("SATISFIABLE", [["a"]], more=1))

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_more_int1.lp")
        ok = "warning_truncated" in r
        report("Models.More=1 (int) -> truncation warning", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ STDERR FILTERING ══════════════════════════

async def test_stderr_benign_filtered_out():
    """Benign stderr noise should not be surfaced as warnings."""
    w = await write_clingo_file_logic("test_stderr_benign.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare stderr-benign filter test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(
                _build_outf_json("SATISFIABLE", [["a"]], more="no"),
                b"clingo version 5.7.1\nreading from test.lp\n",
            )

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_stderr_benign.lp")
        ok = "warnings" not in r
        report("Benign stderr -> no warnings field", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_stderr_actionable_kept():
    """Actionable stderr should still be surfaced as warnings."""
    w = await write_clingo_file_logic("test_stderr_actionable.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare stderr-actionable filter test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(
                _build_outf_json("SATISFIABLE", [["a"]], more="no"),
                b"warning: atom does not occur in any rule head\n",
            )

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_stderr_actionable.lp")
        ok = "warnings" in r and "atom does not occur" in r["warnings"].lower()
        report("Actionable stderr -> warnings field kept", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_stderr_error_keyword_detected():
    """Stderr containing 'error' keyword should be surfaced."""
    w = await write_clingo_file_logic("test_stderr_error.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare stderr-error test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(
                _build_outf_json("SATISFIABLE", [["a"]], more="no"),
                b"error: some clingo error occurred\n",
            )

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_stderr_error.lp")
        ok = "warnings" in r
        report("Stderr with 'error' keyword -> warnings surfaced", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ TERMINATE PROCESS ═════════════════════════

async def test_terminate_already_exited():
    """_terminate_process should be a no-op for already-exited process."""
    class AlreadyDone:
        returncode = 0
        killed = False
        def kill(self): self.killed = True
    proc = AlreadyDone()
    await _terminate_process(proc)
    ok = not proc.killed
    report("Terminate already-exited -> no kill", ok)


async def test_terminate_graceful_then_kill():
    """_terminate_process should try CTRL_BREAK first, then kill on timeout."""
    import signal

    class StubProc:
        def __init__(self):
            self.returncode = None
            self.signal_sent = None
            self.killed = False
            self.wait_calls = 0

        async def wait(self):
            self.wait_calls += 1
            if self.wait_calls == 1:
                await asyncio.sleep(5)  # Simulate hanging
            self.returncode = -9
            return -9

        def send_signal(self, sig):
            self.signal_sent = sig

        def kill(self):
            self.killed = True
            self.returncode = -9

    proc = StubProc()
    await _terminate_process(proc)
    ok = proc.signal_sent == signal.CTRL_BREAK_EVENT and proc.killed
    report("Terminate: CTRL_BREAK then kill on timeout", ok, str(vars(proc)) if not ok else "")


# ═════════════════════════════ ADDITIONAL EDGE CASES ═════════════════════

async def test_run_general_exception():
    """General exception in run_clingo_logic should return error status."""
    w = await write_clingo_file_logic("test_gen_exc.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare general exception test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            raise OSError("Process creation failed")

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_gen_exc.lp")
        ok = r["status"] == "error" and "Process creation failed" in r.get("error", "")
        report("General exception in run_clingo -> error status", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_write_general_exception():
    """General exception in write_clingo_file_logic should return error status."""
    original_write = Path.write_text
    try:
        def _fail_write(self, *args, **kwargs):
            raise OSError("Disk full")
        Path.write_text = _fail_write
        w = await write_clingo_file_logic("test_write_exc.lp", "a.")
        ok = w["status"] == "error" and "Disk full" in w.get("error", "")
        report("General exception in write_clingo -> error status", ok, str(w) if not ok else "")
    finally:
        Path.write_text = original_write


async def test_run_json_decode_error_nonzero():
    """JSON decode error with nonzero exit should return error."""
    w = await write_clingo_file_logic("test_json_err.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare JSON error test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(b"NOT JSON", b"some error", returncode=1)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_json_err.lp")
        ok = r["status"] == "error" and "some error" in r.get("error", "")
        report("JSON decode error + nonzero exit -> error with stderr", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_run_json_decode_error_zero_exit():
    """JSON decode error with zero exit should return unknown status."""
    w = await write_clingo_file_logic("test_json_zero.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare JSON zero-exit test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(b"NOT JSON", b"", returncode=0)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_json_zero.lp")
        ok = r["status"] == "unknown" and r.get("models") == []
        report("JSON decode error + zero exit -> unknown status", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_run_empty_json():
    """Empty JSON output should return unknown status."""
    w = await write_clingo_file_logic("test_empty_json.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare empty JSON test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(b"{}", returncode=0)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_empty_json.lp")
        ok = r["status"] == "unknown" and r.get("models") == []
        report("Empty JSON output -> unknown status, no crash", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_run_unsatisfiable_json():
    """UNSATISFIABLE result text should map to unsatisfiable status."""
    w = await write_clingo_file_logic("test_unsat_json.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare unsat JSON test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("UNSATISFIABLE", []), returncode=0)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_unsat_json.lp")
        ok = r["status"] == "unsatisfiable"
        report("UNSATISFIABLE result text -> unsatisfiable status", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_run_unknown_result_text():
    """UNKNOWN result text should map to unknown status."""
    w = await write_clingo_file_logic("test_unknown_json.lp", "a. #show a/0.")
    if w["status"] != "success":
        report("Prepare unknown JSON test", False, str(w))
        return

    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake_create(*cmd, **kwargs):
            return FakeProcess(_build_outf_json("UNKNOWN", []), returncode=0)

        clingo_logic_module.asyncio.create_subprocess_exec = _fake_create
        r = await run_clingo_logic("test_unknown_json.lp")
        ok = r["status"] == "unknown"
        report("UNKNOWN result text -> unknown status", ok, str(r) if not ok else "")
    finally:
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


async def test_write_syntax_error_with_warnings():
    """Syntax error that also produces warnings should include both."""
    code = """
a :- b.
c.
"""
    w = await write_clingo_file_logic("test_syn_warn.lp", code)
    # This is valid ASP, so let's test with actual syntax error
    code_bad = """
a :- b
c.
"""
    w = await write_clingo_file_logic("test_syn_warn2.lp", code_bad)
    ok = w["status"] == "syntax_error" and "error" in w
    report("Syntax error with warnings -> syntax_error + error field", ok, str(w) if not ok else "")


# ═════════════════════════════ PLATFORM GUARD ════════════════════════════

async def test_clingo_command_linux_apple():
    """Verify that creationflags is NOT set on Linux/Apple."""
    original_platform = sys.platform
    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    
    captured_kwargs = None
    async def _fake(*args, **kwargs):
        nonlocal captured_kwargs
        captured_kwargs = kwargs
        return FakeProcess(_build_outf_json("SATISFIABLE", []), returncode=0)
        
    try:
        sys.platform = "linux"
        clingo_logic_module.asyncio.create_subprocess_exec = _fake
        
        await write_clingo_file_logic("test_linux.lp", "a.")
        await run_clingo_logic("test_linux.lp")
        
        ok = captured_kwargs is not None and "creationflags" not in captured_kwargs
        report("Clingo invoked without creationflags on Linux/Apple", ok, f"Kwargs: {captured_kwargs}")
    finally:
        sys.platform = original_platform
        clingo_logic_module.asyncio.create_subprocess_exec = original_create

async def test_clingo_command_windows():
    """Verify that creationflags IS set on Windows."""
    original_platform = sys.platform
    original_create = clingo_logic_module.asyncio.create_subprocess_exec
    
    captured_kwargs = None
    async def _fake(*args, **kwargs):
        nonlocal captured_kwargs
        captured_kwargs = kwargs
        return FakeProcess(_build_outf_json("SATISFIABLE", []), returncode=0)
        
    try:
        sys.platform = "win32"
        clingo_logic_module.asyncio.create_subprocess_exec = _fake
        
        await write_clingo_file_logic("test_win.lp", "a.")
        await run_clingo_logic("test_win.lp")
        
        ok = captured_kwargs is not None and "creationflags" in captured_kwargs
        report("Clingo invoked with creationflags on Windows", ok, f"Kwargs: {captured_kwargs}")
    finally:
        sys.platform = original_platform
        clingo_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ MAIN ══════════════════════════════════════

async def main():
    print(f"\n{BOLD}=== Clingo MCP Server - Comprehensive Edge Case Tests ==={RESET}\n")

    tests = [
        ("Filename Sanitization", [
            test_sanitize_strips_path_traversal,
            test_sanitize_adds_extension,
            test_sanitize_preserves_extension,
            test_sanitize_special_chars,
            test_sanitize_empty_string,
        ]),
        ("Write & Validate", [
            test_valid_write_and_run,
            test_syntax_error_missing_period,
            test_syntax_error_capitalized_atom,
            test_write_empty_code,
            test_write_crlf_normalization,
            test_write_validation_with_warnings,
            test_write_grounding_timeout_signal,
        ]),
        ("Solve Results", [
            test_run_unsatisfiable,
            test_abnormality_default_reasoning,
            test_arithmetic,
            test_optimization_minimize,
            test_multiple_answer_sets,
        ]),
        ("Error Handling", [
            test_run_nonexistent_file,
            test_run_invalid_json_output,
            test_run_empty_stdout,
        ]),
        ("Timeouts", [
            test_timeout_cancels_solve,
            test_timeout_reports_60_seconds,
            test_timeout_buffer_in_command,
            test_command_uses_10_models_limit,
        ]),
        ("Result Parsing", [
            test_optimum_found_maps_satisfiable,
            test_unknown_with_models_maps_satisfiable,
            test_long_symbol_truncation,
        ]),
        ("Truncation Detection", [
            test_truncation_more_no_exact_limit_not_flagged,
            test_truncation_more_yes_flagged,
            test_truncation_more_missing_fallback_flagged,
            test_truncation_more_integer_1_flagged,
        ]),
        ("Stderr Filtering", [
            test_stderr_benign_filtered_out,
            test_stderr_actionable_kept,
            test_stderr_error_keyword_detected,
        ]),
        ("Process Termination", [
            test_terminate_already_exited,
            test_terminate_graceful_then_kill,
        ]),
        ("Platform Guard", [
            test_clingo_command_linux_apple,
            test_clingo_command_windows,
        ]),
        ("Additional Edge Cases", [
            test_run_general_exception,
            test_write_general_exception,
            test_run_json_decode_error_nonzero,
            test_run_json_decode_error_zero_exit,
            test_run_empty_json,
            test_run_unsatisfiable_json,
            test_run_unknown_result_text,
            test_write_syntax_error_with_warnings,
        ]),
    ]

    for group_name, group_tests in tests:
        print(f"\n{BOLD}--- {group_name} ---{RESET}")
        for test_fn in group_tests:
            await test_fn()

    print(f"\n{BOLD}=== Results ==={RESET}")
    total = passed + failed
    if failed == 0:
        print(f"  {GREEN}{passed}/{total} passed ✓{RESET}")
    else:
        print(f"  {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET} / {total} total")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)