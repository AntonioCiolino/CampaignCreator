import os
import httpx
from fastmcp import FastMCP, Context
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", 4000))

mcp = FastMCP("Campaign Crafter")

# --- Pydantic Models ---
class Campaign(BaseModel):
    title: str
    concept: str

class Character(BaseModel):
    name: str
    concept: str
    campaign_id: Optional[int] = None

class CampaignSection(BaseModel):
    title: str
    content: str
    campaign_id: int

class LinkCharacter(BaseModel):
    campaign_id: int
    character_id: int

class GenerateToc(BaseModel):
    campaign_id: int

class GenerateTitles(BaseModel):
    campaign_id: int
    section_id: int

# --- Helper Function ---
async def forward_request(method: str, path: str, token: str, json: Optional[dict] = None) -> dict:
    """Forwards a request to the main Campaign Crafter API."""
    if not token:
        raise Exception("Unauthorized. Please login first.")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.request(method, f"{API_BASE_URL}/api/v1{path}/", headers=headers, json=json)
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()

# --- MCP Tools ---
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
async def create_campaign(campaign: Campaign, token: str, ctx: Context) -> dict:
    """Creates a new campaign."""
    return await forward_request("POST", "/campaigns", token, campaign.model_dump())

@mcp.tool
async def get_campaign(campaign_id: int, token: str, ctx: Context) -> dict:
    """Retrieves a specific campaign."""
    return await forward_request("GET", f"/campaigns/{campaign_id}", token)

@mcp.tool
async def list_campaigns(token: str, ctx: Context) -> list:
    """Lists all campaigns for the authenticated user."""
    return await forward_request("GET", "/campaigns", token)

@mcp.tool
async def update_campaign(campaign_id: int, campaign: Campaign, token: str, ctx: Context) -> dict:
    """Updates a specific campaign."""
    return await forward_request("PUT", f"/campaigns/{campaign_id}", token, campaign.model_dump())

@mcp.tool
async def delete_campaign(campaign_id: int, token: str, ctx: Context) -> dict:
    """Deletes a specific campaign."""
    return await forward_request("DELETE", f"/campaigns/{campaign_id}", token)

@mcp.tool
async def create_character(character: Character, token: str, ctx: Context) -> dict:
    """Creates a new character."""
    return await forward_request("POST", "/characters", token, character.model_dump())

@mcp.tool
async def get_character(character_id: int, token: str, ctx: Context) -> dict:
    """Retrieves a specific character."""
    return await forward_request("GET", f"/characters/{character_id}", token)

@mcp.tool
async def update_character(character_id: int, character: Character, token: str, ctx: Context) -> dict:
    """Updates a specific character."""
    return await forward_request("PUT", f"/characters/{character_id}", token, character.model_dump())

@mcp.tool
async def delete_character(character_id: int, token: str, ctx: Context) -> dict:
    """Deletes a specific character."""
    return await forward_request("DELETE", f"/characters/{character_id}", token)

@mcp.tool
async def list_characters(token: str, ctx: Context) -> list:
    """Lists all characters for the authenticated user."""
    return await forward_request("GET", "/characters", token)

@mcp.tool
async def link_character_to_campaign(link: LinkCharacter, token: str, ctx: Context) -> dict:
    """Links a character to a campaign."""
    return await forward_request("POST", "/characters/link", token, link.model_dump())

@mcp.tool
async def unlink_character_from_campaign(link: LinkCharacter, token: str, ctx: Context) -> dict:
    """Unlinks a character from a campaign."""
    return await forward_request("POST", "/characters/unlink", token, link.model_dump())

@mcp.tool
async def create_campaign_section(section: CampaignSection, token: str, ctx: Context) -> dict:
    """Creates a new campaign section."""
    return await forward_request("POST", "/campaign-sections", token, section.model_dump())

@mcp.tool
async def list_campaign_sections(campaign_id: int, token: str, ctx: Context) -> list:
    """Lists all sections for a specific campaign."""
    return await forward_request("GET", f"/campaign-sections/campaign/{campaign_id}", token)

@mcp.tool
async def update_campaign_section(section_id: int, section: CampaignSection, token: str, ctx: Context) -> dict:
    """Updates a specific campaign section."""
    return await forward_request("PUT", f"/campaign-sections/{section_id}", token, section.model_dump())

@mcp.tool
async def delete_campaign_section(section_id: int, token: str, ctx: Context) -> dict:
    """Deletes a specific campaign section."""
    return await forward_request("DELETE", f"/campaign-sections/{section_id}", token)

@mcp.tool
async def generate_toc(toc_request: GenerateToc, token: str, ctx: Context) -> dict:
    """Generates a table of contents for a campaign."""
    return await forward_request("POST", "/campaigns/generate-toc", token, toc_request.model_dump())

@mcp.tool
async def generate_titles(title_request: GenerateTitles, token: str, ctx: Context) -> dict:
    """Generates titles for a campaign section."""
    return await forward_request("POST", "/campaigns/generate-titles", token, title_request.model_dump())

if __name__ == "__main__":
    mcp.run(transport="http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
