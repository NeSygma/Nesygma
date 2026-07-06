from typing import Dict, Any
from vampire_mcp_server import mcp
from vampire_mcp_server.vampire_logic import write_and_run_vampire_logic

@mcp.tool()
async def write_and_run_vampire(
    pos_filename: str, 
    pos_code: str, 
    neg_filename: str, 
    neg_code: str
) -> Dict[str, Any]:
    """
    Write two TPTP problem files (positive claim and negation) and run Vampire 
    on both concurrently to get proof results for both in one iteration.
    Returns a dictionary with 'positive' and 'negative' result objects.
    """
    return await write_and_run_vampire_logic(pos_filename, pos_code, neg_filename, neg_code)

