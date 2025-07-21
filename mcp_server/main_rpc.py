import os
import httpx
from fastmcp import FastMCP, Context
from pydantic import BaseModel

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

mcp = FastMCP("Campaign Crafter")

class User(BaseModel):
    username: str

class State(BaseModel):
    user: User
    token: str

@mcp.tool
async def list_campaigns(ctx: Context) -> list:
    """
    Lists all campaigns for the authenticated user.
    """
    token = ctx.session.get("token")
    if not token:
        raise Exception("Unauthorized")
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
        raise Exception("Unauthorized")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/campaigns",
            headers=headers,
            json=campaign.model_dump(),
        )
        response.raise_for_status()
        return response.json()

@mcp.tool
async def login(token: str, ctx: Context) -> str:
    """
    Logs in a user and stores the token in the session.
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/users/me", headers=headers)
        if response.status_code == 200:
            ctx.session["token"] = token
            return "Login successful."
        else:
            raise Exception("Invalid token")


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=4000)
