import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, ANY, MagicMock


from app.main import app
from app.db import Base, get_db
from app.orm_models import Campaign as ORMCampaign, CampaignSection as ORMCampaignSection # Renamed Campaign to ORMCampaign
from app import crud # Import crud to mock its functions
from app import models as pydantic_models # For request/response validation if needed


# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
# DATABASE_URL = "sqlite:///./test.db" # Alternative: use a file-based test DB

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Pytest fixture to create tables for each test function
@pytest.fixture(autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_list_campaigns_empty_db():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/campaigns/") # Adjusted path
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_campaigns_with_data():
    # Add a campaign to the test database
    db = TestingSessionLocal()
    # For Campaign ORM model, ensure all required fields from the latest models.py are present
    # Based on previous steps, Campaign ORM model has: id, title, initial_user_prompt, concept, toc, homebrewery_export, owner_id
    # The test Campaign model used here for setup might need to be updated if it causes issues with the actual ORM model.
    # For now, assuming title and owner_id are sufficient for pre-populating,
    # and other fields are nullable or have defaults.
    test_campaign = Campaign(title="Test Campaign 1", owner_id=1) # owner_id is placeholder
    db.add(test_campaign)
    db.commit()
    db.refresh(test_campaign)
    campaign_id = test_campaign.id # Get the id for the path
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/campaigns/") # Adjusted path

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    ret_campaign = response_data[0]
    assert ret_campaign["title"] == "Test Campaign 1"
    assert ret_campaign["id"] == campaign_id
    # Asserting based on the Campaign model from models.py which includes these fields
    assert "initial_user_prompt" in ret_campaign
    assert "concept" in ret_campaign
    # Updated field names
    assert "display_toc" in ret_campaign
    assert "homebrewery_toc" in ret_campaign
    assert "homebrewery_export" in ret_campaign

@pytest.mark.asyncio
async def test_create_campaign_full_data():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "My Super Campaign",
            "initial_user_prompt": "A world of dragons and magic.",
            "model_id_with_prefix_for_concept": "openai/gpt-3.5-turbo" # Example model
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text # Include response text on failure
    data = response.json()
    assert data["title"] == "My Super Campaign"
    assert data["initial_user_prompt"] == "A world of dragons and magic."
    assert "id" in data
    assert "owner_id" in data # Default owner_id = 1 from endpoint
    assert "concept" in data # Can be None or str
    # Updated field names
    assert data["display_toc"] is None
    assert data["homebrewery_toc"] is None
    assert data["homebrewery_export"] is None # Should be None initially
    # If LLMs are not actually called in test env, concept might be None.
    # If concept generation is mocked, assert specific mock output.

@pytest.mark.asyncio
async def test_create_campaign_no_model_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "Simple Adventure",
            "initial_user_prompt": "A quiet village with a dark secret."
            # model_id_with_prefix_for_concept is omitted
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Simple Adventure"
    assert data["initial_user_prompt"] == "A quiet village with a dark secret."
    assert "id" in data
    assert "owner_id" in data
    assert "concept" in data # Concept generation might be attempted with a default model or skipped
    # Updated field names
    assert data["display_toc"] is None
    assert data["homebrewery_toc"] is None
    assert data["homebrewery_export"] is None

@pytest.mark.asyncio
async def test_create_campaign_only_title():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "The Lone Artifact"
            # initial_user_prompt is omitted
            # model_id_with_prefix_for_concept is omitted
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "The Lone Artifact"
    assert data["initial_user_prompt"] is None
    assert "id" in data
    assert "owner_id" in data
    # Concept should be None as no prompt was provided for generation
    assert data["concept"] is None
    # Updated field names
    assert data["display_toc"] is None
    assert data["homebrewery_toc"] is None
    assert data["homebrewery_export"] is None

# Helper fixture to create a campaign directly in DB for API tests
@pytest.fixture
def db_campaign(create_test_tables) -> ORMCampaign: # Depends on create_test_tables to ensure tables exist
    db = TestingSessionLocal()
    campaign = ORMCampaign(title="API Test Campaign", owner_id=1, concept="A concept for testing APIs.")
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    db.close()
    return campaign

# Helper fixture to create a section directly in DB for API tests
@pytest.fixture
def db_section(db_campaign: ORMCampaign) -> ORMCampaignSection:
    db = TestingSessionLocal()
    section = ORMCampaignSection(
        title="Test Section for API",
        content="Initial content",
        order=0,
        campaign_id=db_campaign.id,
        type="initial_type"
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    db.close()
    return section


@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
async def test_generate_campaign_titles_success(mock_get_llm_service, db_campaign: ORMCampaign, async_client: AsyncClient):
    mock_llm_instance = AsyncMock()
    expected_titles = ["Title 1", "Awesome Title 2", "The Third Title"]
    mock_llm_instance.generate_titles = AsyncMock(return_value=expected_titles)
    mock_get_llm_service.return_value = mock_llm_instance

    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/titles",
        json={"model_id_with_prefix": "test_provider/test_model"}, # prompt is not used by this endpoint
        params={"count": 3}
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"titles": expected_titles}
    mock_get_llm_service.assert_called_once_with(provider_name="test_provider", model_id_with_prefix="test_provider/test_model")
    mock_llm_instance.generate_titles.assert_called_once_with(
        campaign_concept=db_campaign.concept,
        db=ANY,
        count=3,
        model="test_model"
    )

# --- New Tests for TOC and Section Type ---

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_toc')
async def test_generate_campaign_toc_endpoint_new_format(
    mock_crud_update_toc, mock_get_llm_service, db_campaign: ORMCampaign, async_client: AsyncClient
):
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_toc = AsyncMock(return_value={
        "display_toc": "- Title 1\n- Title 2",
        "homebrewery_toc": "* HB Title 1"
    })
    mock_get_llm_service.return_value = mock_llm_instance

    # Mock crud.update_campaign_toc to return a campaign-like object (or the campaign itself)
    # The actual ORMCampaign object might be complex to construct here fully,
    # so we mock its return to be a simplified version or the input campaign if appropriate.
    # For this test, we mostly care that it was called correctly.
    mock_crud_update_toc.return_value = db_campaign # Simulate it returns the updated campaign

    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/toc",
        json={"prompt": "Unused prompt", "model_id_with_prefix": "test/model"} # Prompt is unused by endpoint
    )

    assert response.status_code == 200, response.text
    data = response.json()

    expected_display_toc = [{"title": "Title 1", "type": "unknown"}, {"title": "Title 2", "type": "unknown"}]
    expected_hb_toc = [{"title": "HB Title 1", "type": "unknown"}]

    # The response from the endpoint IS the campaign object from crud.update_campaign_toc
    # If that mock returns db_campaign, and db_campaign itself wasn't updated with these lists,
    # this assertion might fail on data["display_toc"].
    # For this to pass, mock_crud_update_toc should return a campaign with these lists.
    # A simpler way is to check the call to mock_crud_update_toc.

    # Instead of checking response.json() for the TOC content (which depends on mock_crud_update_toc's return value),
    # we check if crud.update_campaign_toc was called with the correctly transformed lists.
    mock_crud_update_toc.assert_called_once()
    call_args = mock_crud_update_toc.call_args
    assert call_args.kwargs['campaign_id'] == db_campaign.id
    assert call_args.kwargs['display_toc_content'] == expected_display_toc
    assert call_args.kwargs['homebrewery_toc_content'] == expected_hb_toc

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content')
async def test_seed_sections_from_toc_endpoint_uses_type(
    mock_crud_create_section, mock_get_llm_service, db_campaign: ORMCampaign, async_client: AsyncClient
):
    db = TestingSessionLocal()
    toc_data = [
        {"title": "NPC Alpha", "type": "npc"},
        {"title": "Generic Chapter", "type": "generic"},
        {"title": "Location Beta", "type": "Location"} # Test case-insensitivity for type refinement
    ]
    crud.update_campaign_toc(db, db_campaign.id, toc_data, []) # Set display_toc
    db.close()

    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Generated content")
    mock_get_llm_service.return_value = mock_llm_instance

    # Mock for crud.create_section_with_placeholder_content
    # It needs to return an ORMCampaignSection compatible object for from_orm
    def mock_create_section_side_effect(db, campaign_id, title, order, placeholder_content, type):
        mock_section = MagicMock(spec=ORMCampaignSection)
        mock_section.id = order + 1 # Ensure unique ID for key
        mock_section.title = title
        mock_section.content = placeholder_content
        mock_section.order = order
        mock_section.campaign_id = campaign_id
        mock_section.type = type
        return mock_section
    mock_crud_create_section.side_effect = mock_create_section_side_effect


    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/seed_sections_from_toc?auto_populate=true")

    # Consume SSE response to ensure all calls are made
    async for line in response.aiter_lines():
        pass # print(line) # For debugging SSE content

    assert response.status_code == 200

    assert mock_crud_create_section.call_count == 3
    # Call 1 for NPC Alpha
    assert mock_crud_create_section.call_args_list[0].kwargs['type'] == "npc"
    assert mock_crud_create_section.call_args_list[0].kwargs['title'] == "NPC Alpha"
    # Call 2 for Generic Chapter
    assert mock_crud_create_section.call_args_list[1].kwargs['type'] == "generic"
    assert mock_crud_create_section.call_args_list[1].kwargs['title'] == "Generic Chapter"
    # Call 3 for Location Beta
    assert mock_crud_create_section.call_args_list[2].kwargs['type'] == "Location" # Preserves case from TOC
    assert mock_crud_create_section.call_args_list[2].kwargs['title'] == "Location Beta"

    assert mock_llm_instance.generate_section_content.call_count == 3
    # LLM call for NPC Alpha
    assert mock_llm_instance.generate_section_content.call_args_list[0].kwargs['section_type'] == "npc"
    # LLM call for Generic Chapter (title "Generic Chapter" implies "Chapter/Quest" if logic is hit)
    assert mock_llm_instance.generate_section_content.call_args_list[1].kwargs['section_type'] == "Chapter/Quest" # type refined by title
    # LLM call for Location Beta (type "Location" is specific enough)
    assert mock_llm_instance.generate_section_content.call_args_list[2].kwargs['section_type'] == "Location"


@pytest.mark.asyncio
async def test_get_campaign_full_content_formats_new_toc(db_campaign: ORMCampaign, async_client: AsyncClient):
    db = TestingSessionLocal()
    toc_data = [{"title": "Entry 1", "type": "chapter"}, {"title": "Entry 2", "type": "location"}]
    crud.update_campaign_toc(db, db_campaign.id, toc_data, [])
    db.close()

    response = await async_client.get(f"/api/v1/campaigns/{db_campaign.id}/full_content")
    assert response.status_code == 200
    data = response.json()
    expected_toc_string = "## Table of Contents\n\n- Entry 1\n- Entry 2\n\n"
    assert expected_toc_string in data["full_content"]

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.create_campaign_section')
async def test_create_new_campaign_section_endpoint_uses_type(
    mock_crud_create_section, mock_get_llm_service, db_campaign: ORMCampaign, async_client: AsyncClient
):
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Generated test content.")
    mock_get_llm_service.return_value = mock_llm_instance

    # Mock crud.create_campaign_section to return a valid CampaignSection object
    mock_created_section = ORMCampaignSection(id=1, campaign_id=db_campaign.id, title="Test Section", content="Generated test content.", order=0, type="custom_type")
    mock_crud_create_section.return_value = mock_created_section

    section_payload = {
        "title": "New Section with Type",
        "prompt": "A detailed prompt.",
        "type": "custom_type",
        "model_id_with_prefix": "test/model"
    }
    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/sections", json=section_payload)

    assert response.status_code == 200, response.text
    mock_crud_create_section.assert_called_once()
    assert mock_crud_create_section.call_args.kwargs['section_type'] == "custom_type"

    mock_llm_instance.generate_section_content.assert_called_once()
    assert mock_llm_instance.generate_section_content.call_args.kwargs['section_type'] == "custom_type"

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_section')
async def test_regenerate_campaign_section_endpoint_uses_type(
    mock_crud_update_section, mock_get_llm_service, db_section: ORMCampaignSection, async_client: AsyncClient
):
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Regenerated content.")
    mock_get_llm_service.return_value = mock_llm_instance

    # Mock crud.update_campaign_section to return the updated section
    # The actual db_section object is fine to return, or a mock with updated attributes
    def update_side_effect(db, section_id, campaign_id, section_update_data):
        # Simulate update
        db_section.content = section_update_data.content
        if section_update_data.title is not None: db_section.title = section_update_data.title
        if section_update_data.type is not None: db_section.type = section_update_data.type
        return db_section
    mock_crud_update_section.side_effect = update_side_effect

    campaign_id = db_section.campaign_id

    # Test 1: Provide section_type in request
    regenerate_payload_with_type = {"section_type": "new_type", "new_prompt": "A new prompt."}
    response1 = await async_client.post(
        f"/api/v1/campaigns/{campaign_id}/sections/{db_section.id}/regenerate",
        json=regenerate_payload_with_type
    )
    assert response1.status_code == 200, response1.text
    mock_llm_instance.generate_section_content.assert_called_with(
        campaign_concept=ANY, db=ANY, existing_sections_summary=ANY,
        section_creation_prompt=ANY, section_title_suggestion=ANY,
        model=ANY, section_type="new_type"
    )
    mock_crud_update_section.assert_called_with(
        db=ANY, section_id=db_section.id, campaign_id=campaign_id,
        section_update_data=ANY
    )
    assert mock_crud_update_section.call_args.kwargs['section_update_data'].type == "new_type"

    # Test 2: Do not provide section_type in request (should use existing or inferred)
    mock_llm_instance.generate_section_content.reset_mock()
    mock_crud_update_section.reset_mock()
    # db_section.type is now "new_type" from the previous call due to side_effect

    regenerate_payload_no_type = {"new_prompt": "Another new prompt."}
    response2 = await async_client.post(
        f"/api/v1/campaigns/{campaign_id}/sections/{db_section.id}/regenerate",
        json=regenerate_payload_no_type
    )
    assert response2.status_code == 200, response2.text
    # Type for LLM should be the existing type of the section ("new_type")
    # because no new type was provided in input, and title keyword inference logic might trigger if it's generic.
    # If db_section.type ("new_type") is not generic, it will be used.
    assert mock_llm_instance.generate_section_content.call_args.kwargs['section_type'] == "new_type"

    # Type should not be in the update data if not specified in input
    assert mock_crud_update_section.call_args.kwargs['section_update_data'].type is None
