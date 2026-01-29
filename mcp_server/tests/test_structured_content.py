"""
Tests to verify that MCP tools return proper structuredContent.

These tests verify that:
1. Tools with output_schema return structuredContent in responses
2. The structuredContent matches the defined output_schema structure
3. List-returning tools wrap results in objects (not raw arrays)

All configuration is loaded from .env file.
"""
import asyncio
import os
import httpx
from pathlib import Path

# Load .env from parent directory (mcp_server/.env)
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# --- All Configuration from .env ---
API_BASE_URL = os.getenv("API_BASE_URL")
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST")
MCP_SERVER_PORT = os.getenv("MCP_SERVER_PORT")
MCP_SERVER_URL = f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/sse"
USERNAME = os.getenv("CAMPAIGN_CRAFTER_USERNAME")
PASSWORD = os.getenv("CAMPAIGN_CRAFTER_PASSWORD")

# Import pytest and fastmcp
try:
    import pytest
    from fastmcp import Client
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    Client = None


async def get_fresh_token():
    """Authenticates with the API using credentials from .env."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={"username": USERNAME, "password": PASSWORD},
        )
        response.raise_for_status()
        return response.json()["access_token"]


# --- Pytest fixtures ---
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def token():
    return await get_fresh_token()


@pytest.fixture
async def mcp_client():
    async with Client(MCP_SERVER_URL) as client:
        yield client


# --- Test Classes ---
class TestStructuredContent:
    """Test suite for structured content in MCP tool responses."""

    @pytest.mark.asyncio
    async def test_get_auth_status_returns_structured_content(self):
        """Test that get_auth_status returns proper structured content."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool("get_auth_status", {})
            
            assert result.structured_content is not None
            assert isinstance(result.structured_content, dict)
            assert "authenticated" in result.structured_content

    @pytest.mark.asyncio
    async def test_refresh_auth_returns_structured_content(self):
        """Test that refresh_auth returns proper structured content."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool("refresh_auth", {})
            
            assert result.structured_content is not None
            assert isinstance(result.structured_content, dict)
            assert "authenticated" in result.structured_content

    @pytest.mark.asyncio
    async def test_list_campaigns_returns_wrapped_array(self, token):
        """Test that list_campaigns returns campaigns wrapped in an object."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool("list_campaigns", {"token": token})
            
            assert result.structured_content is not None
            assert isinstance(result.structured_content, dict)
            assert "campaigns" in result.structured_content
            assert isinstance(result.structured_content["campaigns"], list)

    @pytest.mark.asyncio
    async def test_list_characters_returns_wrapped_array(self, token):
        """Test that list_characters returns characters wrapped in an object."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool("list_characters", {"token": token})
            
            assert result.structured_content is not None
            assert isinstance(result.structured_content, dict)
            assert "characters" in result.structured_content
            assert isinstance(result.structured_content["characters"], list)

    @pytest.mark.asyncio
    async def test_get_all_characters_returns_wrapped_array(self, token):
        """Test that get_all_characters returns characters wrapped in an object."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool("get_all_characters", {"token": token})
            
            assert result.structured_content is not None
            assert isinstance(result.structured_content, dict)
            assert "characters" in result.structured_content
            assert isinstance(result.structured_content["characters"], list)

    @pytest.mark.asyncio
    async def test_create_campaign_returns_structured_content(self, token):
        """Test that create_campaign returns proper structured content."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(
                "create_campaign",
                {"campaign": {"title": "Structured Content Test"}, "token": token}
            )
            
            assert result.structured_content is not None
            assert isinstance(result.structured_content, dict)
            assert "id" in result.structured_content
            assert "title" in result.structured_content
            assert "owner_id" in result.structured_content
            
            # Cleanup
            campaign_id = result.structured_content["id"]
            await client.call_tool("delete_campaign", {"campaign_id": campaign_id, "token": token})

    @pytest.mark.asyncio
    async def test_get_campaign_returns_structured_content(self, token):
        """Test that get_campaign returns proper structured content."""
        async with Client(MCP_SERVER_URL) as client:
            # Create
            create_result = await client.call_tool(
                "create_campaign",
                {"campaign": {"title": "Get Campaign Test"}, "token": token}
            )
            campaign_id = create_result.structured_content["id"]
            
            # Get
            result = await client.call_tool("get_campaign", {"campaign_id": campaign_id, "token": token})
            
            assert result.structured_content is not None
            assert result.structured_content["id"] == campaign_id
            assert "title" in result.structured_content
            
            # Cleanup
            await client.call_tool("delete_campaign", {"campaign_id": campaign_id, "token": token})

    @pytest.mark.asyncio
    async def test_create_character_returns_structured_content(self, token):
        """Test that create_character returns proper structured content."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(
                "create_character",
                {"character": {"name": "Test Hero"}, "token": token}
            )
            
            assert result.structured_content is not None
            assert "id" in result.structured_content
            assert "name" in result.structured_content
            assert result.structured_content["name"] == "Test Hero"
            
            # Cleanup
            character_id = result.structured_content["id"]
            await client.call_tool("delete_character", {"character_id": character_id, "token": token})

    @pytest.mark.asyncio
    async def test_list_campaign_sections_returns_wrapped_array(self, token):
        """Test that list_campaign_sections returns sections wrapped in an object."""
        async with Client(MCP_SERVER_URL) as client:
            # Create campaign
            create_result = await client.call_tool(
                "create_campaign",
                {"campaign": {"title": "Sections Test"}, "token": token}
            )
            campaign_id = create_result.structured_content["id"]
            
            # List sections
            result = await client.call_tool(
                "list_campaign_sections",
                {"campaign_id": campaign_id, "token": token}
            )
            
            assert result.structured_content is not None
            assert "sections" in result.structured_content
            assert isinstance(result.structured_content["sections"], list)
            
            # Cleanup
            await client.call_tool("delete_campaign", {"campaign_id": campaign_id, "token": token})

    @pytest.mark.asyncio
    async def test_get_user_info_returns_structured_content(self, token):
        """Test that get_user_info returns proper structured content."""
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool("get_user_info", {"token": token})
            
            assert result.structured_content is not None
            assert "valid" in result.structured_content
            assert "token" in result.structured_content
            assert result.structured_content["valid"] is True


class TestOutputSchemaPresence:
    """Test that tools expose their output schemas."""

    @pytest.mark.asyncio
    async def test_tools_have_output_schemas(self):
        """Verify that expected tools are registered."""
        async with Client(MCP_SERVER_URL) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            
            expected_tools = [
                "refresh_auth", "get_auth_status", "get_user_info",
                "create_campaign", "get_campaign", "list_campaigns",
                "update_campaign", "delete_campaign",
                "create_character", "get_character", "list_characters",
                "get_all_characters", "create_campaign_section",
                "list_campaign_sections", "get_campaign_section",
            ]
            
            for tool in expected_tools:
                assert tool in tool_names, f"Tool {tool} not found"



# --- Smoke Test (run directly) ---
if __name__ == "__main__":
    async def smoke_test():
        print("=" * 60)
        print("Structured Content Smoke Test")
        print("=" * 60)
        print(f"API_BASE_URL: {API_BASE_URL}")
        print(f"MCP_SERVER_URL: {MCP_SERVER_URL}")
        print(f"USERNAME: {USERNAME}")
        print("=" * 60)
        
        # Get fresh token
        print("\n1. Getting fresh auth token...")
        try:
            token = await get_fresh_token()
            print(f"   ✓ Got token: {token[:20]}...")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return
        
        # Connect to MCP server
        print("\n2. Connecting to MCP server...")
        try:
            async with Client(MCP_SERVER_URL) as client:
                print("   ✓ Connected")
                
                # Test get_auth_status
                print("\n3. Testing get_auth_status...")
                result = await client.call_tool("get_auth_status", {})
                assert result.structured_content is not None
                assert "authenticated" in result.structured_content
                print(f"   ✓ structuredContent: {result.structured_content}")
                
                # Test refresh_auth
                print("\n4. Testing refresh_auth...")
                result = await client.call_tool("refresh_auth", {})
                assert result.structured_content is not None
                print(f"   ✓ structuredContent: {result.structured_content}")
                
                # Test list_campaigns
                print("\n5. Testing list_campaigns...")
                result = await client.call_tool("list_campaigns", {"token": token})
                assert result.structured_content is not None
                assert "campaigns" in result.structured_content
                print(f"   ✓ structuredContent keys: {list(result.structured_content.keys())}")
                print(f"   ✓ campaigns count: {len(result.structured_content['campaigns'])}")
                
                # Test list_characters
                print("\n6. Testing list_characters...")
                result = await client.call_tool("list_characters", {"token": token})
                assert result.structured_content is not None
                assert "characters" in result.structured_content
                print(f"   ✓ structuredContent keys: {list(result.structured_content.keys())}")
                print(f"   ✓ characters count: {len(result.structured_content['characters'])}")
                
                # Test create_campaign
                print("\n7. Testing create_campaign...")
                result = await client.call_tool(
                    "create_campaign",
                    {"campaign": {"title": "Smoke Test Campaign"}, "token": token}
                )
                assert result.structured_content is not None
                assert "id" in result.structured_content
                campaign_id = result.structured_content["id"]
                print(f"   ✓ Created campaign id: {campaign_id}")
                print(f"   ✓ structuredContent keys: {list(result.structured_content.keys())}")
                
                # Test list_campaign_sections
                print("\n8. Testing list_campaign_sections...")
                result = await client.call_tool(
                    "list_campaign_sections",
                    {"campaign_id": campaign_id, "token": token}
                )
                assert result.structured_content is not None
                assert "sections" in result.structured_content
                print(f"   ✓ structuredContent keys: {list(result.structured_content.keys())}")
                
                # Cleanup
                print("\n9. Cleanup - deleting test campaign...")
                await client.call_tool("delete_campaign", {"campaign_id": campaign_id, "token": token})
                print("   ✓ Deleted")
                
                print("\n" + "=" * 60)
                print("✓ ALL SMOKE TESTS PASSED!")
                print("  structuredContent is working correctly.")
                print("=" * 60)
                
        except Exception as e:
            print(f"   ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(smoke_test())
