import pytest
from unittest.mock import AsyncMock, patch
from mcp_server.main_rpc import mcp, Campaign, Character, CampaignSection, LinkCharacter, GenerateToc, GenerateTitles

@pytest.fixture
def mock_context():
    return AsyncMock()

@pytest.mark.asyncio
async def test_login_success(mock_context):
    with patch("mcp_server.main_rpc.httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        token = await mcp._tools["login"].function("test_token", mock_context)
        assert token == "test_token"

@pytest.mark.asyncio
async def test_login_failure(mock_context):
    with patch("mcp_server.main_rpc.httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        with pytest.raises(Exception, match="Invalid token"):
            await mcp._tools["login"].function("test_token", mock_context)

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_create_campaign(mock_forward_request, mock_context):
    campaign = Campaign(title="Test Campaign", concept="A test campaign")
    mock_forward_request.return_value = {"id": 1, **campaign.model_dump()}
    result = await mcp._tools["create_campaign"].function(campaign, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/campaigns", "test_token", campaign.model_dump())
    assert result["id"] == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_get_campaign(mock_forward_request, mock_context):
    mock_forward_request.return_value = {"id": 1, "title": "Test Campaign", "concept": "A test campaign"}
    result = await mcp._tools["get_campaign"].function(1, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("GET", "/campaigns/1", "test_token")
    assert result["id"] == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_list_campaigns(mock_forward_request, mock_context):
    mock_forward_request.return_value = [{"id": 1, "title": "Test Campaign", "concept": "A test campaign"}]
    result = await mcp._tools["list_campaigns"].function("test_token", mock_context)
    mock_forward_request.assert_called_once_with("GET", "/campaigns", "test_token")
    assert len(result) == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_update_campaign(mock_forward_request, mock_context):
    campaign = Campaign(title="Updated Campaign", concept="An updated concept")
    mock_forward_request.return_value = {"id": 1, **campaign.model_dump()}
    result = await mcp._tools["update_campaign"].function(1, campaign, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("PUT", "/campaigns/1", "test_token", campaign.model_dump())
    assert result["title"] == "Updated Campaign"

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_delete_campaign(mock_forward_request, mock_context):
    mock_forward_request.return_value = {}
    await mcp._tools["delete_campaign"].function(1, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("DELETE", "/campaigns/1", "test_token")

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_create_character(mock_forward_request, mock_context):
    character = Character(name="Test Character", concept="A test character")
    mock_forward_request.return_value = {"id": 1, **character.model_dump()}
    result = await mcp._tools["create_character"].function(character, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/characters", "test_token", character.model_dump())
    assert result["id"] == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_get_character(mock_forward_request, mock_context):
    mock_forward_request.return_value = {"id": 1, "name": "Test Character", "concept": "A test character"}
    result = await mcp._tools["get_character"].function(1, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("GET", "/characters/1", "test_token")
    assert result["id"] == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_update_character(mock_forward_request, mock_context):
    character = Character(name="Updated Character", concept="An updated concept")
    mock_forward_request.return_value = {"id": 1, **character.model_dump()}
    result = await mcp._tools["update_character"].function(1, character, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("PUT", "/characters/1", "test_token", character.model_dump())
    assert result["name"] == "Updated Character"

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_delete_character(mock_forward_request, mock_context):
    mock_forward_request.return_value = {}
    await mcp._tools["delete_character"].function(1, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("DELETE", "/characters/1", "test_token")

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_link_character_to_campaign(mock_forward_request, mock_context):
    link = LinkCharacter(campaign_id=1, character_id=1)
    mock_forward_request.return_value = {}
    await mcp._tools["link_character_to_campaign"].function(link, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/characters/link", "test_token", link.model_dump())

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_unlink_character_from_campaign(mock_forward_request, mock_context):
    link = LinkCharacter(campaign_id=1, character_id=1)
    mock_forward_request.return_value = {}
    await mcp._tools["unlink_character_from_campaign"].function(link, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/characters/unlink", "test_token", link.model_dump())

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_create_campaign_section(mock_forward_request, mock_context):
    section = CampaignSection(title="Test Section", content="A test section", campaign_id=1)
    mock_forward_request.return_value = {"id": 1, **section.model_dump()}
    result = await mcp._tools["create_campaign_section"].function(section, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/campaign-sections", "test_token", section.model_dump())
    assert result["id"] == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_list_campaign_sections(mock_forward_request, mock_context):
    mock_forward_request.return_value = [{"id": 1, "title": "Test Section", "content": "A test section", "campaign_id": 1}]
    result = await mcp._tools["list_campaign_sections"].function(1, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("GET", "/campaign-sections/campaign/1", "test_token")
    assert len(result) == 1

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_update_campaign_section(mock_forward_request, mock_context):
    section = CampaignSection(title="Updated Section", content="An updated section", campaign_id=1)
    mock_forward_request.return_value = {"id": 1, **section.model_dump()}
    result = await mcp._tools["update_campaign_section"].function(1, section, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("PUT", "/campaign-sections/1", "test_token", section.model_dump())
    assert result["title"] == "Updated Section"

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_delete_campaign_section(mock_forward_request, mock_context):
    mock_forward_request.return_value = {}
    await mcp._tools["delete_campaign_section"].function(1, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("DELETE", "/campaign-sections/1", "test_token")

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_generate_toc(mock_forward_request, mock_context):
    toc_request = GenerateToc(campaign_id=1)
    mock_forward_request.return_value = {"toc": "Table of Contents"}
    result = await mcp._tools["generate_toc"].function(toc_request, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/campaigns/generate-toc", "test_token", toc_request.model_dump())
    assert "toc" in result

@pytest.mark.asyncio
@patch("mcp_server.main_rpc.forward_request")
async def test_generate_titles(mock_forward_request, mock_context):
    title_request = GenerateTitles(campaign_id=1, section_id=1)
    mock_forward_request.return_value = {"titles": ["Title 1", "Title 2"]}
    result = await mcp._tools["generate_titles"].function(title_request, "test_token", mock_context)
    mock_forward_request.assert_called_once_with("POST", "/campaigns/generate-titles", "test_token", title_request.model_dump())
    assert "titles" in result
