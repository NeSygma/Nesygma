import os
import logging
from pathlib import Path
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

WORKSPACE = Path(os.environ.get("Z3_WORKSPACE", "./z3_workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
QUERY_TIMEOUT = int(os.environ.get("Z3_TIMEOUT", "60"))

mcp = FastMCP("z3")
