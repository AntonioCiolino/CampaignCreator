"""
Configuration utilities for the Campaign Crafter MCP server.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Load environment variables from .env file in the mcp_server directory
# This ensures the .env is found regardless of the current working directory
_mcp_server_dir = Path(__file__).parent.parent.parent
_env_path = _mcp_server_dir / ".env"
load_dotenv(_env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("campaign_crafter_mcp")


def get_config() -> Dict[str, Any]:
    """
    Get the configuration for the MCP server.
    
    Returns:
        Dictionary containing the configuration
    """
    return {
        "api_base_url": os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
        "mcp_server_host": os.getenv("MCP_SERVER_HOST", "127.0.0.1"),
        "mcp_server_port": int(os.getenv("MCP_SERVER_PORT", 4000)),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }