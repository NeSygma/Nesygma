import os
import logging

from clingo_mcp_server import mcp, WORKSPACE, logger
from clingo_mcp_server import tools


def main():
    log_file = os.environ.get("CLINGO_LOG_FILE", "clingo_server_execution.log")
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - CLINGO_SERVER - %(message)s'))
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    logger.info(f"Starting Clingo MCP Server (workspace: {WORKSPACE})")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
