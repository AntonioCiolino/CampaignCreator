import pytest
from httpx import AsyncClient
from fastmcp.mcp import MCP
from mcp_server.src.server import mcp, API_BASE_URL, auto_authenticate
from mcp_server.src.models.schemas import Character, CharacterStats

@pytest.fixture
async def authenticated_client():
    """Provides an authenticated client for testing."""
    token = await auto_authenticate()
    async with AsyncClient(app=mcp.app, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client

@pytest.mark.asyncio
async def test_character_fields(authenticated_client: AsyncClient):
    """
    Tests that all character fields are correctly created, updated, and retrieved.
    """
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
    create_response = await authenticated_client.post("/characters/", json=initial_character_data)
    assert create_response.status_code == 201
    created_character = create_response.json()
    character_id = created_character["id"]

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
    update_response = await authenticated_client.put(f"/characters/{character_id}/", json=updated_character_data)
    assert update_response.status_code == 200

    # 3. Get the character and verify that all fields have been updated correctly
    get_response = await authenticated_client.get(f"/characters/{character_id}/")
    assert get_response.status_code == 200
    retrieved_character = get_response.json()

    assert retrieved_character["name"] == updated_character_data["name"]
    assert retrieved_character["concept"] == updated_character_data["concept"]
    assert retrieved_character["description"] == updated_character_data["description"]
    assert retrieved_character["appearance_description"] == updated_character_data["appearance_description"]
    assert retrieved_character["stats"]["strength"] == updated_character_data["stats"]["strength"]
    assert retrieved_character["stats"]["dexterity"] == updated_character_data["stats"]["dexterity"]
    assert retrieved_character["stats"]["constitution"] == updated_character_data["stats"]["constitution"]
    assert retrieved_character["stats"]["intelligence"] == updated_character_data["stats"]["intelligence"]
    assert retrieved_character["stats"]["wisdom"] == updated_character_data["stats"]["wisdom"]
    assert retrieved_character["stats"]["charisma"] == updated_character_data["stats"]["charisma"]
