from typing import Dict, Any
from z3_mcp_server import mcp
from z3_mcp_server.z3_logic import write_and_run_z3_logic

@mcp.tool()
async def write_and_run_z3(filename: str, code: str) -> Dict[str, Any]:
    """
    Write Python code using Z3 to a file and run it immediately to get results.
    We capture printed stdout and stderr from running the script.
    """
    return await write_and_run_z3_logic(filename, code)
