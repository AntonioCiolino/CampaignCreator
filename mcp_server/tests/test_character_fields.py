import asyncio
import os
from dotenv import load_dotenv
from mcp.client.session import ClientSession as Client
import httpx

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
        created_character = await client.call_tool(
            "create_character", {"character": initial_character_data, "token": token}
        )
        character_id = created_character.data["id"]
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
        updated_character = await client.call_tool(
            "update_character",
            {
                "character_id": character_id,
                "character": updated_character_data,
                "token": token,
            },
        )
        print(f"Updated Character: {updated_character.data['name']}")

        # 3. Get the character and verify that all fields have been updated correctly
        retrieved_character = await client.call_tool(
            "get_character", {"character_id": character_id, "token": token}
        )
        retrieved_character_data = retrieved_character.data

        assert retrieved_character_data["name"] == updated_character_data["name"]
        assert retrieved_character_data["concept"] == updated_character_data["concept"]
        assert retrieved_character_data["description"] == updated_character_data["description"]
        assert (
            retrieved_character_data["appearance_description"]
            == updated_character_data["appearance_description"]
        )
        assert retrieved_character_data["stats"]["strength"] == updated_character_data["stats"]["strength"]
        assert retrieved_character_data["stats"]["dexterity"] == updated_character_data["stats"]["dexterity"]
        assert (
            retrieved_character_data["stats"]["constitution"]
            == updated_character_data["stats"]["constitution"]
        )
        assert (
            retrieved_character_data["stats"]["intelligence"]
            == updated_character_data["stats"]["intelligence"]
        )
        assert retrieved_character_data["stats"]["wisdom"] == updated_character_data["stats"]["wisdom"]
        assert retrieved_character_data["stats"]["charisma"] == updated_character_data["stats"]["charisma"]

        print("All character fields verified successfully.")

        # --- Cleanup ---
        print("\n--- Cleaning up created resources ---")
        await client.call_tool(
            "delete_character", {"character_id": character_id, "token": token}
        )
        print(f"Deleted character {character_id}")


if __name__ == "__main__":
    asyncio.run(main())
