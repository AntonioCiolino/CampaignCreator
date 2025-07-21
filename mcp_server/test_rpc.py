import asyncio
import os
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()

async def main():
    """
    A simple test application that connects to the MCP server and calls the available tools.
    """
    # Get the token from the environment variables
    token = os.getenv("CAMPAIGN_CRAFTER_TOKEN")
    if not token:
        print("Error: CAMPAIGN_CRAFTER_TOKEN not found in .env file.")
        return

    async with Client("http://127.0.0.1:4000") as client:
        # Login to the server
        login_result = await client.call_tool("login", {"token": token})
        print(login_result.text)

        # List the available tools
        tools = await client.call_tool("list_tools")
        print("Available tools:", tools.json())

        # List the campaigns
        campaigns = await client.call_tool("list_campaigns")
        print("Campaigns:", campaigns.json())

        # Create a new campaign
        new_campaign = {
            "title": "My Awesome Campaign",
            "concept": "A campaign about a group of heroes saving the world."
        }
        created_campaign = await client.call_tool("create_campaign", {"campaign": new_campaign})
        print("Created campaign:", created_campaign.json())

if __name__ == "__main__":
    asyncio.run(main())
