import os
import httpx
from fastmcp import FastMCP, Context
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", 4000))

mcp = FastMCP("Campaign Crafter")

@mcp.tool
async def login(token: str, ctx: Context) -> str:
    """
    Logs in a user and returns the token.
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/users/me", headers=headers)
        if response.status_code == 200:
            return token
        else:
            raise Exception("Invalid token")

@mcp.tool
async def list_tools(ctx: Context) -> list[str]:
    """
    Lists the available tools.
    """
    return [tool.name for tool in mcp.tools]

@mcp.tool
async def list_campaigns(ctx: Context) -> list:
    """
    Lists all campaigns for the authenticated user.
    """
    token = ctx.session.get("token")
    if not token:
        raise Exception("Unauthorized. Please login first.")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/campaigns", headers=headers)
        response.raise_for_status()
        return response.json()

class Campaign(BaseModel):
    title: str
    concept: str

@mcp.tool
async def create_campaign(campaign: Campaign, ctx: Context) -> dict:
    """
    Creates a new campaign.
    """
    token = ctx.session.get("token")
    if not token:
        raise Exception("Unauthorized. Please login first.")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/campaigns",
            headers=headers,
            json=campaign.model_dump(),
        )
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    mcp.run(transport="http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
