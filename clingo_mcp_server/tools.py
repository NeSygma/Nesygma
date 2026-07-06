from typing import Dict, Any

from clingo_mcp_server import mcp
from clingo_mcp_server.clingo_logic import write_clingo_file_logic, run_clingo_logic

@mcp.tool()
async def write_and_run_clingo(filename: str, code: str) -> Dict[str, Any]:
    """
    Write ASP code to a file for Clingo, validate syntax, and immediately run it to get answer sets.
    """
    # Step 1: Write and check syntax
    write_result = await write_clingo_file_logic(filename, code)
    if write_result.get("status") != "success":
        return write_result
        
    # Step 2: Run Clingo
    run_result = await run_clingo_logic(filename)
    return run_result


