import asyncio
import signal
from pathlib import Path


async def _terminate_process(process: asyncio.subprocess.Process) -> None:
    """Terminate spawned process (and process group on Windows when possible)."""
    if process.returncode is not None:
        return

    try:
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
            await asyncio.wait_for(process.wait(), timeout=1)
        except (AttributeError, ProcessLookupError, PermissionError, ValueError, asyncio.TimeoutError):
            pass

        if process.returncode is None:
            process.kill()
            await process.wait()
    except Exception:
        pass

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    safe_name = Path(filename).name
    import re
    safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
    if not safe_name or safe_name == ".lp":
        safe_name = "solver"
    if not safe_name.endswith('.lp'):
        safe_name += '.lp'
    return safe_name
