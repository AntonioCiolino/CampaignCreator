import asyncio
import os
import httpx
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()

## AC: this is WRONG - it needs to call mcp tools. RETOOL THIS IT FAILS

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
    Test that all character fields are correctly created, updated, and retrieved.
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

        # 1. Create a character with all fields populated
        initial_character_data = {
            "name": "Test Character",
            "concept": "A test character concept.",
            "description": "A test character description.",
            "appearance_description": "A test character appearance.",
            "stats": {
                "strength": 10,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 16,
                "wisdom": 18,
                "charisma": 20,
            },
        }
        create_response = await client.post("/characters/", json=initial_character_data)
        assert create_response.status_code == 201
        created_character = create_response.json()
        character_id = created_character["id"]
        print(f"Created Character: {character_id}")

        # 2. Update the character with new values for all fields
        updated_character_data = {
            "name": "Updated Character",
            "concept": "An updated character concept.",
            "description": "An updated character description.",
            "appearance_description": "An updated character appearance.",
            "stats": {
                "strength": 20,
                "dexterity": 18,
                "constitution": 16,
                "intelligence": 14,
                "wisdom": 12,
                "charisma": 10,
            },
        }
        update_response = await client.put(
            f"/characters/{character_id}/", json=updated_character_data
        )
        assert update_response.status_code == 200

        # 3. Get the character and verify that all fields have been updated correctly
        get_response = await client.get(f"/characters/{character_id}/")
        assert get_response.status_code == 200
        retrieved_character = get_response.json()

        assert retrieved_character_data["name"] == updated_character_data["name"]
        assert retrieved_character_data["description"] == updated_character_data["description"]
        assert (
            retrieved_character["appearance_description"]
            == updated_character_data["appearance_description"]
        )
        assert retrieved_character["stats"]["strength"] == updated_character_data["stats"]["strength"]
        assert retrieved_character["stats"]["dexterity"] == updated_character_data["stats"]["dexterity"]
        assert (
            retrieved_character["stats"]["constitution"]
            == updated_character_data["stats"]["constitution"]
        )
        assert (
            retrieved_character["stats"]["intelligence"]
            == updated_character_data["stats"]["intelligence"]
        )
        assert retrieved_character["stats"]["wisdom"] == updated_character_data["stats"]["wisdom"]
        assert retrieved_character["stats"]["charisma"] == updated_character_data["stats"]["charisma"]

        print("All character fields verified successfully.")

        # --- Cleanup ---
        print("\n--- Cleaning up created resources ---")
        delete_response = await client.delete(f"/characters/{character_id}/")
        assert delete_response.status_code == 200
        print(f"Deleted character {character_id}")


if __name__ == "__main__":
    asyncio.run(main())
