"""
Main server module for the Campaign Crafter MCP server.
"""
import sys
import os
import httpx
from fastmcp import FastMCP, Context
from .models.schemas import (
    Campaign, Character, CampaignSection, LinkCharacter, GenerateToc, GenerateTitles, SeedSections
)
from .utils.config import get_config, logger
from typing import Optional, Dict, Any, List

# Load configuration
config = get_config()
API_BASE_URL = config["api_base_url"]
MCP_SERVER_HOST = config["mcp_server_host"]
MCP_SERVER_PORT = config["mcp_server_port"]

# Create MCP server
mcp = FastMCP("Campaign Crafter")

# Add this global variable to store the token
_auth_token = None


async def auto_authenticate():
    """Automatically authenticate using environment credentials."""
    global _auth_token
    username = os.getenv("CAMPAIGN_CRAFTER_USERNAME")
    password = os.getenv("CAMPAIGN_CRAFTER_PASSWORD")

    if not username or not password:
        logger.warning("No credentials found in environment variables")
        return None

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/auth/token",
                data={"username": username, "password": password},
            )
            response.raise_for_status()
            _auth_token = response.json()["access_token"]
            logger.info(f"Auto-authentication successful; : token is \n{_auth_token}\n")
            return _auth_token
    except Exception as e:
        logger.error(f"Auto-authentication failed: {e}")
        return None


# --- Helper Function ---
async def forward_request(
    method: str, path: str, token: str, json: Optional[dict] = None, timeout: float = 120.0
) -> Dict[str, Any]:
    """
    Forwards a request to the main Campaign Crafter API.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path (e.g., "/campaigns/")
        token: Authentication token
        json: Request body as a dictionary
        timeout: Request timeout in seconds (default 120s for LLM operations)
        
    Returns:
        Response from the API as a dictionary
        
    Raises:
        Exception: If the request fails or the user is not authenticated
    """
    auth_token = token or _auth_token
    if not auth_token:
        raise Exception("Unauthorized. Please login or set credentials.")
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        url = f"{API_BASE_URL}/api/v1{path}"
        logger.debug(f"Forwarding {method} request to {url}")
        response = await client.request(method, url, headers=headers, json=json)
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()


# --- MCP Tools ---

@mcp.tool
async def refresh_auth(ctx: Context) -> Dict[str, Any]:
    """
    Force re-authentication using environment credentials.
    Call this if you get 'Unauthorized' errors to refresh the auth token.
    
    Returns:
        Dictionary with success status and message
    """
    token = await auto_authenticate()
    if token:
        return {
            "success": True,
            "message": "Authentication refreshed successfully",
            "authenticated": True
        }
    else:
        return {
            "success": False,
            "error": "Authentication failed - check credentials in environment variables"
        }


@mcp.tool
async def get_auth_status(ctx: Context) -> Dict[str, Any]:
    """
    Check if the server has a valid auth token.
    
    Returns:
        Dictionary with authentication status
    """
    return {
        "authenticated": _auth_token is not None,
        "has_env_credentials": bool(os.getenv("CAMPAIGN_CRAFTER_USERNAME") and os.getenv("CAMPAIGN_CRAFTER_PASSWORD")),
        "api_base_url": API_BASE_URL
    }


@mcp.tool
async def get_user_info(token: str, ctx: Context) -> str:
    """
    Retrieves information about the logged-in user.
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/users/me", headers=headers)
        if response.status_code == 200:
            logger.info("User successfully authenticated")
            return token
        else:
            logger.warning("Authentication failed")
            raise Exception("Invalid token")


@mcp.tool
async def create_campaign(campaign: Campaign, token: str, ctx: Context) -> Dict[str, Any]:
    """
    Creates a new campaign. 
    Pass initial_user_prompt to have the API generate a concept via LLM during creation.
    The concept field is ignored on create - use initial_user_prompt instead.
    """
    logger.info(f"Creating campaign: {campaign.title}")
    # Build payload with fields the API accepts for creation
    payload = {"title": campaign.title}
    if campaign.initial_user_prompt:
        payload["initial_user_prompt"] = campaign.initial_user_prompt
    result = await forward_request("POST", "/campaigns/", token, payload)
    logger.info(f"Create campaign result: {result}")
    return result


@mcp.tool
async def get_campaign(campaign_id: int, token: str, ctx: Context) -> Dict[str, Any]:
    """Retrieves a specific campaign."""
    logger.info(f"Getting campaign: {campaign_id}")
    return await forward_request("GET", f"/campaigns/{campaign_id}/", token)


@mcp.tool
async def list_campaigns(token: str, ctx: Context) -> List[Dict[str, Any]]:
    """Lists all campaigns for the authenticated user."""
    logger.info("Listing campaigns")
    return await forward_request("GET", "/campaigns/", token)


@mcp.tool
async def update_campaign(
    campaign_id: int, campaign: Campaign, token: str, ctx: Context
) -> Dict[str, Any]:
    """Updates a specific campaign."""
    logger.info(f"Updating campaign: {campaign_id}")
    return await forward_request(
        "PUT", f"/campaigns/{campaign_id}/", token, campaign.model_dump()
    )


@mcp.tool
async def delete_campaign(campaign_id: int, token: str, ctx: Context) -> Dict[str, Any]:
    """Deletes a specific campaign."""
    logger.info(f"Deleting campaign: {campaign_id}")
    return await forward_request("DELETE", f"/campaigns/{campaign_id}/", token)


@mcp.tool
async def create_character(character: Character, token: str, ctx: Context) -> Dict[str, Any]:
    """Creates a new character."""
    logger.info(f"Creating character: {character.name}")
    return await forward_request("POST", "/characters/", token, character.model_dump())


@mcp.tool
async def get_character(character_id: int, token: str, ctx: Context) -> Dict[str, Any]:
    """Retrieves a specific character."""
    logger.info(f"Getting character: {character_id}")
    return await forward_request("GET", f"/characters/{character_id}/", token)


@mcp.tool
async def list_characters(token: str, ctx: Context) -> List[Dict[str, Any]]:
    """Lists all characters for the authenticated user."""
    logger.info("Listing characters")
    return await forward_request("GET", "/characters/", token)


@mcp.tool
async def get_all_characters(token: str, ctx: Context) -> List[Dict[str, Any]]:
    """Lists all characters, regardless of campaign."""
    logger.info("Getting all characters")
    return await forward_request("GET", "/characters/all/", token)


@mcp.tool
async def update_character(
    character_id: int, character: Character, token: str, ctx: Context
) -> Dict[str, Any]:
    """Updates a specific character."""
    logger.info(f"Updating character: {character_id}")
    return await forward_request(
        "PUT", f"/characters/{character_id}/", token, character.model_dump()
    )


@mcp.tool
async def delete_character(character_id: int, token: str, ctx: Context) -> Dict[str, Any]:
    """Deletes a specific character."""
    logger.info(f"Deleting character: {character_id}")
    return await forward_request("DELETE", f"/characters/{character_id}/", token)


@mcp.tool
async def link_character_to_campaign(
    link: LinkCharacter, token: str, ctx: Context
) -> Dict[str, Any]:
    """Links a character to a campaign."""
    character_id = link.character_id
    campaign_id = link.campaign_id
    logger.info(f"Linking character {character_id} to campaign {campaign_id}")
    return await forward_request("POST", f"/characters/{character_id}/campaigns/{campaign_id}", token)


@mcp.tool
async def unlink_character_from_campaign(
    link: LinkCharacter, token: str, ctx: Context
) -> Dict[str, Any]:
    """Unlinks a character from a campaign."""
    character_id = link.character_id
    campaign_id = link.campaign_id
    logger.info(f"Unlinking character {character_id} from campaign {campaign_id}")
    return await forward_request(
        "DELETE", f"/characters/{character_id}/campaigns/{campaign_id}", token
    )


@mcp.tool
async def create_campaign_section(
    section: CampaignSection, token: str, ctx: Context
) -> Dict[str, Any]:
    """Creates a new campaign section."""
    # Exclude campaign_id from the payload since it's in the URL
    section_data = section.model_dump(exclude={"campaign_id"})
    logger.info(f"Creating section for campaign {section.campaign_id}")
    return await forward_request(
        "POST", f"/campaigns/{section.campaign_id}/sections/", token, section_data
    )


@mcp.tool
async def list_campaign_sections(campaign_id: int, token: str, ctx: Context) -> List[Dict[str, Any]]:
    """Lists all sections for a specific campaign."""
    logger.info(f"Listing sections for campaign {campaign_id}")
    response = await forward_request("GET", f"/campaigns/{campaign_id}/sections/", token)
    # Extract the sections array from the response
    if isinstance(response, dict) and "sections" in response:
        return response["sections"]
    return response


@mcp.tool
async def get_campaign_section(
    campaign_id: int, section_id: int, token: str, ctx: Context
) -> Dict[str, Any]:
    """Retrieves a specific campaign section."""
    logger.info(f"Getting section {section_id} for campaign {campaign_id}")
    return await forward_request(
        "GET", f"/campaigns/{campaign_id}/sections/{section_id}/", token
    )


@mcp.tool
async def update_campaign_section(
    section_id: int, section: CampaignSection, token: str, ctx: Context
) -> Dict[str, Any]:
    """Updates a specific campaign section."""
    # Exclude campaign_id from the payload since it's in the URL
    section_data = section.model_dump(exclude={"campaign_id"})
    logger.info(f"Updating section {section_id} for campaign {section.campaign_id}")
    return await forward_request(
        "PUT",
        f"/campaigns/{section.campaign_id}/sections/{section_id}/",
        token,
        section_data,
    )


@mcp.tool
async def delete_campaign_section(
    campaign_id: int, section_id: int, token: str, ctx: Context
) -> Dict[str, Any]:
    """Deletes a specific campaign section."""
    logger.info(f"Deleting section {section_id} for campaign {campaign_id}")
    return await forward_request(
        "DELETE", f"/campaigns/{campaign_id}/sections/{section_id}/", token
    )


@mcp.tool
async def generate_toc(toc_request: GenerateToc, token: str, ctx: Context) -> Dict[str, Any]:
    """Generates a table of contents for a campaign."""
    campaign_id = toc_request.campaign_id
    # The API expects a LLMGenerationRequest with required prompt and optional model_id_with_prefix
    request_body = {
        "model_id_with_prefix": None,  # Use default model
        "prompt": "Generate a table of contents"  # Required field
    }
    logger.info(f"Generating TOC for campaign {campaign_id}")
    return await forward_request(
        "POST", f"/campaigns/{campaign_id}/toc", token, request_body
    )


@mcp.tool
async def generate_titles(
    title_request: GenerateTitles, token: str, ctx: Context
) -> Dict[str, Any]:
    """Generates titles for a campaign section."""
    campaign_id = title_request.campaign_id
    # The API expects a LLMGenerationRequest with required prompt and optional model_id_with_prefix
    request_body = {
        "model_id_with_prefix": None,  # Use default model
        "prompt": "Generate titles"  # Required field
    }
    logger.info(f"Generating titles for campaign {campaign_id}")
    return await forward_request(
        "POST", f"/campaigns/{campaign_id}/titles", token, request_body
    )


@mcp.tool
async def seed_sections_from_toc(
    seed_request: SeedSections, token: str, ctx: Context
) -> Dict[str, Any]:
    """
    Seeds campaign sections from the generated TOC.
    Call this after generate_toc to create actual section records.
    If auto_populate is True, uses LLM to generate content for each section (slower but richer).
    """
    campaign_id = seed_request.campaign_id
    auto_populate = seed_request.auto_populate
    logger.info(f"Seeding sections from TOC for campaign {campaign_id} (auto_populate={auto_populate})")
    
    # This endpoint returns SSE events - we need to consume them and return a summary
    auth_token = token or _auth_token
    if not auth_token:
        raise Exception("Unauthorized. Please login or set credentials.")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}/seed_sections_from_toc?auto_populate={str(auto_populate).lower()}"
    
    sections_created = []
    errors = []
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
        async with client.stream("POST", url, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                # Skip empty lines
                if not line or not line.strip():
                    continue
                
                # Strip "data: " prefix (may be doubled due to SSE format)
                data_line = line
                while data_line.startswith("data: "):
                    data_line = data_line[6:]
                
                # Skip if nothing left after stripping
                if not data_line.strip():
                    continue
                
                try:
                    import json
                    event_data = json.loads(data_line)
                    event_type = event_data.get("event_type")
                    if event_type == "section_update":
                        section_data = event_data.get("section_data", {})
                        sections_created.append({
                            "id": section_data.get("id"),
                            "title": section_data.get("title"),
                            "type": section_data.get("type")
                        })
                    elif event_type == "error":
                        errors.append(event_data.get("message", "Unknown error"))
                    elif event_type == "complete":
                        logger.info(f"Seeding complete: {event_data}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE event: {line} - {e}")
    
    return {
        "success": len(errors) == 0,
        "campaign_id": campaign_id,
        "sections_created": len(sections_created),
        "sections": sections_created,
        "errors": errors if errors else None
    }


def run_server():
    """Run the MCP server with appropriate transport."""
    logger.info(f"API base URL: {API_BASE_URL}")
    
    # Check for Claude Desktop mode via environment variable
    transport_mode = os.getenv("MCP_TRANSPORT_MODE", "auto")
    logger.info(transport_mode)
    
    if transport_mode == "stdio" or (transport_mode == "auto" and not sys.stdin.isatty()):
        # Running via Claude Desktop - use stdio transport
        logger.info("Starting MCP server with stdio transport for Claude Desktop")
        mcp.run(transport="stdio", show_banner=False)
    else:
        # Running standalone - use SSE transport for HTTP clients
        logger.info(f"Starting MCP server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
        mcp.run(transport="sse", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT, show_banner=False)