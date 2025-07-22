import asyncio
import os
import httpx
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TEST_USERNAME = os.getenv("CAMPAIGN_CRAFTER_USERNAME", "admin")
TEST_PASSWORD = os.getenv("CAMPAIGN_CRAFTER_PASSWORD", "changeme")

async def get_auth_token():
    """
    Authenticates with the main application and returns an access token.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        response.raise_for_status()
        return response.json()["access_token"]

async def main():
    """
    Test application focused on character linking endpoints
    """
    # Get the token
    token = await get_auth_token()
    print("Successfully authenticated and obtained a token.")
    
    async with Client("http://127.0.0.1:4000/mcp/") as client:
        # Login to the server
        login_result = await client.call_tool("get_user_info", {"token": token})
        token = login_result.data
        print("Successfully logged in.")
        
        # Create a campaign
        new_campaign_data = {
            "title": "Test Campaign",
            "concept": "A fantasy adventure campaign",
        }
        created_campaign = await client.call_tool(
            "create_campaign", {"campaign": new_campaign_data, "token": token}
        )
        campaign_id = created_campaign.data["id"]
        print(f"Created Campaign: {campaign_id}")
        
        # Create a character
        new_character_data = {"name": "Test Character", "concept": "A test character"}
        created_character = await client.call_tool(
            "create_character", {"character": new_character_data, "token": token}
        )
        character_id = created_character.data["id"]
        print(f"Created Character: {character_id}")
        
        # --- Linking Endpoints ---
        print("\n--- Testing Linking Endpoints ---")
        
        # 1. Link character to campaign
        link_result = await client.call_tool(
            "link_character_to_campaign",
            {
                "link": {"campaign_id": campaign_id, "character_id": character_id},
                "token": token,
            },
        )
        print(f"Linked character to campaign: {link_result.data}")
        
        # 2. Unlink character from campaign
        unlink_result = await client.call_tool(
            "unlink_character_from_campaign",
            {
                "link": {"campaign_id": campaign_id, "character_id": character_id},
                "token": token,
            },
        )
        print(f"Unlinked character from campaign: {unlink_result.data}")
        
        # Cleanup
        await client.call_tool(
            "delete_character", {"character_id": character_id, "token": token}
        )
        print(f"Deleted character {character_id}")
        
        await client.call_tool(
            "delete_campaign", {"campaign_id": campaign_id, "token": token}
        )
        print(f"Deleted campaign {campaign_id}")

if __name__ == "__main__":
    asyncio.run(main())