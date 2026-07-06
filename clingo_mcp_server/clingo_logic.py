import asyncio
import json
import subprocess
import sys
from typing import Dict, Any
import clingo

from clingo_mcp_server import WORKSPACE, QUERY_TIMEOUT, logger
from clingo_mcp_server.helpers import sanitize_filename, _terminate_process

MAX_MODELS = 10
CLINGO_WARNING_KEYWORDS = ["warning", "error", "undefined", "unsafe", "atom does not occur"]

async def write_clingo_file_logic(filename: str, code: str) -> Dict[str, Any]:
    """Write ASP code to a file and run bounded syntax/grounding validation."""
    logger.info(f"Writing Clingo file: {filename}")
    
    safe_name = sanitize_filename(filename)
    filepath = WORKSPACE / safe_name
    
    try:
        code = code.replace('\r\n', '\n').strip()
        filepath.write_text(code, encoding='utf-8')
        
        # Bounded validation: catches syntax/safety errors while preventing the
        # write step from blocking indefinitely on very hard groundings.
        def _check_syntax():
            warnings = []
            def _logger(code_msg: clingo.MessageCode, message: str):
                warnings.append(message)
                
            ctrl = clingo.Control(["0"], logger=_logger)
            try:
                ctrl.add("base", [], code)
                ctrl.ground([("base", [])])
                warning_str = "\n".join(warnings) if warnings else None
                return {"status": "success", "warnings": warning_str}
            except Exception as e:
                error_msg = str(e)
                if warnings:
                    error_msg = "\n".join(warnings) + "\n" + error_msg
                return {"status": "error", "error": error_msg}
                
        loop = asyncio.get_running_loop()
        syntax_timeout = max(1, min(QUERY_TIMEOUT, 15)) # Cap syntax check timeout to prevent long waits on large groundings, but allow some time for complex syntax.
        try:
            syntax_result = await asyncio.wait_for(
                loop.run_in_executor(None, _check_syntax),
                timeout=syntax_timeout,
            )
        except asyncio.TimeoutError:
            syntax_result = {
                "status": "grounding_timeout",
                "warnings": (
                    "CRITICAL ERROR: Grounding timed out (>15s). "
                    "Your ASP program is too large and was stopped to prevent a laptop RAM crash. "
                    "Solution: Tighten your domains (e.g., use node(X) instead of just X), "
                    "check for 'unsafe' variables, or reduce the 'horizon' steps."
                ),
            }
        
        if syntax_result["status"] == "success":
            res = {
                "status": "success",
                "message": f"Wrote and validated {safe_name}",
                "path": str(filepath),
                "lines": len(code.splitlines())
            }
            if syntax_result.get("warnings"):
                res["warnings"] = syntax_result["warnings"]
            return res
        elif syntax_result["status"] == "grounding_timeout":
            return {
                "status": "grounding_timeout",
                "error": syntax_result["warnings"],
                "hint": (
                    "Clingo was stopped because the grounding was too large. "
                    "Optimize your ASP code: Use domain predicates (like 'node(X)'), check for unsafe variables, "
                    "or reduce your time horizon."
                )
            }
        else:
            return {
                "status": "syntax_error",
                "error": syntax_result["error"],
                "hint": "Fix the ASP syntax. Common issues: missing periods, undefined atoms, variable capitalization."
            }
            
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return {"status": "error", "error": str(e)}

async def run_clingo_logic(filename: str) -> Dict[str, Any]:
    """Execute a Clingo file using clingo CLI and return answer sets."""
    logger.info(f"Running Clingo via subprocess: {filename}")
    
    safe_name = sanitize_filename(filename)
    filepath = WORKSPACE / safe_name
    
    if not filepath.exists():
        return {
            "status": "error",
            "error": f"File not found: {safe_name}. Write it first using write_clingo_file."
        }
    
    try:
        kwargs = {
            "stdin": asyncio.subprocess.DEVNULL,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "cwd": str(WORKSPACE),
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        cmd = ["clingo", safe_name, str(MAX_MODELS), "--outf=2", f"--time-limit={QUERY_TIMEOUT}"]
        process = await asyncio.create_subprocess_exec(*cmd, **kwargs)

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=QUERY_TIMEOUT + 5)
        except asyncio.TimeoutError:
            await _terminate_process(process)
            return {"status": "timeout", "error": f"Clingo exceeded {QUERY_TIMEOUT}s"}
        except asyncio.CancelledError:
            await _terminate_process(process)
            raise

        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()

        models = []
        status = "unknown"
        warning_truncated = False

        try:
            parsed = json.loads(stdout_text) if stdout_text.strip() else {}
            result_text = str(parsed.get("Result", "")).upper()
            if "UNSATISFIABLE" in result_text:
                status = "unsatisfiable"
            elif "SATISFIABLE" in result_text:
                status = "satisfiable"
            elif "OPTIMUM FOUND" in result_text:
                # Optimization runs can report OPTIMUM FOUND instead of SATISFIABLE.
                status = "optimum_found"
            elif "UNKNOWN" in result_text:
                status = "unknown"

            for call in parsed.get("Call", []):
                for witness in call.get("Witnesses", []):
                    symbols = []
                    for sym in witness.get("Value", []):
                        sym_str = str(sym)
                        if len(sym_str) > 200:
                            sym_str = sym_str[:197] + "..."
                        symbols.append(sym_str)
                    models.append(symbols)

            # If witnesses exist but Result text is non-standard, treat as satisfiable.
            if status == "unknown" and models:
                status = "satisfiable"

            more_models = parsed.get("Models", {}).get("More")
            # Trust Clingo's explicit truncation signal first.
            warning_truncated = more_models in ("yes", "1", 1, True)
            if not warning_truncated and more_models is None:
                warning_truncated = len(models) >= MAX_MODELS
        except json.JSONDecodeError:
            if process.returncode != 0:
                return {
                    "status": "error",
                    "error": stderr_text or f"clingo exited with code {process.returncode}",
                    "command": " ".join(cmd),
                }

        result = {
            "status": status,
            "command": " ".join(cmd),
            "models": models,
        }
        if warning_truncated:
            result["warning_truncated"] = f"Note: Output was truncated to {MAX_MODELS} models to fit context limits. If you need a specific Answer Set, use constraints."
        if stderr_text:
            stderr_lower = stderr_text.lower()
            if any(keyword in stderr_lower for keyword in CLINGO_WARNING_KEYWORDS):
                result["warnings"] = stderr_text

        logger.info(f"Clingo result [{safe_name}]: status={result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {"status": "error", "error": str(e)}
