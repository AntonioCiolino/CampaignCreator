#!/usr/bin/env python3
"""
Entry point for the Campaign Crafter MCP server.
"""
import sys
from src.server import run_server
from src.utils.config import logger

if __name__ == "__main__":
    try:
        logger.info("Starting Campaign Crafter MCP server")
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)