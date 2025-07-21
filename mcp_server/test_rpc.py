import asyncio
from fastmcp import Client

async def main():
    """
    A simple test application that connects to the MCP server and calls the available tools.
    """
    # Replace with your actual token
    token = "your_auth_token_here"

    async with Client("http://127.0.0.1:4000") as client:
        # Login to the server
        login_result = await client.call_tool("login", {"token": token})
        print(login_result.text)

        # List the available tools
        tools = await client.list_tools()
        print("Available tools:", [tool.name for tool in tools])

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
