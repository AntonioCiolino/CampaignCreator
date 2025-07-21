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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def main():
    """
    A simple test application that connects to the MCP server and calls the available tools.
    """
    # Get the token from the environment variables
    token = os.getenv("CAMPAIGN_CRAFTER_TOKEN")
    if not token:
        print("CAMPAIGN_CRAFTER_TOKEN not found, attempting to authenticate...")
        try:
            token = await get_auth_token()
            print("Successfully authenticated and obtained a token.")
        except Exception as e:
            print(f"Error authenticating: {e}")
            return

    async with Client("http://127.0.0.1:4000/mcp/") as client:
        # Login to the server
        token = await client.call_tool("login", {"token": token})
        print("Successfully logged in.")

        # List the available tools
        tools = await client.call_tool("list_tools")
        print("Available tools:", tools.json())

        # List the campaigns
        campaigns = await client.call_tool("list_campaigns", {"token": token})
        print("Campaigns:", campaigns.json())

        # Create a new campaign
        new_campaign = {
            "title": "My Awesome Campaign",
            "concept": "A campaign about a group of heroes saving the world."
        }
        created_campaign = await client.call_tool("create_campaign", {"campaign": new_campaign, "token": token})
        print("Created campaign:", created_campaign.json())

if __name__ == "__main__":
    asyncio.run(main())
