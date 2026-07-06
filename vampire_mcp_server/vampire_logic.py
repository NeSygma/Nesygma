import asyncio
import subprocess
import sys
from typing import Dict, Any
from vampire_mcp_server import WORKSPACE, QUERY_TIMEOUT, logger
from vampire_mcp_server.helpers import _terminate_process, sanitize_filename

async def _run_vampire_single(filename: str, code: str) -> Dict[str, Any]:
    """Internal helper to write and run a single Vampire TPTP file."""
    logger.info(f"Writing Vampire TPTP file: {filename}")
    
    safe_name = sanitize_filename(filename)
    filepath = WORKSPACE / safe_name
    
    try:
        # Standardize newlines before writing
        code = code.replace('\r\n', '\n').strip()
        filepath.write_text(code, encoding='utf-8')
        
        kwargs = {
            "stdin": asyncio.subprocess.DEVNULL,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "cwd": str(WORKSPACE)
        }
        
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            cmd = ["wsl", "vampire", "-t", str(QUERY_TIMEOUT), safe_name]
        else:
            cmd = ["vampire", "-t", str(QUERY_TIMEOUT), safe_name]
            
        logger.info(f"Executing: {' '.join(cmd)}")
            
        process = await asyncio.create_subprocess_exec(
            *cmd, **kwargs
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=QUERY_TIMEOUT + 5
            )
            stdout_text = stdout_bytes.decode('utf-8', errors='replace')
            stderr_text = stderr_bytes.decode('utf-8', errors='replace')
            
            filtered_lines = []
            for line in stdout_text.splitlines():
                if line.startswith(("% Version:", "% Linked with", "% CaDiCaL version:",
                                   "% Time elapsed:", "% Peak memory usage:",
                                   "% ------------------------------",
                                   "% Running in auto input_syntax")):
                    continue
                filtered_lines.append(line)
            stdout_text = "\n".join(filtered_lines).strip()

            def get_szs_status(txt: str) -> str:
                for line in txt.splitlines():
                    if line.startswith("% SZS status"):
                        return line.split("SZS status", 1)[1].strip().split()[0]
                return "Unknown"

            szs = get_szs_status(stdout_text)

            SUCCESSFUL_SZS = {"Theorem", "Unsatisfiable", "Satisfiable",
                              "CounterSatisfiable", "ContradictoryAxioms"}

            if szs in SUCCESSFUL_SZS or process.returncode == 0:
                logger.info(f"Vampire success ({szs}): {safe_name}")
                return {
                    "status": "success",
                    "szs_status": szs,
                    "stdout": stdout_text,
                    "stderr": stderr_text if stderr_text else None,
                    "returncode": process.returncode
                }
            else:
                logger.warning(f"Vampire failed ({szs}, code {process.returncode}): {safe_name}")
                return {
                    "status": "error",
                    "szs_status": szs,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "returncode": process.returncode
                }
                
        except asyncio.TimeoutError:
            await _terminate_process(process)
            return {"status": "timeout", "error": f"Vampire execution exceeded {QUERY_TIMEOUT}s"}
        except asyncio.CancelledError:
            await _terminate_process(process)
            raise
            
    except Exception as e:
        logger.exception(f"Error executing Vampire file {filename}: {e}")
        return {
            "status": "error", "error": str(e)
        }

async def write_and_run_vampire_logic(
    pos_filename: str, 
    pos_code: str, 
    neg_filename: str, 
    neg_code: str
) -> Dict[str, Any]:
    """Execute both positive and negative Vampire TPTP files concurrently."""
    results = await asyncio.gather(
        _run_vampire_single(pos_filename, pos_code),
        _run_vampire_single(neg_filename, neg_code)
    )
    return {
        "positive": results[0],
        "negative": results[1]
    }

