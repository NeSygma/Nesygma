import asyncio
import subprocess
import sys
from typing import Dict, Any
from z3_mcp_server import WORKSPACE, QUERY_TIMEOUT, logger
from z3_mcp_server.helpers import _terminate_process, sanitize_filename

async def write_and_run_z3_logic(filename: str, code: str) -> Dict[str, Any]:
    """Write Z3 python code to a file and execute it."""
    logger.info(f"Writing Z3 Python file: {filename}")
    
    safe_name = sanitize_filename(filename)
    filepath = WORKSPACE / safe_name
    
    try:
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
            
        # Run python script
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(filepath),
            **kwargs
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=QUERY_TIMEOUT + 5
            )
            stdout_text = stdout_bytes.decode('utf-8', errors='replace')
            stderr_text = stderr_bytes.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                logger.info(f"Z3 script completed successfully: {safe_name}")
                return {
                    "status": "success",
                    "stdout": stdout_text,
                    "stderr": stderr_text if stderr_text else None
                }
            else:
                logger.warning(f"Z3 script failed: {safe_name}")
                return {
                    "status": "error",
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "hint": "The script crashed or failed. Check the stderr."
                }
                
        except asyncio.TimeoutError:
            await _terminate_process(process)
            return {"status": "timeout", "error": f"Z3 execution exceeded {QUERY_TIMEOUT}s"}
        except asyncio.CancelledError:
            await _terminate_process(process)
            raise
            
    except Exception as e:
        logger.exception(f"Error executing Z3 file: {e}")
        return {"status": "error", "error": str(e)}
