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
    Test all endpoints of the MCP server.
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
        login_result = await client.call_tool("login", {"token": token})
        token = login_result.data
        print("Successfully logged in.")

        # List available tools
        tools = await client.list_tools()
        print("\n--- Available Tools ---")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        # --- Campaigns ---
        print("\n--- Testing Campaign Endpoints ---")
        new_campaign_data = {
            "title": "My Awesome Campaign",
            "concept": "A fantasy adventure campaign where heroes explore ancient dungeons and fight dragons",
        }
        created_campaign = await client.call_tool(
            "create_campaign", {"campaign": new_campaign_data, "token": token}
        )
        campaign_id = created_campaign.data["id"]
        print(f"Created Campaign: {campaign_id}")
        
        # Update campaign to ensure concept is properly set
        updated_campaign = await client.call_tool(
            "update_campaign", 
            {"campaign_id": campaign_id, "campaign": new_campaign_data, "token": token}
        )
        print(f"Updated Campaign with concept: {updated_campaign.data.get('concept')}")

        retrieved_campaign = await client.call_tool(
            "get_campaign", {"campaign_id": campaign_id, "token": token}
        )
        print(f"Retrieved Campaign: {retrieved_campaign.data['title']}")

        all_campaigns = await client.call_tool("list_campaigns", {"token": token})
        print(f"All Campaigns: {len(all_campaigns.data)} campaigns found")

        updated_campaign_data = {
            "title": "My Updated Campaign",
            "concept": "An updated test campaign",
        }
        updated_campaign = await client.call_tool(
            "update_campaign",
            {
                "campaign_id": campaign_id,
                "campaign": updated_campaign_data,
                "token": token,
            },
        )
        print(f"Updated Campaign: {updated_campaign.data['title']}")

        # --- Characters ---
        print("\n--- Testing Character Endpoints ---")
        new_character_data = {"name": "Test Character", "concept": "A test character"}
        created_character = await client.call_tool(
            "create_character", {"character": new_character_data, "token": token}
        )
        character_id = created_character.data["id"]
        print(f"Created Character: {character_id}")

        retrieved_character = await client.call_tool(
            "get_character", {"character_id": character_id, "token": token}
        )
        print(f"Retrieved Character: {retrieved_character.data['name']}")

        all_characters = await client.call_tool("list_characters", {"token": token})
        print(f"All Characters: {len(all_characters.data)} characters found")

        updated_character_data = {
            "name": "Updated Character",
            "concept": "An updated test character",
        }
        updated_character = await client.call_tool(
            "update_character",
            {
                "character_id": character_id,
                "character": updated_character_data,
                "token": token,
            },
        )
        print(f"Updated Character: {updated_character.data['name']}")

        # --- Campaign Sections ---
        print("\n--- Testing Campaign Section Endpoints ---")
        new_section_data = {
            "title": "Test Section",
            "content": "A test section",
            "campaign_id": campaign_id,
        }
        created_section = await client.call_tool(
            "create_campaign_section", {"section": new_section_data, "token": token}
        )
        section_id = created_section.data["id"]
        print(f"Created Section: {section_id}")

        retrieved_section = await client.call_tool(
            "get_campaign_section",
            {"campaign_id": campaign_id, "section_id": section_id, "token": token},
        )
        print(f"Retrieved Section: {retrieved_section.data['title']}")

        all_sections = await client.call_tool(
            "list_campaign_sections", {"campaign_id": campaign_id, "token": token}
        )
        print(f"All Sections: {len(all_sections.data)} sections found")

        updated_section_data = {
            "title": "Updated Section",
            "content": "An updated test section",
            "campaign_id": campaign_id,
        }
        updated_section = await client.call_tool(
            "update_campaign_section",
            {"section_id": section_id, "section": updated_section_data, "token": token},
        )
        print(f"Updated Section: {updated_section.data['title']}")

        # --- Linking ---
        print("\n--- Testing Linking Endpoints ---")
        link_result = await client.call_tool(
            "link_character_to_campaign",
            {
                "link": {"campaign_id": campaign_id, "character_id": character_id},
                "token": token,
            },
        )
        print(f"Linked character to campaign: {link_result.data}")

        unlink_result = await client.call_tool(
            "unlink_character_from_campaign",
            {
                "link": {"campaign_id": campaign_id, "character_id": character_id},
                "token": token,
            },
        )
        print(f"Unlinked character from campaign: {unlink_result.data}")

        # --- Generation ---
        print("\n--- Testing Generation Endpoints ---")
        try:
            toc_result = await client.call_tool(
                "generate_toc", {"toc_request": {"campaign_id": campaign_id}, "token": token}
            )
            print(f"Generated TOC: {len(toc_result.data.get('display_toc', []))} sections")
            
            # Verify the TOC was generated successfully
            if "display_toc" in toc_result.data and toc_result.data["display_toc"]:
                print(f"TOC generation successful! Generated {len(toc_result.data['display_toc'])} sections.")
                for i, section in enumerate(toc_result.data["display_toc"]):
                    print(f"  {i+1}. {section.get('title', 'Untitled')} - Type: {section.get('type', 'generic')}")
            else:
                print("TOC generation failed or returned unexpected format.")
        except Exception as e:
            print(f"Error generating TOC: {e}")

        try:
            titles_result = await client.call_tool(
                "generate_titles",
                {
                    "title_request": {"campaign_id": campaign_id, "section_id": section_id},
                    "token": token,
                },
            )
            print(f"Generated Titles: {len(titles_result.data.get('titles', []))} titles")
            
            # Verify the titles were generated successfully
            if "titles" in titles_result.data:
                print(f"Title generation successful! Generated {len(titles_result.data['titles'])} titles.")
                for i, title in enumerate(titles_result.data["titles"]):
                    print(f"  {i+1}. {title}")
            else:
                print("Title generation failed or returned unexpected format.")
        except Exception as e:
            print(f"Error generating titles: {e}")

        # --- Cleanup ---
        print("\n--- Cleaning up created resources ---")
        await client.call_tool(
            "delete_campaign_section",
            {"campaign_id": campaign_id, "section_id": section_id, "token": token},
        )
        print(f"Deleted section {section_id}")

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