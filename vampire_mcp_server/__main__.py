import os
import logging
from vampire_mcp_server import mcp, WORKSPACE, logger
from vampire_mcp_server import tools

def main():
    log_file = os.environ.get("VAMPIRE_LOG_FILE", "vampire_server_execution.log")
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - VAMPIRE_SERVER - %(message)s'))
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    logger.info(f"Starting Vampire MCP Server (workspace: {WORKSPACE})")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
