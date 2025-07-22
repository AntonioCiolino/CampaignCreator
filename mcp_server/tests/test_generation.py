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
    Test the generation endpoints of the MCP server.
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

        # Create a test campaign
        print("\n--- Creating a test campaign ---")
        new_campaign_data = {
            "title": "Fantasy Adventure",
            "concept": "A high fantasy adventure where heroes explore ancient ruins and battle mythical creatures.",
        }
        created_campaign = await client.call_tool(
            "create_campaign", {"campaign": new_campaign_data, "token": token}
        )
        campaign_id = created_campaign.data["id"]
        print(f"Created Campaign: {created_campaign.data}")
        
        # Update the campaign to ensure it has a concept
        updated_campaign = await client.call_tool(
            "update_campaign", 
            {"campaign_id": campaign_id, "campaign": new_campaign_data, "token": token}
        )
        print(f"Updated Campaign with concept: {updated_campaign.data.get('concept')}")
        
        # Create a section for the campaign
        print("\n--- Creating a test section ---")
        new_section_data = {
            "title": "Introduction",
            "content": "This is the introduction to the campaign.",
            "campaign_id": campaign_id,
        }
        created_section = await client.call_tool(
            "create_campaign_section", {"section": new_section_data, "token": token}
        )
        section_id = created_section.data["id"]
        print(f"Created Section: {created_section.data}")

        # --- Testing TOC Generation ---
        print("\n--- Testing TOC Generation ---")
        try:
            toc_result = await client.call_tool(
                "generate_toc", {"toc_request": {"campaign_id": campaign_id}, "token": token}
            )
            print(f"Generated TOC: {toc_result.data}")
            
            # Verify the TOC was generated successfully
            if "display_toc" in toc_result.data and toc_result.data["display_toc"]:
                print(f"TOC generation successful! Generated {len(toc_result.data['display_toc'])} sections.")
                for i, section in enumerate(toc_result.data["display_toc"]):
                    print(f"  {i+1}. {section.get('title', 'Untitled')} - Type: {section.get('type', 'generic')}")
            else:
                print("TOC generation failed or returned unexpected format.")
                print(f"Response data: {toc_result.data}")
        except Exception as e:
            print(f"Error generating TOC: {e}")

        # --- Testing Title Generation ---
        print("\n--- Testing Title Generation ---")
        try:
            titles_result = await client.call_tool(
                "generate_titles",
                {
                    "title_request": {"campaign_id": campaign_id, "section_id": section_id},
                    "token": token,
                },
            )
            print(f"Generated Titles: {titles_result.data}")
            
            # Verify the titles were generated successfully
            if "titles" in titles_result.data:
                print(f"Title generation successful! Generated {len(titles_result.data['titles'])} titles.")
                for i, title in enumerate(titles_result.data["titles"]):
                    print(f"  {i+1}. {title}")
            else:
                print("Title generation failed or returned unexpected format.")
                print(f"Response data: {titles_result.data}")
        except Exception as e:
            print(f"Error generating titles: {e}")

        # Clean up - delete the test campaign
        print("\n--- Cleaning up ---")
        await client.call_tool(
            "delete_campaign", {"campaign_id": campaign_id, "token": token}
        )
        print(f"Deleted test campaign {campaign_id}")


if __name__ == "__main__":
    asyncio.run(main())