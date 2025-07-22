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
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        response.raise_for_status()
        return response.json()["access_token"]

async def main():
    """Debug campaign section creation"""
    token = await get_auth_token()
    print("Successfully authenticated and obtained a token.")
    
    async with Client("http://127.0.0.1:4000/mcp/") as client:
        # Login to the server
        login_result = await client.call_tool("login", {"token": token})
        token = login_result.data
        print("Successfully logged in.")
        
        # Create a campaign first
        new_campaign_data = {
            "title": "Debug Campaign",
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
        
        # Test section creation
        try:
            # Test with direct API call first
            async with httpx.AsyncClient(follow_redirects=True) as api_client:
                headers = {"Authorization": f"Bearer {token}"}
                section_data = {"title": "Test Section", "content": "A test section"}
                response = await api_client.post(
                    f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}/sections/", 
                    headers=headers, 
                    json=section_data
                )
                print(f"Direct API call: {response.status_code}")
                if response.status_code == 201:
                    print(f"Direct API success: {response.json()}")
                else:
                    print(f"Direct API error: {response.text}")
            
            # Now test with MCP
            new_section_data = {
                "title": "Test Section",
                "content": "A test section",
                "campaign_id": campaign_id,
            }
            print(f"Calling create_campaign_section with: {new_section_data}")
            created_section = await client.call_tool(
                "create_campaign_section", {"section": new_section_data, "token": token}
            )
            print(f"Created Section: {created_section.data}")
            
        except Exception as e:
            print(f"Error: {e}")
            
        # Cleanup
        await client.call_tool(
            "delete_campaign", {"campaign_id": campaign_id, "token": token}
        )
        print(f"Deleted campaign {campaign_id}")

if __name__ == "__main__":
    asyncio.run(main())