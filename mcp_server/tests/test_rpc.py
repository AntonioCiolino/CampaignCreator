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
        login_result = await client.call_tool("get_user_info", {"token": token})
        token = login_result.data
        print("Successfully logged in.")

        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        # --- Campaigns ---
        print("\n--- Testing Campaign Endpoints ---")
        new_campaign_data = {"title": "My Awesome Campaign", "concept": "A test campaign"}
        created_campaign = await client.call_tool("create_campaign", {"campaign": new_campaign_data, "token": token})
        campaign_id = created_campaign.data["id"]
        print(f"Created Campaign: {created_campaign.data}")

        retrieved_campaign = await client.call_tool("get_campaign", {"campaign_id": campaign_id, "token": token})
        print(f"Retrieved Campaign: {retrieved_campaign.data}")

        all_campaigns = await client.call_tool("list_campaigns", {"token": token})
        print(f"All Campaigns: {all_campaigns.data}")

        updated_campaign_data = {"title": "My Updated Campaign", "concept": "An updated test campaign"}
        updated_campaign = await client.call_tool("update_campaign", {"campaign_id": campaign_id, "campaign": updated_campaign_data, "token": token})
        print(f"Updated Campaign: {updated_campaign.data}")

        # --- Characters ---
        print("\n--- Testing Character Endpoints ---")
        new_character_data = {"name": "Test Character", "concept": "A test character"}
        created_character = await client.call_tool("create_character", {"character": new_character_data, "token": token})
        character_id = created_character.data["id"]
        print(f"Created Character: {created_character.data}")

        retrieved_character = await client.call_tool("get_character", {"character_id": character_id, "token": token})
        print(f"Retrieved Character: {retrieved_character.data}")

        all_characters = await client.call_tool("list_characters", {"token": token})
        print(f"All Characters: {all_characters.data}")

        updated_character_data = {"name": "Updated Character", "concept": "An updated test character"}
        updated_character = await client.call_tool("update_character", {"character_id": character_id, "character": updated_character_data, "token": token})
        print(f"Updated Character: {updated_character.data}")

        # --- Campaign Sections ---
        print("\n--- Testing Campaign Section Endpoints ---")
        new_section_data = {"title": "Test Section", "content": "A test section", "campaign_id": campaign_id}
        created_section = await client.call_tool("create_campaign_section", {"section": new_section_data, "token": token})
        section_id = created_section.data["id"]
        print(f"Created Section: {created_section.data}")

        retrieved_section = await client.call_tool("get_campaign_section", {"campaign_id": campaign_id, "section_id": section_id, "token": token})
        print(f"Retrieved Section: {retrieved_section.data}")

        all_sections = await client.call_tool("list_campaign_sections", {"campaign_id": campaign_id, "token": token})
        print(f"All Sections: {all_sections.data}")

        updated_section_data = {"title": "Updated Section", "content": "An updated test section", "campaign_id": campaign_id}
        updated_section = await client.call_tool("update_campaign_section", {"section_id": section_id, "section": updated_section_data, "token": token})
        print(f"Updated Section: {updated_section.data}")

        # --- Linking ---
        print("\n--- Testing Linking Endpoints ---")
        await client.call_tool("link_character_to_campaign", {"link": {"campaign_id": campaign_id, "character_id": character_id}, "token": token})
        print("Linked character to campaign.")

        await client.call_tool("unlink_character_from_campaign", {"link": {"campaign_id": campaign_id, "character_id": character_id}, "token": token})
        print("Unlinked character from campaign.")

        # --- Generation ---
        print("\n--- Testing Generation Endpoints ---")
        toc = await client.call_tool("generate_toc", {"toc_request": {"campaign_id": campaign_id}, "token": token})
        print(f"Generated TOC: {toc.data}")

        titles = await client.call_tool("generate_titles", {"title_request": {"campaign_id": campaign_id, "section_id": section_id}, "token": token})
        print(f"Generated Titles: {titles.data}")

        # --- Cleanup ---
        print("\n--- Cleaning up created resources ---")
        await client.call_tool("delete_campaign_section", {"campaign_id": campaign_id, "section_id": section_id, "token": token})
        print(f"Deleted section {section_id}")

        await client.call_tool("delete_character", {"character_id": character_id, "token": token})
        print(f"Deleted character {character_id}")

        await client.call_tool("delete_campaign", {"campaign_id": campaign_id, "token": token})
        print(f"Deleted campaign {campaign_id}")


if __name__ == "__main__":
    asyncio.run(main())
