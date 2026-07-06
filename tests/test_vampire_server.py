import asyncio
import os
import signal
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR))

import vampire_mcp_server.vampire_logic as vampire_logic_module
from vampire_mcp_server.vampire_logic import write_and_run_vampire_logic
from vampire_mcp_server.helpers import sanitize_filename, _terminate_process

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0


class FakeProcess:
    """Minimal async subprocess stub for Vampire edge-case tests."""

    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
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


# ═════════════════════════════ SANITIZE FILENAME ═════════════════════════

async def test_sanitize_strips_path_traversal():
    """Path traversal attempt is stripped down to safe basename."""
    safe = sanitize_filename("../../etc/passwd")
    ok = "/" not in safe and "\\" not in safe and safe.endswith(".p")
    report("Sanitize strips path traversal", ok, f"Got: {safe}")


async def test_sanitize_adds_extension():
    """Missing .p extension is auto-appended."""
    safe = sanitize_filename("myfile")
    ok = safe == "myfile.p"
    report("Sanitize auto-appends .p", ok, f"Got: {safe}")


async def test_sanitize_preserves_extension():
    """Existing .p extension is preserved (not doubled)."""
    safe = sanitize_filename("myfile.p")
    ok = safe == "myfile.p"
    report("Sanitize preserves existing .p", ok, f"Got: {safe}")


async def test_sanitize_special_chars():
    """Special characters in filename are replaced with underscores."""
    safe = sanitize_filename("my file (1).p")
    ok = " " not in safe and "(" not in safe and ")" not in safe and safe.endswith(".p")
    report("Sanitize replaces special chars", ok, f"Got: {safe}")


async def test_sanitize_empty_string():
    """Empty filename should still produce a valid .p filename."""
    safe = sanitize_filename("")
    ok = safe.endswith(".p") and len(safe) > 2
    report("Sanitize handles empty string", ok, f"Got: {safe}")


async def test_sanitize_dot_p_only():
    """Filename '.p' should be handled (produces 'proof.p')."""
    safe = sanitize_filename(".p")
    ok = safe.endswith(".p") and safe != ".p"
    report("Sanitize '.p' -> fallback name", ok, f"Got: {safe}")


async def test_sanitize_double_extension():
    """File with non-.p extension gets .p appended."""
    safe = sanitize_filename("script.txt")
    ok = safe.endswith(".p") and "txt" in safe
    report("Non-.p extension -> .p appended", ok, f"Got: {safe}")


async def test_sanitize_long_filename():
    """Very long filename should be handled."""
    safe = sanitize_filename("a" * 500 + ".p")
    ok = safe.endswith(".p") and "/" not in safe
    report("Sanitize long filename -> handled", ok, f"Length: {len(safe)}")


# ═════════════════════════════ HAPPY PATH PROOFS ═════════════════════════

async def test_provable_theorem():
    """Happy path: valid TPTP code -> Proof found."""
    code = """
fof(my_axiom, axiom, p).
fof(my_conjecture, conjecture, p).
"""
    r = await write_and_run_vampire_logic("test_provable.p", code, "test_provable_neg.p", code)
    res = r["positive"]
    ok = res["status"] == "success" and res.get("szs_status") == "Theorem"
    report("Valid TPTP -> Theorem proved (status=success)", ok, str(res) if not ok else "")


async def test_multi_step_proof():
    """Multi-step FOL reasoning: mortal(socrates) from human(socrates) + all humans mortal."""
    code = """
fof(all_humans_mortal, axiom, ![X]: (human(X) => mortal(X))).
fof(socrates_human, axiom, human(socrates)).
fof(goal, conjecture, mortal(socrates)).
"""
    r = await write_and_run_vampire_logic("test_socrates.p", code, "test_socrates_neg.p", code)
    res = r["positive"]
    ok = res["status"] == "success" and res.get("szs_status") == "Theorem"
    report("Socrates mortality proof -> Theorem", ok, str(res) if not ok else "")


async def test_unprovable_theorem():
    """Unprovable conjecture -> CounterSatisfiable (no proof exists)."""
    code = """
fof(my_axiom, axiom, p).
fof(my_conjecture, conjecture, q).
"""
    r = await write_and_run_vampire_logic("test_unprovable.p", code, "test_unprovable_neg.p", code)
    res = r["positive"]
    ok = res["status"] == "success" and res.get("szs_status") == "CounterSatisfiable"
    report("Unprovable TPTP -> CounterSatisfiable (status=success)", ok, str(res) if not ok else "")


async def test_refutation_unsatisfiable():
    """CNF refutation with negated_conjecture -> Unsatisfiable (proof found)."""
    code = """
cnf(man_socrates, axiom, man(socrates)).
cnf(mortal_rule, axiom, (~man(X) | mortal(X))).
cnf(goal_negated, negated_conjecture, ~mortal(socrates)).
"""
    r = await write_and_run_vampire_logic("test_refutation.p", code, "test_refutation_neg.p", code)
    res = r["positive"]
    ok = res["status"] == "success" and res.get("szs_status") in ("Unsatisfiable", "Theorem")
    report("Refutation style -> Unsatisfiable/Theorem (status=success)", ok, str(res) if not ok else "")


async def test_negation_proof():
    """Proving a negative: ~mammal(tweety) from bird(tweety) + no birds are mammals."""
    code = """
fof(no_birds_mammals, axiom, ![X]: (bird(X) => ~mammal(X))).
fof(tweety_bird, axiom, bird(tweety)).
fof(goal, conjecture, ~mammal(tweety)).
"""
    r = await write_and_run_vampire_logic("test_negation.p", code, "test_negation_neg.p", code)
    res = r["positive"]
    ok = res["status"] == "success" and res.get("szs_status") == "Theorem"
    report("Negation proof -> Theorem", ok, str(res) if not ok else "")


async def test_equality_reasoning():
    """Uniqueness/equality: owns(alice, fluffy) + owns(alice, pet_x) + unique_owner -> fluffy=pet_x."""
    code = """
fof(unique_owner, axiom, ![X,Y,Z]: ((owns(X,Y) & owns(X,Z)) => Y = Z)).
fof(alice_owns_fluffy, axiom, owns(alice, fluffy)).
fof(alice_owns_pet_x, axiom, owns(alice, pet_x)).
fof(goal, conjecture, fluffy = pet_x).
"""
    r = await write_and_run_vampire_logic("test_equality.p", code, "test_equality_neg.p", code)
    res = r["positive"]
    ok = res["status"] == "success" and res.get("szs_status") == "Theorem"
    report("Equality reasoning -> Theorem", ok, str(res) if not ok else "")


# ═════════════════════════════ SZS STATUS CLASSIFICATION ═════════════════

async def test_szs_theorem_nonzero_exit():
    """Vampire exit code 1 with SZS Theorem should be status='success', not 'error'."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status Theorem for test\n% SZS output start Proof\nsome proof lines\n% SZS output end Proof\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=1)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_exit1.p", "fof(a, axiom, p). fof(g, conjecture, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("szs_status") == "Theorem"
        report("Exit code 1 + SZS Theorem -> status=success (not error)", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_countersatisfiable_nonzero_exit():
    """CounterSatisfiable with non-zero exit should still be status='success'."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status CounterSatisfiable for test\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=1)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_countersat.p", "fof(a, axiom, p). fof(g, conjecture, q).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("szs_status") == "CounterSatisfiable"
        report("Exit code 1 + SZS CounterSatisfiable -> status=success", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_satisfiable_exit_zero():
    """Satisfiable with exit code 0 -> success."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status Satisfiable for test\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=0)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_sat.p", "fof(a, axiom, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("szs_status") == "Satisfiable"
        report("Exit code 0 + SZS Satisfiable -> status=success", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_unknown_nonzero_exit():
    """Unknown SZS with non-zero exit -> error."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status Unknown for test\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=2)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_unknown.p", "fof(a, axiom, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "error" and res.get("szs_status") == "Unknown"
        report("Non-zero exit + SZS Unknown -> status=error", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_no_status_nonzero_exit():
    """No SZS status line + non-zero exit -> error."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"Some random output with no SZS line\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"parse error\n", returncode=1)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_none.p", "bad syntax here", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "error" and res.get("szs_status") == "Unknown"
        report("No SZS line + non-zero exit -> error + Unknown", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_contradictory_axioms():
    """ContradictoryAxioms should be treated as success."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status ContradictoryAxioms for test\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=1)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_contra.p", "fof(a, axiom, p & ~p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("szs_status") == "ContradictoryAxioms"
        report("SZS ContradictoryAxioms -> status=success", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ ERROR HANDLING ════════════════════════════

async def test_syntax_error():
    """Invalid syntax -> error or parsing failure in Vampire."""
    code = """
this is not valid tptp syntax at all
"""
    r = await write_and_run_vampire_logic("test_syntax.p", code, "neg.p", "")
    res = r["positive"]
    ok = "error" in res["status"].lower() or "User error" in res.get("stdout", "")
    report("Invalid syntax -> Error handled", ok, str(res) if not ok else "")


async def test_crlf_normalization():
    """CRLF should be normalized to LF."""
    code = "fof(a, axiom, p).\r\nfof(g, conjecture, p).\r\n"
    r = await write_and_run_vampire_logic("test_crlf.p", code, "neg.p", "")
    filepath = Path(vampire_logic_module.WORKSPACE) / "test_crlf.p"
    content = filepath.read_text(encoding="utf-8")
    ok = "\r\n" not in content
    report("CRLF normalized to LF", ok, f"Content still has CRLF" if not ok else "")


async def test_stdout_filtering():
    """Vampire banner lines (Version, Linked, etc.) should be filtered from stdout."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = (
            b"% Version: Vampire 4.8\n"
            b"% Linked with Z3 library\n"
            b"% CaDiCaL version: 1.5\n"
            b"% Running in auto input_syntax mode\n"
            b"% Time elapsed: 0.001s\n"
            b"% Peak memory usage: 10MB\n"
            b"% ------------------------------\n"
            b"% SZS status Theorem for test\n"
            b"Important proof line here\n"
        )
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=0)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_filter.p", "fof(a, axiom, p). fof(g, conjecture, p).", "neg.p", "")
        res = r["positive"]
        out = res.get("stdout", "")
        ok = (
            "Version" not in out
            and "Linked" not in out
            and "CaDiCaL" not in out
            and "Time elapsed" not in out
            and "Peak memory" not in out
            and "SZS status Theorem" in out
            and "Important proof line" in out
        )
        report("Vampire banner lines filtered, SZS + proof kept", ok, f"stdout: {out[:200]}" if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ TIMEOUTS ══════════════════════════════════

async def test_timeout_cancels_solve():
    """Ensure that the execution raises a timeout error gracefully."""
    original_timeout = vampire_logic_module.QUERY_TIMEOUT
    original_wait_for = vampire_logic_module.asyncio.wait_for
    try:
        vampire_logic_module.QUERY_TIMEOUT = 0.001

        async def _always_timeout(awaitable, timeout=None):
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.TimeoutError()

        vampire_logic_module.asyncio.wait_for = _always_timeout
        code = """
fof(my_axiom, axiom, p).
fof(my_conjecture, conjecture, p).
"""
        r = await write_and_run_vampire_logic("test_timeout.p", code, "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "timeout"
        report("Vampire timeout triggers cancellation", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.wait_for = original_wait_for
        vampire_logic_module.QUERY_TIMEOUT = original_timeout


async def test_timeout_reports_correct_seconds():
    """Timeout error message should contain the configured timeout value."""
    original_timeout = vampire_logic_module.QUERY_TIMEOUT
    original_wait_for = vampire_logic_module.asyncio.wait_for
    try:
        vampire_logic_module.QUERY_TIMEOUT = 42

        async def _always_timeout(awaitable, timeout=None):
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.TimeoutError()

        vampire_logic_module.asyncio.wait_for = _always_timeout
        r = await write_and_run_vampire_logic("test_timeout_msg.p", "fof(a, axiom, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "timeout" and "42s" in res.get("error", "")
        report("Timeout error contains '42s'", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.wait_for = original_wait_for
        vampire_logic_module.QUERY_TIMEOUT = original_timeout


# ═════════════════════════════ PROCESS TERMINATION ═══════════════════════

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
    """_terminate_process should try CTRL_BREAK first, then fall back to kill."""
    class HangingProcess:
        def __init__(self):
            self.returncode = None
            self.signal_sent = None
            self.killed = False
            self.wait_calls = 0

        async def wait(self):
            self.wait_calls += 1
            if self.wait_calls == 1:
                await asyncio.sleep(5)
            self.returncode = -9
            return -9

        def send_signal(self, sig):
            self.signal_sent = sig

        def kill(self):
            self.killed = True
            self.returncode = -9

    proc = HangingProcess()
    await _terminate_process(proc)
    ok = proc.signal_sent == signal.CTRL_BREAK_EVENT and proc.killed and proc.wait_calls >= 2
    report("Terminate: CTRL_BREAK then kill on timeout", ok, str(vars(proc)) if not ok else "")


# ═════════════════════════════ WSL COMMAND CHECK ═════════════════════════

async def test_vampire_command_linux_apple():
    """Verify that Vampire is invoked without WSL on Linux/Apple."""
    original_platform = sys.platform
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    
    captured_args = None
    async def _fake(*args, **kwargs):
        nonlocal captured_args
        captured_args = args
        return FakeProcess(b"% SZS status Theorem for test\n", b"", returncode=0)
    
    try:
        sys.platform = "linux"
        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        
        await write_and_run_vampire_logic("test_linux.p", "fof(a, axiom, p).", "neg.p", "")
        
        ok = captured_args and captured_args[0] == "vampire" and "wsl" not in captured_args
        report("Vampire invoked directly on Linux/Apple (no wsl)", ok, f"Args: {captured_args}")
    finally:
        sys.platform = original_platform
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_vampire_command_windows():
    """Verify that Vampire is invoked via WSL on Windows."""
    original_platform = sys.platform
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    
    captured_args = None
    captured_kwargs = None
    async def _fake(*args, **kwargs):
        nonlocal captured_args, captured_kwargs
        captured_args = args
        captured_kwargs = kwargs
        return FakeProcess(b"% SZS status Theorem for test\n", b"", returncode=0)
    
    try:
        sys.platform = "win32"
        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        
        await write_and_run_vampire_logic("test_win.p", "fof(a, axiom, p).", "neg.p", "")
        
        ok = captured_args and captured_args[0] == "wsl" and captured_args[1] == "vampire"
        ok = ok and "creationflags" in captured_kwargs
        report("Vampire invoked via WSL on Windows", ok, f"Args: {captured_args}")
    finally:
        sys.platform = original_platform
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ ADDITIONAL EDGE CASES ═════════════════════

async def test_szs_exit_zero_no_szs():
    """Exit code 0 with no SZS line should be success (returncode==0)."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"Some output without SZS\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=0)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_exit0_noszs.p", "fof(a, axiom, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("szs_status") == "Unknown"
        report("Exit code 0 + no SZS -> status=success (returncode==0)", ok, str(res) if not ok else "")
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_stderr_preserved():
    """Non-empty stderr should be preserved in result."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status Theorem for test\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"warning: something\n", returncode=0)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_stderr.p", "fof(a, axiom, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("stderr") is not None and "warning" in res["stderr"]
        report("Non-empty stderr -> preserved in result", ok)
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_szs_empty_stderr_is_none():
    """Empty stderr should be set to None."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = b"% SZS status Theorem for test\n"
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=0)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_empty_stderr.p", "fof(a, axiom, p).", "neg.p", "")
        res = r["positive"]
        ok = res["status"] == "success" and res.get("stderr") is None
        report("Empty stderr -> stderr is None", ok)
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


async def test_write_and_run_returns_both():
    """write_and_run_vampire_logic should return both positive and negative results."""
    code = "fof(a, axiom, p). fof(g, conjecture, p)."
    r = await write_and_run_vampire_logic("test_both.p", code, "test_both_neg.p", code)
    ok = "positive" in r and "negative" in r and isinstance(r["positive"], dict) and isinstance(r["negative"], dict)
    report("write_and_run returns both positive and negative dicts", ok)


async def test_szs_output_start_end_filtered():
    """SZS output start/end markers should be kept (not filtered)."""
    original_create = vampire_logic_module.asyncio.create_subprocess_exec
    try:
        stdout = (
            b"% SZS status Theorem for test\n"
            b"% SZS output start Proof\n"
            b"1. p [input]\n"
            b"% SZS output end Proof\n"
        )
        async def _fake(*args, **kwargs):
            return FakeProcess(stdout, b"", returncode=0)

        vampire_logic_module.asyncio.create_subprocess_exec = _fake
        r = await write_and_run_vampire_logic("test_szs_markers.p", "fof(a, axiom, p).", "neg.p", "")
        out = r["positive"].get("stdout", "")
        ok = "SZS output start" in out and "SZS output end" in out
        report("SZS output start/end markers preserved in stdout", ok)
    finally:
        vampire_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ MAIN ══════════════════════════════════════

async def main():
    print(f"\n{BOLD}=== Vampire MCP Server - Comprehensive Edge Case Tests ==={RESET}\n")

    tests = [
        ("Filename Sanitization", [
            test_sanitize_strips_path_traversal,
            test_sanitize_adds_extension,
            test_sanitize_preserves_extension,
            test_sanitize_special_chars,
            test_sanitize_empty_string,
            test_sanitize_dot_p_only,
            test_sanitize_double_extension,
            test_sanitize_long_filename,
        ]),
        ("Happy Path Proofs", [
            test_provable_theorem,
            test_multi_step_proof,
            test_unprovable_theorem,
            test_refutation_unsatisfiable,
            test_negation_proof,
            test_equality_reasoning,
        ]),
        ("SZS Status Classification (Bug Fix #9)", [
            test_szs_theorem_nonzero_exit,
            test_szs_countersatisfiable_nonzero_exit,
            test_szs_satisfiable_exit_zero,
            test_szs_unknown_nonzero_exit,
            test_szs_no_status_nonzero_exit,
            test_szs_contradictory_axioms,
        ]),
        ("Error Handling", [
            test_syntax_error,
            test_crlf_normalization,
            test_stdout_filtering,
        ]),
        ("Timeouts", [
            test_timeout_cancels_solve,
            test_timeout_reports_correct_seconds,
        ]),
        ("Process Termination", [
            test_terminate_already_exited,
            test_terminate_graceful_then_kill,
        ]),
        ("Command Structure (Cross-Platform)", [
            test_vampire_command_linux_apple,
            test_vampire_command_windows,
        ]),
        ("Additional Edge Cases", [
            test_szs_exit_zero_no_szs,
            test_szs_stderr_preserved,
            test_szs_empty_stderr_is_none,
            test_write_and_run_returns_both,
            test_szs_output_start_end_filtered,
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