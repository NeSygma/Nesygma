import asyncio
import os
import signal
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR))

# Set short timeout for test speed BEFORE importing the module
os.environ["Z3_TIMEOUT"] = "2"

import z3_mcp_server.z3_logic as z3_logic_module
from z3_mcp_server.z3_logic import write_and_run_z3_logic
from z3_mcp_server.helpers import sanitize_filename, _terminate_process

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0


class FakeProcess:
    """Minimal async subprocess stub."""

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
    ok = "/" not in safe and "\\" not in safe and safe.endswith(".py")
    report("Sanitize strips path traversal", ok, f"Got: {safe}")


async def test_sanitize_adds_extension():
    """Missing .py extension is auto-appended."""
    safe = sanitize_filename("myfile")
    ok = safe == "myfile.py"
    report("Sanitize auto-appends .py", ok, f"Got: {safe}")


async def test_sanitize_preserves_extension():
    """Existing .py extension is preserved (not doubled)."""
    safe = sanitize_filename("myfile.py")
    ok = safe == "myfile.py"
    report("Sanitize preserves existing .py", ok, f"Got: {safe}")


async def test_sanitize_special_chars():
    """Special characters in filename are replaced with underscores."""
    safe = sanitize_filename("my file (1).py")
    ok = " " not in safe and "(" not in safe and ")" not in safe and safe.endswith(".py")
    report("Sanitize replaces special chars", ok, f"Got: {safe}")


async def test_sanitize_double_extension():
    """File with non-.py extension gets .py appended."""
    safe = sanitize_filename("script.txt")
    ok = safe.endswith(".py") and "txt" in safe
    report("Non-.py extension -> .py appended", ok, f"Got: {safe}")


# ═════════════════════════════ WRITE & RUN SUCCESS ═══════════════════════

async def test_valid_write_and_run():
    """Happy path: valid code -> satisfiable constraints."""
    code = """
from z3 import *
x = Int('x')
y = Int('y')
s = Solver()
s.add(x > 0)
s.add(y > 0)
s.add(x + y == 10)
if s.check() == sat:
    print("SAT")
    m = s.model()
    print(f"x={m[x]}, y={m[y]}")
"""
    w = await write_and_run_z3_logic("test_z3_valid.py", code)
    ok = w["status"] == "success" and "SAT" in w.get("stdout", "")
    report("Valid Z3 script -> success + SAT", ok, str(w) if not ok else "")


async def test_z3_unsat():
    """Contradictory logic outputs UNSAT"""
    code = """
from z3 import *
x = Int('x')
s = Solver()
s.add(x > 5)
s.add(x < 2)
if s.check() == unsat:
    print("UNSATISFIABLE")
"""
    w = await write_and_run_z3_logic("test_z3_unsat.py", code)
    ok = w["status"] == "success" and "UNSATISFIABLE" in w.get("stdout", "")
    report("Z3 logic contradiction -> outputs UNSAT", ok, str(w) if not ok else "")


async def test_z3_optimization():
    """Z3 Optimize() usage should work."""
    code = """
from z3 import *
opt = Optimize()
x = Int('x')
opt.add(x >= 0, x <= 100)
opt.maximize(x)
if opt.check() == sat:
    print(f"MAX={opt.model()[x]}")
"""
    w = await write_and_run_z3_logic("test_z3_opt.py", code)
    ok = w["status"] == "success" and "MAX=100" in w.get("stdout", "")
    report("Z3 Optimize maximize -> MAX=100", ok, str(w) if not ok else "")


async def test_z3_theorem_proving():
    """Theorem proving by contradiction."""
    code = """
from z3 import *
x = Int('x')
s = Solver()
s.add(Not(x * x >= 0))
result = s.check()
if result == unsat:
    print("THEOREM_TRUE")
else:
    print("THEOREM_FALSE")
"""
    w = await write_and_run_z3_logic("test_z3_theorem.py", code)
    ok = w["status"] == "success" and "THEOREM_TRUE" in w.get("stdout", "")
    report("Theorem proving x²≥0 by contradiction -> TRUE", ok, str(w) if not ok else "")


async def test_z3_distinct():
    """Distinct constraint on multiple variables."""
    code = """
from z3 import *
s = Solver()
xs = [Int(f'x{i}') for i in range(3)]
s.add(Distinct(xs))
for x in xs:
    s.add(x >= 1, x <= 3)
if s.check() == sat:
    m = s.model()
    vals = sorted([m[x].as_long() for x in xs])
    print(f"VALS={vals}")
"""
    w = await write_and_run_z3_logic("test_z3_distinct.py", code)
    ok = w["status"] == "success" and "VALS=[1, 2, 3]" in w.get("stdout", "")
    report("Distinct(x0,x1,x2) in [1,3] -> permutation", ok, str(w) if not ok else "")


async def test_crlf_normalization():
    """CRLF line endings should be stripped before writing."""
    code = "from z3 import *\r\nprint('OK')\r\n"
    w = await write_and_run_z3_logic("test_crlf.py", code)
    ok = w["status"] == "success" and "OK" in w.get("stdout", "")
    if ok:
        filepath = Path(z3_logic_module.WORKSPACE) / "test_crlf.py"
        content = filepath.read_text(encoding="utf-8")
        ok = "\r\n" not in content
    report("CRLF normalized to LF on write", ok, str(w) if not ok else "")


# ═════════════════════════════ ERROR STATES ══════════════════════════════

async def test_syntax_error_python():
    """Code has python syntax error -> error."""
    code = """
from z3 import *
print("missing parenthesis
"""
    w = await write_and_run_z3_logic("test_z3_syntax.py", code)
    ok = w["status"] == "error" and ("SyntaxError" in w.get("stderr", "") or "EOL" in w.get("stderr", ""))
    report("Python syntax error -> error state", ok, str(w) if not ok else "")


async def test_import_error():
    """Script importing nonexistent module -> error with stderr."""
    code = """
import nonexistent_module_xyz_123
print("should not reach here")
"""
    w = await write_and_run_z3_logic("test_z3_import.py", code)
    ok = w["status"] == "error" and "ModuleNotFoundError" in w.get("stderr", "")
    report("Import error -> error + ModuleNotFoundError", ok, str(w) if not ok else "")


async def test_runtime_error():
    """Script with runtime error -> error status."""
    code = """
x = 1 / 0
"""
    w = await write_and_run_z3_logic("test_z3_runtime.py", code)
    ok = w["status"] == "error" and "ZeroDivisionError" in w.get("stderr", "")
    report("Runtime ZeroDivisionError -> error + stderr", ok, str(w) if not ok else "")


async def test_nonzero_exitcode_with_stdout():
    """Nonzero exit code should return error status but still include stdout."""
    original_create = z3_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake(*args, **kwargs):
            return FakeProcess(b"partial output here\n", b"some error\n", returncode=1)

        z3_logic_module.asyncio.create_subprocess_exec = _fake
        w = await write_and_run_z3_logic("test_z3_nonzero.py", "print('x')")
        ok = w["status"] == "error" and "partial output" in w.get("stdout", "")
        report("Nonzero exit -> error status + stdout preserved", ok, str(w) if not ok else "")
    finally:
        z3_logic_module.asyncio.create_subprocess_exec = original_create


async def test_stderr_only_on_success():
    """Success with stderr should include stderr in result."""
    original_create = z3_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake(*args, **kwargs):
            return FakeProcess(b"result\n", b"deprecation warning here\n", returncode=0)

        z3_logic_module.asyncio.create_subprocess_exec = _fake
        w = await write_and_run_z3_logic("test_z3_stderr_ok.py", "print('x')")
        ok = w["status"] == "success" and w.get("stderr") is not None
        report("Success + nonempty stderr -> stderr included", ok, str(w) if not ok else "")
    finally:
        z3_logic_module.asyncio.create_subprocess_exec = original_create


async def test_success_empty_stderr_is_none():
    """Success with empty stderr should set stderr to None."""
    original_create = z3_logic_module.asyncio.create_subprocess_exec
    try:
        async def _fake(*args, **kwargs):
            return FakeProcess(b"result\n", b"", returncode=0)

        z3_logic_module.asyncio.create_subprocess_exec = _fake
        w = await write_and_run_z3_logic("test_z3_empty_stderr.py", "print('x')")
        ok = w["status"] == "success" and w.get("stderr") is None
        report("Success + empty stderr -> stderr is None", ok, str(w) if not ok else "")
    finally:
        z3_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ TIMEOUTS ══════════════════════════════════

async def test_timeout_execution():
    """Script enters infinite loop -> timeout kill."""
    code = """
while True:
    pass
"""
    w = await write_and_run_z3_logic("test_z3_timeout.py", code)
    ok = w["status"] == "timeout"
    report("Infinite Python loop -> Subprocess Timeout", ok, str(w) if not ok else "")


async def test_cancellation_propagates():
    """External coroutine cancellation should not be converted into timeout."""

    class CancellingFakeProcess:
        def __init__(self):
            self.returncode = None
            self.killed = False
            self.wait_calls = 0
            self.comm_calls = 0

        async def communicate(self):
            self.comm_calls += 1
            if self.comm_calls == 1:
                raise asyncio.CancelledError()
            return b"", b""

        async def wait(self):
            self.wait_calls += 1
            return self.returncode

        def kill(self):
            self.killed = True
            self.returncode = -9

    fake_process = CancellingFakeProcess()
    original_factory = z3_logic_module.asyncio.create_subprocess_exec
    try:
        async def fake_create_subprocess_exec(*args, **kwargs):
            return fake_process

        z3_logic_module.asyncio.create_subprocess_exec = fake_create_subprocess_exec

        try:
            await write_and_run_z3_logic("test_z3_cancel.py", "print('ok')")
            report("Coroutine cancellation propagates", False, "Expected CancelledError to be re-raised")
        except asyncio.CancelledError:
            ok = fake_process.killed
            report("Coroutine cancellation propagates", ok, "Process cleanup did not complete" if not ok else "")
    finally:
        z3_logic_module.asyncio.create_subprocess_exec = original_factory


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


async def test_terminate_graceful_windows_signal():
    """Windows cleanup should try CTRL_BREAK_EVENT before a hard kill."""

    class GracefulProcess:
        def __init__(self):
            self.returncode = None
            self.signal_sent = None
            self.killed = False
            self.wait_calls = 0

        async def wait(self):
            self.wait_calls += 1
            self.returncode = 0
            return 0

        def send_signal(self, sig):
            self.signal_sent = sig

        def kill(self):
            self.killed = True
            self.returncode = -9

    proc = GracefulProcess()
    await _terminate_process(proc)
    ok = proc.signal_sent == signal.CTRL_BREAK_EVENT and not proc.killed and proc.wait_calls == 1
    report("Cleanup prefers CTRL_BREAK_EVENT on Windows", ok, str(vars(proc)) if not ok else "")


async def test_terminate_falls_back_to_kill():
    """Cleanup should fall back to kill when graceful termination times out."""

    class HangingProcess:
        def __init__(self):
            self.returncode = None
            self.signal_sent = None
            self.killed = False
            self.wait_calls = 0

        async def wait(self):
            self.wait_calls += 1
            if self.wait_calls == 1:
                await asyncio.sleep(5)  # Simulate hang
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
    report("Cleanup falls back to kill after grace period", ok, str(vars(proc)) if not ok else "")


# ═════════════════════════════ PLATFORM GUARD ════════════════════════════

async def test_platform_guard_creationflags():
    """Verify that creationflags is only set on Windows (sys.platform check present)."""
    import inspect
    source = inspect.getsource(write_and_run_z3_logic)
    ok = 'sys.platform' in source and 'creationflags' in source
    report("Platform guard: sys.platform check exists for creationflags", ok,
           "Missing sys.platform guard in z3_logic.py" if not ok else "")

async def test_z3_command_linux_apple():
    """Verify that creationflags is NOT set on Linux/Apple."""
    original_platform = sys.platform
    original_create = z3_logic_module.asyncio.create_subprocess_exec
    
    captured_kwargs = None
    async def _fake(*args, **kwargs):
        nonlocal captured_kwargs
        captured_kwargs = kwargs
        return FakeProcess(b"SAT\n", b"", returncode=0)
        
    try:
        sys.platform = "linux"
        z3_logic_module.asyncio.create_subprocess_exec = _fake
        
        await write_and_run_z3_logic("test_linux.py", "print('SAT')")
        
        ok = captured_kwargs is not None and "creationflags" not in captured_kwargs
        report("Z3 invoked without creationflags on Linux/Apple", ok, f"Kwargs: {captured_kwargs}")
    finally:
        sys.platform = original_platform
        z3_logic_module.asyncio.create_subprocess_exec = original_create


# ═════════════════════════════ ADDITIONAL EDGE CASES ═════════════════════

async def test_general_exception():
    """General exception in write_and_run_z3_logic should return error status."""
    original_write = Path.write_text
    try:
        def _fail_write(self, *args, **kwargs):
            raise OSError("Disk full")
        Path.write_text = _fail_write
        w = await write_and_run_z3_logic("test_gen_exc.py", "print('x')")
        ok = w["status"] == "error" and "Disk full" in w.get("error", "")
        report("General exception in write_and_run_z3 -> error status", ok, str(w) if not ok else "")
    finally:
        Path.write_text = original_write


async def test_timeout_reports_seconds():
    """Timeout error message should contain the configured timeout value."""
    original_timeout = z3_logic_module.QUERY_TIMEOUT
    original_wait_for = z3_logic_module.asyncio.wait_for
    try:
        z3_logic_module.QUERY_TIMEOUT = 30

        async def _always_timeout(awaitable, timeout=None):
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.TimeoutError()

        z3_logic_module.asyncio.wait_for = _always_timeout
        w = await write_and_run_z3_logic("test_timeout_30.py", "import time; time.sleep(999)")
        ok = w["status"] == "timeout" and "30s" in w.get("error", "")
        report("Timeout reports 30s", ok, str(w) if not ok else "")
    finally:
        z3_logic_module.asyncio.wait_for = original_wait_for
        z3_logic_module.QUERY_TIMEOUT = original_timeout


async def test_success_with_output():
    """Success with stdout should include stdout in result."""
    code = """
print("Hello Z3")
print("Result: OK")
"""
    w = await write_and_run_z3_logic("test_output.py", code)
    ok = w["status"] == "success" and "Hello Z3" in w.get("stdout", "") and "Result: OK" in w.get("stdout", "")
    report("Success with output -> stdout preserved", ok)


async def test_empty_script():
    """Empty Python script should succeed."""
    w = await write_and_run_z3_logic("test_empty.py", "")
    ok = w["status"] == "success"
    report("Empty script -> success", ok, str(w) if not ok else "")


# ═════════════════════════════ MAIN ══════════════════════════════════════

async def main():
    print(f"\n{BOLD}=== Z3 MCP Server - Comprehensive Edge Case Tests ==={RESET}\n")

    tests = [
        ("Filename Sanitization", [
            test_sanitize_strips_path_traversal,
            test_sanitize_adds_extension,
            test_sanitize_preserves_extension,
            test_sanitize_special_chars,
            test_sanitize_double_extension,
        ]),
        ("Write & Run Success", [
            test_valid_write_and_run,
            test_z3_unsat,
            test_z3_optimization,
            test_z3_theorem_proving,
            test_z3_distinct,
            test_crlf_normalization,
        ]),
        ("Error States", [
            test_syntax_error_python,
            test_import_error,
            test_runtime_error,
            test_nonzero_exitcode_with_stdout,
            test_stderr_only_on_success,
            test_success_empty_stderr_is_none,
        ]),
        ("Timeouts & Cancellation", [
            test_timeout_execution,
            test_cancellation_propagates,
        ]),
        ("Process Termination", [
            test_terminate_already_exited,
            test_terminate_graceful_windows_signal,
            test_terminate_falls_back_to_kill,
        ]),
        ("Platform Guard", [
            test_platform_guard_creationflags,
            test_z3_command_linux_apple,
        ]),
        ("Additional Edge Cases", [
            test_general_exception,
            test_timeout_reports_seconds,
            test_success_with_output,
            test_empty_script,
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