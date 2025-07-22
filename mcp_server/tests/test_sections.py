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
    Test application focused on campaign section endpoints
    """
    # Get the token
    token = await get_auth_token()
    print("Successfully authenticated and obtained a token.")
    
    async with Client("http://127.0.0.1:4000/mcp/") as client:
        # Login to the server
        login_result = await client.call_tool("login", {"token": token})
        token = login_result.data
        print("Successfully logged in.")
        
        # Create a campaign
        new_campaign_data = {
            "title": "Test Campaign",
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
        
        # --- Campaign Sections ---
        print("\n--- Testing Campaign Section Endpoints ---")
        
        # 1. Create a section
        new_section_data = {
            "title": "Test Section",
            "content": "A test section",
            "campaign_id": campaign_id,
        }
        created_section = await client.call_tool(
            "create_campaign_section", {"section": new_section_data, "token": token}
        )
        section_id = created_section.data["id"]
        print(f"Created Section: {created_section.data}")
        
        # 2. Get a specific section
        retrieved_section = await client.call_tool(
            "get_campaign_section",
            {"campaign_id": campaign_id, "section_id": section_id, "token": token},
        )
        print(f"Retrieved Section: {retrieved_section.data}")
        
        # 3. List all sections
        all_sections = await client.call_tool(
            "list_campaign_sections", {"campaign_id": campaign_id, "token": token}
        )
        print(f"All Sections: {all_sections.data}")
        
        # 4. Update a section
        updated_section_data = {
            "title": "Updated Section",
            "content": "An updated test section",
            "campaign_id": campaign_id,
        }
        updated_section = await client.call_tool(
            "update_campaign_section",
            {"section_id": section_id, "section": updated_section_data, "token": token},
        )
        print(f"Updated Section: {updated_section.data}")
        
        # 5. Delete a section
        deleted_section = await client.call_tool(
            "delete_campaign_section",
            {"campaign_id": campaign_id, "section_id": section_id, "token": token},
        )
        print(f"Deleted Section: {deleted_section.data}")
        
        # Cleanup
        await client.call_tool(
            "delete_campaign", {"campaign_id": campaign_id, "token": token}
        )
        print(f"Deleted campaign {campaign_id}")

if __name__ == "__main__":
    asyncio.run(main())