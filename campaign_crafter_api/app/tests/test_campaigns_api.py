import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient # Not used in this file directly, but common
from fastapi import HTTPException # For error case testing
from unittest.mock import patch, AsyncMock, ANY, MagicMock
from io import BytesIO
import builtins # For patching print

from app.main import app
from app.core.config import settings # For AZURE_STORAGE_CONTAINER_NAME
from app.db import Base, get_db
from app.orm_models import Campaign as ORMCampaign, CampaignSection as ORMCampaignSection
from app import crud
from app import models as pydantic_models
from app.models import Campaign as PydanticCampaign
from app.services.openai_service import OpenAILLMService # To allow its direct instantiation if needed, or to patch its methods


# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_list_campaigns_empty_db():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/campaigns/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_campaigns_with_data():
    db = TestingSessionLocal()
    test_campaign = ORMCampaign(title="Test Campaign 1", owner_id=1)
    db.add(test_campaign)
    db.commit()
    db.refresh(test_campaign)
    campaign_id = test_campaign.id
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/campaigns/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    ret_campaign = response_data[0]
    assert ret_campaign["title"] == "Test Campaign 1"
    assert ret_campaign["id"] == campaign_id
    assert "initial_user_prompt" in ret_campaign
    assert "concept" in ret_campaign
    assert "display_toc" in ret_campaign
    assert "homebrewery_toc" in ret_campaign
    assert "homebrewery_export" in ret_campaign

@pytest.mark.asyncio
async def test_create_campaign_full_data():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "My Super Campaign",
            "initial_user_prompt": "A world of dragons and magic.",
            "model_id_with_prefix_for_concept": "openai/gpt-3.5-turbo"
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "My Super Campaign"
    assert data["initial_user_prompt"] == "A world of dragons and magic."
    assert "id" in data
    assert "owner_id" in data
    assert "concept" in data
    assert data["display_toc"] is None
    assert data["homebrewery_toc"] is None
    assert data["homebrewery_export"] is None

@pytest.mark.asyncio
async def test_create_campaign_no_model_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "Simple Adventure",
            "initial_user_prompt": "A quiet village with a dark secret."
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Simple Adventure"
    assert data["initial_user_prompt"] == "A quiet village with a dark secret."
    assert "id" in data
    assert "owner_id" in data
    assert "concept" in data
    assert data["display_toc"] is None
    assert data["homebrewery_toc"] is None
    assert data["homebrewery_export"] is None

@pytest.mark.asyncio
async def test_create_campaign_only_title():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = { "title": "The Lone Artifact" }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "The Lone Artifact"
    assert data["initial_user_prompt"] is None
    assert "id" in data
    assert "owner_id" in data
    assert data["concept"] is None
    assert data["display_toc"] is None
    assert data["homebrewery_toc"] is None
    assert data["homebrewery_export"] is None

@pytest.fixture
def db_campaign(create_test_tables) -> ORMCampaign:
    db = TestingSessionLocal()
    campaign = ORMCampaign(title="API Test Campaign", owner_id=1, concept="A concept for testing APIs.")
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    db.close()
    return campaign

@pytest.fixture
def db_section(db_campaign: ORMCampaign) -> ORMCampaignSection:
    db = TestingSessionLocal()
    section = ORMCampaignSection(
        title="Test Section for API", content="Initial content", order=0,
        campaign_id=db_campaign.id, type="initial_type"
    )
    db.add(section); db.commit(); db.refresh(section); db.close()
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
        json={"model_id_with_prefix": "test_provider/test_model"},
        params={"count": 3}
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"titles": expected_titles}
    mock_get_llm_service.assert_called_once_with(provider_name="test_provider", model_id_with_prefix="test_provider/test_model")
    mock_llm_instance.generate_titles.assert_called_once_with(
        campaign_concept=db_campaign.concept, db=ANY, current_user=ANY, count=3, model="test_model"
    )

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_toc')
async def test_generate_campaign_toc_endpoint_new_format(
    mock_crud_update_toc, mock_get_llm_service, db_campaign: ORMCampaign, async_client: AsyncClient
):
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_toc = AsyncMock(return_value={
        "display_toc": "- Title 1\n- Title 2", "homebrewery_toc": "* HB Title 1"
    })
    mock_get_llm_service.return_value = mock_llm_instance

    updated_campaign_mock = MagicMock(spec=ORMCampaign)
    updated_campaign_mock.id = db_campaign.id; updated_campaign_mock.title = db_campaign.title
    updated_campaign_mock.concept = db_campaign.concept; updated_campaign_mock.initial_user_prompt = db_campaign.initial_user_prompt
    updated_campaign_mock.owner_id = db_campaign.owner_id; updated_campaign_mock.mood_board_image_urls = db_campaign.mood_board_image_urls
    updated_campaign_mock.homebrewery_export = db_campaign.homebrewery_export
    expected_display_toc_structure = [{"title": "Title 1", "type": "unknown"}, {"title": "Title 2", "type": "unknown"}]
    expected_hb_toc_structure = [{"title": "HB Title 1", "type": "unknown"}]
    updated_campaign_mock.display_toc = expected_display_toc_structure
    updated_campaign_mock.homebrewery_toc = expected_hb_toc_structure
    mock_crud_update_toc.return_value = updated_campaign_mock

    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/toc",
        json={"prompt": "Unused prompt", "model_id_with_prefix": "test/model"}
    )
    assert response.status_code == 200, response.text
    mock_crud_update_toc.assert_called_once()
    call_args = mock_crud_update_toc.call_args
    assert call_args.kwargs['campaign_id'] == db_campaign.id
    assert call_args.kwargs['display_toc_content'] == expected_display_toc_structure
    assert call_args.kwargs['homebrewery_toc_content'] == expected_hb_toc_structure
    data = response.json()
    assert data["id"] == db_campaign.id
    assert data["display_toc"] == expected_display_toc_structure
    assert data["homebrewery_toc"] == expected_hb_toc_structure

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_toc')
async def test_generate_campaign_toc_success(
    mock_crud_update_toc: MagicMock, mock_get_llm_service: MagicMock,
    db_campaign: ORMCampaign, async_client: AsyncClient
):
    mock_llm_instance = AsyncMock()
    generated_display_toc_str = "- Display TOC Item 1\n  - Sub Item 1.1\n- Display TOC Item 2"
    generated_hb_toc_str = "- ### [HB TOC Item 1{{PAGENUM}}](#pPAGENUM)\n  - #### [HB Sub Item 1.1{{PAGENUM}}](#pPAGENUM)"
    mock_llm_instance.generate_toc = AsyncMock(return_value={
        "display_toc": generated_display_toc_str, "homebrewery_toc": generated_hb_toc_str
    })
    mock_get_llm_service.return_value = mock_llm_instance

    expected_api_display_toc = [
        {"title": "Display TOC Item 1", "type": "unknown"},
        {"title": "Sub Item 1.1", "type": "unknown"},
        {"title": "Display TOC Item 2", "type": "unknown"}
    ]
    expected_api_hb_toc = [
        {"title": "HB TOC Item 1", "type": "unknown"},
        {"title": "HB Sub Item 1.1", "type": "unknown"}
    ]
    mock_updated_campaign_orm = MagicMock(spec=ORMCampaign)
    mock_updated_campaign_orm.id = db_campaign.id; mock_updated_campaign_orm.title = db_campaign.title
    mock_updated_campaign_orm.concept = db_campaign.concept; mock_updated_campaign_orm.initial_user_prompt = db_campaign.initial_user_prompt
    mock_updated_campaign_orm.owner_id = db_campaign.owner_id; mock_updated_campaign_orm.mood_board_image_urls = db_campaign.mood_board_image_urls
    mock_updated_campaign_orm.homebrewery_export = "Existing export or None"
    mock_updated_campaign_orm.display_toc = expected_api_display_toc
    mock_updated_campaign_orm.homebrewery_toc = expected_api_hb_toc
    mock_crud_update_toc.return_value = mock_updated_campaign_orm

    request_payload = {"model_id_with_prefix": "test_provider/test_model"}
    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/toc", json=request_payload)

    assert response.status_code == 200, response.text
    response_data = response.json()
    mock_get_llm_service.assert_called_once_with(provider_name="test_provider", model_id_with_prefix="test_provider/test_model")
    mock_llm_instance.generate_toc.assert_called_once_with(
        campaign_concept=db_campaign.concept, db=ANY, current_user=ANY, model="test_model"
    )
    mock_crud_update_toc.assert_called_once_with(
        db=ANY, campaign_id=db_campaign.id,
        display_toc_content=expected_api_display_toc, homebrewery_toc_content=expected_api_hb_toc
    )
    assert "display_toc" in response_data; assert "homebrewery_toc" in response_data
    validated_campaign_response = PydanticCampaign.model_validate(response_data)
    assert validated_campaign_response.display_toc == expected_api_display_toc
    assert validated_campaign_response.homebrewery_toc == expected_api_hb_toc
    assert len(validated_campaign_response.display_toc) > 0
    assert len(validated_campaign_response.homebrewery_toc) > 0

@pytest.mark.asyncio
@pytest.mark.parametrize("hb_concept_prompt_scenario", ["prompt_not_found", "prompt_key_error"])
@patch("app.services.openai_service.OpenAILLMService._perform_chat_completion", new_callable=AsyncMock)
@patch("app.services.feature_prompt_service.FeaturePromptService.get_prompt")
@patch("app.api.endpoints.campaigns.crud.update_campaign_toc")
@patch("builtins.print") # To capture warning print statements
async def test_generate_campaign_toc_handles_hb_prompt_issues(
    mock_print: MagicMock,
    mock_crud_update_toc: MagicMock,
    mock_get_feature_prompt: MagicMock,
    mock_perform_chat_completion: AsyncMock,
    hb_concept_prompt_scenario: str,
    db_campaign: ORMCampaign,
    async_client: AsyncClient,
):
    # --- Arrange ---
    # Mock FeaturePromptService.get_prompt behavior based on scenario
    def get_prompt_side_effect(prompt_name: str, db: ANY):
        if prompt_name == "TOC Display":
            return "Generate Display TOC for {campaign_concept}"
        elif prompt_name == "TOC Homebrewery Concept":
            if hb_concept_prompt_scenario == "prompt_not_found":
                return None
            elif hb_concept_prompt_scenario == "prompt_key_error":
                return "Malformed prompt {campaign_concept} and {sections_summary}" # sections_summary will cause KeyError
        return f"Default prompt for {prompt_name}" # Should not be called for these
    mock_get_feature_prompt.side_effect = get_prompt_side_effect

    # Mock LLM's _perform_chat_completion
    # First call is for Display TOC, second (if any) for Homebrewery TOC
    mock_perform_chat_completion.side_effect = [
        AsyncMock(return_value="- Display Item 1\n- Display Item 2"), # For Display TOC
        AsyncMock(return_value="This should not be used if fallback occurs before LLM call for HB") # For Homebrewery TOC (if prompt was found and valid)
    ]

    # Mock crud.update_campaign_toc to return a campaign object
    # The endpoint will set homebrewery_toc to None when calling this if it used the LLM service's fallback string.
    # More accurately, the endpoint currently always sets homebrewery_toc_content=None for update_campaign_toc.
    # So the returned campaign from CRUD will likely have homebrewery_toc as None or its previous DB state.
    mock_updated_campaign_orm = MagicMock(spec=ORMCampaign)
    mock_updated_campaign_orm.id = db_campaign.id; mock_updated_campaign_orm.title = db_campaign.title
    mock_updated_campaign_orm.concept = db_campaign.concept; mock_updated_campaign_orm.initial_user_prompt = db_campaign.initial_user_prompt
    mock_updated_campaign_orm.owner_id = db_campaign.owner_id; mock_updated_campaign_orm.mood_board_image_urls = []
    mock_updated_campaign_orm.homebrewery_export = None

    expected_display_toc_structure = [{"title": "Display Item 1", "type": "unknown"}, {"title": "Display Item 2", "type": "unknown"}]
    mock_updated_campaign_orm.display_toc = expected_display_toc_structure
    # Since endpoint calls crud.update_campaign_toc with homebrewery_toc_content=None,
    # the returned campaign's homebrewery_toc will be None (or its state before update if not cleared by None).
    mock_updated_campaign_orm.homebrewery_toc = None
    mock_crud_update_toc.return_value = mock_updated_campaign_orm

    # --- Act ---
    # Use a specific provider to ensure we are testing the patched OpenAILLMService's behavior
    request_payload = {"model_id_with_prefix": "openai/gpt-3.5-turbo"}
    # This patch makes get_llm_service return a real OpenAILLMService,
    # whose _perform_chat_completion is mocked, and whose FeaturePromptService uses the globally mocked get_prompt.
    with patch("app.api.endpoints.campaigns.get_llm_service", return_value=OpenAILLMService()):
        response = await async_client.post(
            f"/api/v1/campaigns/{db_campaign.id}/toc",
            json=request_payload
        )

    # --- Assert ---
    assert response.status_code == 200, f"Endpoint failed with scenario: {hb_concept_prompt_scenario}, details: {response.text}"

    # Verify Display TOC was generated and processed
    mock_crud_update_toc.assert_called_once()
    update_call_args = mock_crud_update_toc.call_args.kwargs
    assert update_call_args['display_toc_content'] == expected_display_toc_structure
    # Endpoint currently passes homebrewery_toc_content=None to crud.update_campaign_toc
    assert update_call_args['homebrewery_toc_content'] is None

    # Check that a warning was printed by the LLM service
    warning_found = False
    for call in mock_print.call_args_list:
        args, _ = call
        if args and "WARNING:" in args[0]:
            if hb_concept_prompt_scenario == "prompt_not_found" and "'TOC Homebrewery Concept' prompt not found" in args[0]:
                warning_found = True; break
            if hb_concept_prompt_scenario == "prompt_key_error" and "formatting 'TOC Homebrewery Concept' prompt failed due to KeyError" in args[0]:
                warning_found = True; break
    assert warning_found, f"Expected warning not printed for scenario: {hb_concept_prompt_scenario}"

    # Check response structure (homebrewery_toc should be None as per current endpoint logic)
    response_data = response.json()
    validated_response = PydanticCampaign.model_validate(response_data)
    assert validated_response.display_toc == expected_display_toc_structure
    assert validated_response.homebrewery_toc is None


@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content')
async def test_seed_sections_from_toc_endpoint_uses_type(
    mock_crud_create_section, mock_get_llm_service, db_campaign: ORMCampaign, async_client: AsyncClient
):
    db = TestingSessionLocal()
    toc_data = [
        {"title": "NPC Alpha", "type": "npc"}, {"title": "Generic Chapter", "type": "generic"},
        {"title": "Location Beta", "type": "Location"}
    ]
    db_campaign_instance = db.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    db_campaign_instance.display_toc = toc_data; db_campaign_instance.homebrewery_toc = []
    db.commit(); db.refresh(db_campaign_instance); db.close()

    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Generated content")
    mock_get_llm_service.return_value = mock_llm_instance

    def mock_create_section_side_effect(db, campaign_id, title, order, placeholder_content, type):
        mock_section = MagicMock(spec=ORMCampaignSection)
        mock_section.id = order + 1; mock_section.title = title; mock_section.content = placeholder_content
        mock_section.order = order; mock_section.campaign_id = campaign_id; mock_section.type = type
        mock_section.user_prompt = None; mock_section.llm_prompt = None; mock_section.llm_response = None
        mock_section.word_count = len(placeholder_content.split()) if placeholder_content else 0
        mock_section.images = []; mock_section.created_at = db_campaign.created_at; mock_section.updated_at = db_campaign.updated_at
        return mock_section
    mock_crud_create_section.side_effect = mock_create_section_side_effect

    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/seed_sections_from_toc?auto_populate=true&model_id_with_prefix=test_provider/test_model")
    async for _ in response.aiter_lines(): pass
    assert response.status_code == 200
    assert mock_crud_create_section.call_count == 3
    assert mock_crud_create_section.call_args_list[0].kwargs['type'] == "npc"
    assert mock_crud_create_section.call_args_list[1].kwargs['type'] == "generic"
    assert mock_crud_create_section.call_args_list[2].kwargs['type'] == "Location"
    assert mock_llm_instance.generate_section_content.call_count == 3
    assert mock_llm_instance.generate_section_content.call_args_list[0].kwargs['section_type'] == "npc"
    assert mock_llm_instance.generate_section_content.call_args_list[1].kwargs['section_type'] == "generic"
    assert mock_llm_instance.generate_section_content.call_args_list[2].kwargs['section_type'] == "Location"

@pytest.mark.asyncio
async def test_get_campaign_full_content_formats_new_toc(db_campaign: ORMCampaign, async_client: AsyncClient):
    db = TestingSessionLocal()
    toc_data = [{"title": "Entry 1", "type": "chapter"}, {"title": "Entry 2", "type": "location"}]
    db_campaign_instance = db.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    db_campaign_instance.display_toc = toc_data; db_campaign_instance.homebrewery_toc = []
    db.commit(); db.refresh(db_campaign_instance); db.close()

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

    mock_created_section = MagicMock(spec=ORMCampaignSection)
    mock_created_section.id = 1; mock_created_section.campaign_id = db_campaign.id
    mock_created_section.title = "New Section with Type"; mock_created_section.content = "Generated test content."
    mock_created_section.order = 0; mock_created_section.type = "custom_type"
    mock_created_section.user_prompt = "A detailed prompt."; mock_created_section.llm_prompt = "Actual LLM prompt."
    mock_created_section.llm_response = "Generated test content."; mock_created_section.word_count = len("Generated test content.".split())
    mock_created_section.images = []; mock_created_section.created_at = db_campaign.created_at; mock_created_section.updated_at = db_campaign.updated_at
    mock_crud_create_section.return_value = mock_created_section

    section_payload = {
        "title": "New Section with Type", "prompt": "A detailed prompt.",
        "type": "custom_type", "model_id_with_prefix": "test/model"
    }
    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/sections", json=section_payload)
    assert response.status_code == 200, response.text
    mock_crud_create_section.assert_called_once()
    assert mock_crud_create_section.call_args.kwargs['section_type'] == "custom_type"
    mock_llm_instance.generate_section_content.assert_called_once()
    assert mock_llm_instance.generate_section_content.call_args.kwargs['section_type'] == "custom_type"
    response_data = response.json()
    assert response_data["title"] == "New Section with Type"; assert response_data["content"] == "Generated test content."; assert response_data["type"] == "custom_type"

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_section')
async def test_regenerate_campaign_section_endpoint_uses_type(
    mock_crud_update_section, mock_get_llm_service, db_section: ORMCampaignSection, async_client: AsyncClient
):
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Regenerated content.")
    mock_get_llm_service.return_value = mock_llm_instance

    def update_side_effect(db, section_id, campaign_id, section_update_data: pydantic_models.CampaignSectionUpdate):
        updated_section_mock = MagicMock(spec=ORMCampaignSection)
        updated_section_mock.id = db_section.id; updated_section_mock.campaign_id = db_section.campaign_id
        updated_section_mock.title = section_update_data.title if section_update_data.title is not None else db_section.title
        updated_section_mock.content = section_update_data.content if section_update_data.content is not None else db_section.content
        updated_section_mock.order = db_section.order
        updated_section_mock.type = section_update_data.type if section_update_data.type is not None else db_section.type
        updated_section_mock.user_prompt = section_update_data.user_prompt if section_update_data.user_prompt is not None else db_section.user_prompt
        updated_section_mock.llm_prompt = section_update_data.llm_prompt if section_update_data.llm_prompt is not None else db_section.llm_prompt
        updated_section_mock.llm_response = section_update_data.llm_response if section_update_data.llm_response is not None else db_section.llm_response
        updated_section_mock.word_count = len(updated_section_mock.content.split()) if updated_section_mock.content else 0
        updated_section_mock.images = db_section.images; updated_section_mock.created_at = db_section.created_at
        updated_section_mock.updated_at = db_section.updated_at
        if section_update_data.type is not None: db_section.type = section_update_data.type
        return updated_section_mock
    mock_crud_update_section.side_effect = update_side_effect

    campaign_id = db_section.campaign_id
    regenerate_payload_with_type = {
        "section_type": "new_type_from_payload", "new_prompt": "A new prompt.",
        "model_id_with_prefix": "test_provider/test_model"
    }
    response1 = await async_client.post(
        f"/api/v1/campaigns/{campaign_id}/sections/{db_section.id}/regenerate", json=regenerate_payload_with_type
    )
    assert response1.status_code == 200, response1.text
    mock_llm_instance.generate_section_content.assert_called_with(
        campaign_concept=ANY, db=ANY, existing_sections_summary=ANY, section_creation_prompt=ANY,
        section_title_suggestion=ANY, model="test_model", section_type="new_type_from_payload", current_user=ANY
    )
    assert mock_crud_update_section.call_args.kwargs['section_update_data'].type == "new_type_from_payload"
    assert response1.json()["type"] == "new_type_from_payload"

    mock_llm_instance.generate_section_content.reset_mock(); mock_crud_update_section.reset_mock()
    current_section_type_in_db = "new_type_from_payload"
    regenerate_payload_no_type = { "new_prompt": "Another new prompt.", "model_id_with_prefix": "another_provider/another_model" }
    response2 = await async_client.post(
        f"/api/v1/campaigns/{campaign_id}/sections/{db_section.id}/regenerate", json=regenerate_payload_no_type
    )
    assert response2.status_code == 200, response2.text
    assert mock_llm_instance.generate_section_content.call_args.kwargs['section_type'] == current_section_type_in_db
    assert mock_llm_instance.generate_section_content.call_args.kwargs['model'] == "another_model"
    assert mock_crud_update_section.call_args.kwargs['section_update_data'].type is None
    assert response2.json()["type"] == current_section_type_in_db

@pytest.mark.asyncio
@patch('app.crud.ImageGenerationService.delete_image_from_blob_storage', new_callable=AsyncMock)
async def test_update_campaign_remove_moodboard_image_deletes_blob(
    mock_delete_blob, db_campaign: ORMCampaign, async_client: AsyncClient
):
    initial_url1 = f"https://mockaccount.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER_NAME}/blob1.png"
    initial_url2 = f"https://mockaccount.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER_NAME}/blob2.jpg"
    db = TestingSessionLocal()
    try:
        campaign_to_update = db.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
        if not campaign_to_update: pytest.fail(f"Campaign with ID {db_campaign.id} not found.")
        campaign_to_update.mood_board_image_urls = [initial_url1, initial_url2]; db.commit()
    finally: db.close()
    update_payload = { "mood_board_image_urls": [initial_url1] }
    response = await async_client.put( f"/api/v1/campaigns/{db_campaign.id}", json=update_payload )
    assert response.status_code == 200, response.text
    mock_delete_blob.assert_called_once_with("blob2.jpg")
    db = TestingSessionLocal()
    try:
        updated_db_campaign = db.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
        assert updated_db_campaign.mood_board_image_urls == [initial_url1]
    finally: db.close()

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.ImageGenerationService._save_image_and_log_db', new_callable=AsyncMock)
async def test_upload_moodboard_image_success(
    mock_save_image, db_campaign: ORMCampaign, async_client: AsyncClient
):
    mock_image_url = "http://example.com/mock_uploaded_image.png"
    mock_save_image.return_value = mock_image_url
    image_content = b"fake image data"; image_bytes_io = BytesIO(image_content); file_name = "test_image.png"
    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/moodboard/upload",
        files={"file": (file_name, image_bytes_io, "image/png")}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["image_url"] == mock_image_url; assert data["campaign"]["id"] == db_campaign.id
    assert mock_image_url in data["campaign"]["mood_board_image_urls"]
    mock_save_image.assert_called_once()
    assert mock_save_image.call_args[1]['image_bytes'] == image_content
    assert mock_save_image.call_args[1]['user_id'] == db_campaign.owner_id
    assert mock_save_image.call_args[1]['original_filename_from_api'] == file_name
    db = TestingSessionLocal()
    try:
        updated_db_campaign = db.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
        assert mock_image_url in updated_db_campaign.mood_board_image_urls
    finally: db.close()

@pytest.mark.asyncio
async def test_upload_moodboard_image_campaign_not_found(async_client: AsyncClient):
    image_bytes_io = BytesIO(b"fake image data")
    response = await async_client.post(
        "/api/v1/campaigns/99999/moodboard/upload",
        files={"file": ("test.png", image_bytes_io, "image/png")}
    )
    assert response.status_code == 404; assert response.json()["detail"] == "Campaign not found"

@pytest.mark.asyncio
async def test_upload_moodboard_image_unauthorized(db_campaign: ORMCampaign, async_client: AsyncClient):
    db = TestingSessionLocal()
    try:
        other_user_campaign = ORMCampaign(title="Other User Campaign", owner_id=2)
        db.add(other_user_campaign); db.commit(); db.refresh(other_user_campaign)
        other_campaign_id = other_user_campaign.id
    finally: db.close()
    image_bytes_io = BytesIO(b"fake image data")
    response = await async_client.post(
        f"/api/v1/campaigns/{other_campaign_id}/moodboard/upload",
        files={"file": ("test.png", image_bytes_io, "image/png")}
    )
    assert response.status_code == 403; assert response.json()["detail"] == "Not authorized to upload images to this campaign"

@pytest.mark.asyncio
async def test_upload_moodboard_image_no_file(db_campaign: ORMCampaign, async_client: AsyncClient):
    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/moodboard/upload")
    assert response.status_code == 422

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.ImageGenerationService._save_image_and_log_db', new_callable=AsyncMock)
async def test_upload_moodboard_image_service_failure(
    mock_save_image, db_campaign: ORMCampaign, async_client: AsyncClient
):
    mock_save_image.side_effect = HTTPException(status_code=500, detail="Azure upload failed")
    initial_moodboard_urls = list(db_campaign.mood_board_image_urls or [])
    image_bytes_io = BytesIO(b"fake image data")
    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/moodboard/upload",
        files={"file": ("test.png", image_bytes_io, "image/png")}
    )
    assert response.status_code == 500; assert response.json()["detail"] == "Azure upload failed"
    db = TestingSessionLocal()
    try:
        unchanged_db_campaign = db.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
        assert list(unchanged_db_campaign.mood_board_image_urls or []) == initial_moodboard_urls
    finally: db.close()
