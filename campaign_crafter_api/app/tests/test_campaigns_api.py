import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock, ANY, MagicMock
from io import BytesIO

from app.core.config import settings
from app.orm_models import Campaign as ORMCampaign, CampaignSection as ORMCampaignSection, User as ORMUser
from app import crud
from app import models as pydantic_models
from app.models import Campaign as PydanticCampaign, User as PydanticUser, CampaignTitlesResponse, LLMGenerationRequest
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.openai_service import OpenAILLMService
from app.tests.conftest import create_mock_campaign_orm

@pytest.fixture
def db_campaign(db_session: Session, current_active_user_override: PydanticUser) -> ORMCampaign:
    """Create a test campaign in the database"""
    campaign = ORMCampaign(
        title="API Test Campaign",
        owner_id=current_active_user_override.id,
        concept="A concept for testing APIs."
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign

@pytest.fixture
def db_section(db_session: Session, db_campaign: ORMCampaign) -> ORMCampaignSection:
    """Create a test section in the database"""
    section = ORMCampaignSection(
        title="Test Section for API",
        content="Initial content",
        order=0,
        campaign_id=db_campaign.id,
        type="initial_type"
    )
    db_session.add(section)
    db_session.commit()
    db_session.refresh(section)
    return section

@pytest.mark.asyncio
async def test_list_campaigns_empty_db(async_client: AsyncClient, current_active_user_override: PydanticUser):
    response = await async_client.get("/api/v1/campaigns/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_campaigns_with_data(async_client: AsyncClient, db_session: Session, current_active_user_override: PydanticUser):
    test_campaign = ORMCampaign(title="Test Campaign 1", owner_id=current_active_user_override.id)
    db_session.add(test_campaign)
    db_session.commit()
    db_session.refresh(test_campaign)
    campaign_id = test_campaign.id

    response = await async_client.get("/api/v1/campaigns/")

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
async def test_create_campaign_full_data(async_client: AsyncClient, current_active_user_override: PydanticUser):
    payload = {
        "title": "My Super Campaign",
        "initial_user_prompt": "A world of dragons and magic.",
        "model_id_with_prefix_for_concept": "openai/gpt-3.5-turbo"
    }
    response = await async_client.post("/api/v1/campaigns/", json=payload)

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
async def test_create_campaign_no_model_id(async_client: AsyncClient, current_active_user_override: PydanticUser):
    payload = {
        "title": "Simple Adventure",
        "initial_user_prompt": "A quiet village with a dark secret."
    }
    response = await async_client.post("/api/v1/campaigns/", json=payload)

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
async def test_create_campaign_only_title(async_client: AsyncClient, current_active_user_override: PydanticUser):
    payload = { "title": "The Lone Artifact" }
    response = await async_client.post("/api/v1/campaigns/", json=payload)

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

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign')
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
async def test_generate_campaign_titles_success(
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    mock_campaign_id = 1
    mock_user_id = current_active_user_override.id

    # Mock ORM Campaign object
    mock_orm_campaign = MagicMock(spec=ORMCampaign)
    mock_orm_campaign.id = mock_campaign_id
    mock_orm_campaign.owner_id = mock_user_id
    mock_orm_campaign.concept = "Test concept for titles"
    mock_crud_get_campaign.return_value = mock_orm_campaign

    # Mock ORM User object
    mock_orm_user = MagicMock(spec=ORMUser)
    mock_orm_user.id = mock_user_id
    mock_crud_get_user.return_value = mock_orm_user

    # Mock LLM Service
    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    expected_titles = ["Title 1", "Awesome Title 2", "The Third Title"]
    mock_llm_instance.generate_titles = AsyncMock(return_value=expected_titles)
    mock_get_llm_service.return_value = mock_llm_instance

    request_body = LLMGenerationRequest(model_id_with_prefix="openai/gpt-3.5-turbo")

    response = await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_id}/titles",
        json=request_body.model_dump(),
        params={"count": 3}
        # Headers for auth are typically handled by the async_client fixture if auth is part of app setup
        # or by overriding the dependency `get_current_active_user` as done by `current_active_user_override`
    )

    assert response.status_code == 200, response.text
    expected_response = CampaignTitlesResponse(titles=expected_titles)
    assert response.json() == expected_response.model_dump()

    mock_crud_get_campaign.assert_called_once_with(db=ANY, campaign_id=mock_campaign_id)
    mock_crud_get_user.assert_called_once_with(ANY, user_id=mock_user_id)
    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_orm_user,
        provider_name="openai",
        model_id_with_prefix="openai/gpt-3.5-turbo",
        campaign=mock_orm_campaign
    )
    mock_llm_instance.generate_titles.assert_called_once_with(
        campaign_concept=mock_orm_campaign.concept,
        db=ANY,
        current_user=current_active_user_override, # This is the Pydantic User
        count=3,
        model="gpt-3.5-turbo"
    )

# New test: Scenario where request model_id is None, uses campaign.selected_llm_id
@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign')
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
async def test_generate_campaign_titles_uses_campaign_model_when_request_model_none(
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    mock_campaign_id = 2
    mock_user_id = current_active_user_override.id

    mock_orm_campaign = MagicMock(spec=ORMCampaign)
    mock_orm_campaign.id = mock_campaign_id
    mock_orm_campaign.owner_id = mock_user_id
    mock_orm_campaign.concept = "Test concept for titles - campaign model"
    mock_orm_campaign.selected_llm_id = "testprovider/campaign_model" # Campaign specific model
    mock_crud_get_campaign.return_value = mock_orm_campaign

    mock_orm_user = MagicMock(spec=ORMUser)
    mock_orm_user.id = mock_user_id
    mock_crud_get_user.return_value = mock_orm_user

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    expected_titles = ["Campaign Model Title 1", "Campaign Model Title 2"]
    mock_llm_instance.generate_titles = AsyncMock(return_value=expected_titles)
    mock_get_llm_service.return_value = mock_llm_instance

    request_body = LLMGenerationRequest(model_id_with_prefix=None) # No model in request

    await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_id}/titles",
        json=request_body.model_dump(),
        params={"count": 2}
    )

    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_orm_user,
        provider_name=None, # As request model_id_with_prefix is None
        model_id_with_prefix=None,
        campaign=mock_orm_campaign
    )
    # generate_titles should be called with the model part from campaign.selected_llm_id
    mock_llm_instance.generate_titles.assert_called_once_with(
        campaign_concept=mock_orm_campaign.concept,
        db=ANY,
        current_user=current_active_user_override,
        count=2,
        model="campaign_model"
    )

# New test: Scenario where request and campaign model_id are None (system fallback)
@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign')
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
async def test_generate_campaign_titles_system_fallback_when_request_and_campaign_model_none(
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    mock_campaign_id = 3
    mock_user_id = current_active_user_override.id

    mock_orm_campaign = MagicMock(spec=ORMCampaign)
    mock_orm_campaign.id = mock_campaign_id
    mock_orm_campaign.owner_id = mock_user_id
    mock_orm_campaign.concept = "Test concept for titles - system fallback"
    mock_orm_campaign.selected_llm_id = None # No campaign specific model
    mock_crud_get_campaign.return_value = mock_orm_campaign

    mock_orm_user = MagicMock(spec=ORMUser)
    mock_orm_user.id = mock_user_id
    mock_crud_get_user.return_value = mock_orm_user

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    expected_titles = ["System Fallback Title 1"]
    mock_llm_instance.generate_titles = AsyncMock(return_value=expected_titles)
    mock_get_llm_service.return_value = mock_llm_instance

    request_body = LLMGenerationRequest(model_id_with_prefix=None) # No model in request

    await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_id}/titles",
        json=request_body.model_dump(),
        params={"count": 1}
    )

    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_orm_user,
        provider_name=None,
        model_id_with_prefix=None,
        campaign=mock_orm_campaign
    )
    # generate_titles should be called with model=None (service uses its default)
    mock_llm_instance.generate_titles.assert_called_once_with(
        campaign_concept=mock_orm_campaign.concept,
        db=ANY,
        current_user=current_active_user_override,
        count=1,
        model=None
    )

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign')
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_toc')
async def test_generate_campaign_toc_success(
    mock_crud_update_toc: MagicMock,
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser # Use the fixture
):
    mock_campaign_id = 1
    mock_user_id = current_active_user_override.id

    # Mock ORM Campaign object (initial state)
    mock_initial_orm_campaign = MagicMock(spec=ORMCampaign)
    mock_initial_orm_campaign.id = mock_campaign_id
    mock_initial_orm_campaign.owner_id = mock_user_id
    mock_initial_orm_campaign.concept = "Test concept for TOC"
    mock_initial_orm_campaign.title = "Test Campaign Title"
    mock_initial_orm_campaign.initial_user_prompt = "Initial prompt"
    mock_initial_orm_campaign.mood_board_image_urls = []
    mock_initial_orm_campaign.homebrewery_export = None
    mock_initial_orm_campaign.display_toc = [{"title": "Old Chapter 1", "type": "chapter"}] # Initial TOC
    mock_initial_orm_campaign.homebrewery_toc = None # Initial HB TOC
    mock_crud_get_campaign.return_value = mock_initial_orm_campaign

    # Mock ORM User object
    mock_orm_user = MagicMock(spec=ORMUser)
    mock_orm_user.id = mock_user_id
    mock_crud_get_user.return_value = mock_orm_user

    # Mock LLM Service
    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    generated_toc_list = [{"title": "Generated Chapter 1", "type": "chapter"}]
    mock_llm_instance.generate_toc = AsyncMock(return_value=generated_toc_list)
    mock_get_llm_service.return_value = mock_llm_instance

    # Mock ORM Campaign object (after TOC update)
    # This mock should reflect the state *after* update_campaign_toc is called
    from app.tests.conftest import create_mock_campaign_orm
    mock_updated_orm_campaign = create_mock_campaign_orm(
        id=mock_campaign_id,
        owner_id=mock_user_id,
        concept=mock_initial_orm_campaign.concept,
        title=mock_initial_orm_campaign.title,
        initial_user_prompt=mock_initial_orm_campaign.initial_user_prompt,
        mood_board_image_urls=mock_initial_orm_campaign.mood_board_image_urls,
        homebrewery_export=mock_initial_orm_campaign.homebrewery_export,
        display_toc=generated_toc_list,
        homebrewery_toc=None
    )
    mock_crud_update_toc.return_value = mock_updated_orm_campaign


    request_body = LLMGenerationRequest(model_id_with_prefix="openai/gpt-3.5-turbo")

    response = await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_id}/toc",
        json=request_body.model_dump()
    )

    assert response.status_code == 200, response.text
    response_data = response.json()

    # Validate campaign data in response
    # The endpoint returns a Pydantic model of the campaign
    validated_response_campaign = PydanticCampaign.model_validate(response_data)
    assert validated_response_campaign.id == mock_campaign_id
    assert validated_response_campaign.display_toc == generated_toc_list
    assert validated_response_campaign.homebrewery_toc is None


    mock_crud_get_campaign.assert_called_once_with(db=ANY, campaign_id=mock_campaign_id)
    mock_crud_get_user.assert_called_once_with(ANY, user_id=mock_user_id)
    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_orm_user,
        provider_name="openai",
        model_id_with_prefix="openai/gpt-3.5-turbo",
        campaign=mock_initial_orm_campaign
    )
    mock_llm_instance.generate_toc.assert_called_once_with(
        campaign_concept=mock_initial_orm_campaign.concept,
        db=ANY,
        current_user=current_active_user_override, # Pydantic User
        model="gpt-3.5-turbo"
    )
    mock_crud_update_toc.assert_called_once_with(
        db=ANY,
        campaign_id=mock_campaign_id,
        display_toc_content=generated_toc_list,
        homebrewery_toc_content=None
    )

# New test: Scenario where request model_id is None, uses campaign.selected_llm_id for TOC
@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign')
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_toc')
async def test_generate_campaign_toc_uses_campaign_model_when_request_model_none(
    mock_crud_update_toc: MagicMock,
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    mock_campaign_id = 2
    mock_user_id = current_active_user_override.id

    mock_initial_orm_campaign = MagicMock(spec=ORMCampaign)
    mock_initial_orm_campaign.id = mock_campaign_id
    mock_initial_orm_campaign.owner_id = mock_user_id
    mock_initial_orm_campaign.title = "Test Campaign Title"
    mock_initial_orm_campaign.concept = "Test concept for TOC - campaign model"
    mock_initial_orm_campaign.selected_llm_id = "testprovider/campaign_toc_model" # Campaign specific model
    mock_initial_orm_campaign.initial_user_prompt = "Test prompt"
    mock_initial_orm_campaign.mood_board_image_urls = []
    mock_initial_orm_campaign.homebrewery_export = None
    mock_crud_get_campaign.return_value = mock_initial_orm_campaign

    mock_orm_user = MagicMock(spec=ORMUser)
    mock_orm_user.id = mock_user_id
    mock_crud_get_user.return_value = mock_orm_user

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    generated_toc_list = [{"title": "Campaign Model TOC Item", "type": "generic"}]
    mock_llm_instance.generate_toc = AsyncMock(return_value=generated_toc_list)
    mock_get_llm_service.return_value = mock_llm_instance

    mock_updated_orm_campaign = create_mock_campaign_orm(
        id=mock_initial_orm_campaign.id,
        title=mock_initial_orm_campaign.title,
        owner_id=mock_initial_orm_campaign.owner_id,
        concept=mock_initial_orm_campaign.concept,
        display_toc=generated_toc_list
    )
    mock_crud_update_toc.return_value = mock_updated_orm_campaign

    request_body = LLMGenerationRequest(model_id_with_prefix=None) # No model in request

    await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_id}/toc",
        json=request_body.model_dump()
    )

    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_orm_user,
        provider_name=None,
        model_id_with_prefix=None,
        campaign=mock_initial_orm_campaign
    )
    mock_llm_instance.generate_toc.assert_called_once_with(
        campaign_concept=mock_initial_orm_campaign.concept,
        db=ANY,
        current_user=current_active_user_override,
        model="campaign_toc_model"
    )

# New test: Scenario where request and campaign model_id are None for TOC (system fallback)
@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign')
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_toc')
async def test_generate_campaign_toc_system_fallback(
    mock_crud_update_toc: MagicMock,
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    mock_campaign_id = 3
    mock_user_id = current_active_user_override.id

    mock_initial_orm_campaign = MagicMock(spec=ORMCampaign)
    mock_initial_orm_campaign.id = mock_campaign_id
    mock_initial_orm_campaign.owner_id = mock_user_id
    mock_initial_orm_campaign.title = "System Fallback Campaign"
    mock_initial_orm_campaign.concept = "Test concept for TOC - system fallback"
    mock_initial_orm_campaign.selected_llm_id = None # No campaign model
    mock_initial_orm_campaign.initial_user_prompt = "Test prompt"
    mock_initial_orm_campaign.mood_board_image_urls = []
    mock_initial_orm_campaign.homebrewery_export = None
    mock_crud_get_campaign.return_value = mock_initial_orm_campaign

    mock_orm_user = MagicMock(spec=ORMUser)
    mock_orm_user.id = mock_user_id
    mock_crud_get_user.return_value = mock_orm_user

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    generated_toc_list = [{"title": "System Fallback TOC Item", "type": "generic"}]
    mock_llm_instance.generate_toc = AsyncMock(return_value=generated_toc_list)
    mock_get_llm_service.return_value = mock_llm_instance

    mock_updated_orm_campaign = create_mock_campaign_orm(
        id=mock_initial_orm_campaign.id,
        title=mock_initial_orm_campaign.title,
        owner_id=mock_initial_orm_campaign.owner_id,
        concept=mock_initial_orm_campaign.concept,
        display_toc=generated_toc_list
    )
    mock_crud_update_toc.return_value = mock_updated_orm_campaign

    request_body = LLMGenerationRequest(model_id_with_prefix=None) # No model in request

    await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_id}/toc",
        json=request_body.model_dump()
    )

    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_orm_user,
        provider_name=None,
        model_id_with_prefix=None,
        campaign=mock_initial_orm_campaign
    )
    mock_llm_instance.generate_toc.assert_called_once_with(
        campaign_concept=mock_initial_orm_campaign.concept,
        db=ANY,
        current_user=current_active_user_override,
        model=None
    )

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_user') # Added patch for crud.get_user
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content')
async def test_seed_sections_from_toc_endpoint_uses_type(
    mock_crud_create_section: MagicMock,
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    db_campaign: ORMCampaign,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser,
    db_session: Session
):
    toc_data = [
        {"title": "NPC Alpha", "type": "npc"}, {"title": "The Beginning", "type": "generic"},
        {"title": "Location Beta", "type": "Location"}
    ]
    db_campaign_instance = db_session.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    db_campaign_instance.display_toc = toc_data
    db_campaign_instance.homebrewery_toc = []
    db_campaign_instance.selected_llm_id = "test_provider/test_model_campaign_setting"
    db_campaign_instance.concept = "A grand adventure concept for seeding."
    db_session.commit()
    db_session.refresh(db_campaign_instance)

    mock_user_orm = MagicMock(spec=ORMUser)
    mock_user_orm.id = current_active_user_override.id
    mock_crud_get_user.return_value = mock_user_orm

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Generated content")
    mock_get_llm_service.return_value = mock_llm_instance

    def mock_create_section_side_effect(db, campaign_id, title, order, placeholder_content, type):
        from datetime import datetime, timezone
        mock_section = MagicMock(spec=ORMCampaignSection)
        mock_section.id = order + 1; mock_section.title = title; mock_section.content = placeholder_content
        mock_section.order = order; mock_section.campaign_id = campaign_id; mock_section.type = type
        mock_section.user_prompt = None; mock_section.llm_prompt = None; mock_section.llm_response = None
        mock_section.word_count = len(placeholder_content.split()) if placeholder_content else 0
        now = datetime.now(timezone.utc)
        mock_section.images = []; mock_section.created_at = now; mock_section.updated_at = now
        return mock_section
    mock_crud_create_section.side_effect = mock_create_section_side_effect

    response = await async_client.post(f"/api/v1/campaigns/{db_campaign_instance.id}/seed_sections_from_toc?auto_populate=true") # Removed model_id_with_prefix from query
    async for _ in response.aiter_lines(): pass # Consume SSE stream

    assert response.status_code == 200, response.text # Added response.text for debugging

    # Assert get_user was called if auto-population path was taken
    if db_campaign_instance.selected_llm_id and db_campaign_instance.concept:
        mock_crud_get_user.assert_called_with(ANY, user_id=current_active_user_override.id)
        mock_get_llm_service.assert_called_with(
            db=ANY,
            current_user_orm=mock_user_orm,
            provider_name="test_provider", # from campaign's selected_llm_id
            model_id_with_prefix=db_campaign_instance.selected_llm_id,
            campaign=db_campaign_instance
        )

    assert mock_crud_create_section.call_count == 3 # Check if sections were created
    assert mock_crud_create_section.call_args_list[0].kwargs['type'] == "npc"
    assert mock_crud_create_section.call_args_list[1].kwargs['type'] == "generic"
    assert mock_crud_create_section.call_args_list[2].kwargs['type'] == "Location"
    assert mock_llm_instance.generate_section_content.call_count == 3
    assert mock_llm_instance.generate_section_content.call_args_list[0].kwargs['section_type'] == "npc"
    assert mock_llm_instance.generate_section_content.call_args_list[1].kwargs['section_type'] == "generic"
    assert mock_llm_instance.generate_section_content.call_args_list[2].kwargs['section_type'] == "Location"

@pytest.mark.asyncio
async def test_get_campaign_full_content_formats_new_toc(db_campaign: ORMCampaign, async_client: AsyncClient, db_session: Session):
    toc_data = [{"title": "Entry 1", "type": "chapter"}, {"title": "Entry 2", "type": "location"}]
    db_campaign_instance = db_session.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    db_campaign_instance.display_toc = toc_data
    db_campaign_instance.homebrewery_toc = []
    db_session.commit()
    db_session.refresh(db_campaign_instance)

    response = await async_client.get(f"/api/v1/campaigns/{db_campaign.id}/full_content")
    assert response.status_code == 200
    data = response.json()
    # Check that the TOC is formatted correctly (without requiring trailing newlines)
    assert "## Table of Contents" in data["full_content"]
    assert "- Entry 1" in data["full_content"]
    assert "- Entry 2" in data["full_content"]

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_user') # Added patch for crud.get_user
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.create_campaign_section')
async def test_create_new_campaign_section_endpoint_uses_type(
    mock_crud_create_section: MagicMock,
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock, # Added mock for crud.get_user
    db_campaign: ORMCampaign, # This is an ORM campaign fixture
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    # Mock for crud.get_user
    mock_user_orm = MagicMock(spec=ORMUser)
    mock_user_orm.id = current_active_user_override.id
    mock_crud_get_user.return_value = mock_user_orm

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    mock_llm_instance.generate_section_content = AsyncMock(return_value="Generated test content.")
    mock_get_llm_service.return_value = mock_llm_instance

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    mock_created_section = MagicMock(spec=ORMCampaignSection)
    mock_created_section.id = 1; mock_created_section.campaign_id = db_campaign.id
    mock_created_section.title = "New Section with Type"; mock_created_section.content = "Generated test content."
    mock_created_section.order = 0; mock_created_section.type = "custom_type"
    mock_created_section.user_prompt = "A detailed prompt."; mock_created_section.llm_prompt = "Actual LLM prompt."
    mock_created_section.llm_response = "Generated test content."; mock_created_section.word_count = len("Generated test content.".split())
    mock_created_section.images = []; mock_created_section.created_at = now; mock_created_section.updated_at = now
    mock_crud_create_section.return_value = mock_created_section

    section_payload = {
        "title": "New Section with Type", "prompt": "A detailed prompt.",
        "type": "custom_type", "model_id_with_prefix": "test/model"
    }
    response = await async_client.post(f"/api/v1/campaigns/{db_campaign.id}/sections", json=section_payload)
    assert response.status_code == 200, response.text

    mock_crud_get_user.assert_called_once_with(ANY, user_id=current_active_user_override.id)
    mock_get_llm_service.assert_called_once_with(
        db=ANY,
        current_user_orm=mock_user_orm,
        provider_name="test", # from section_payload's model_id_with_prefix
        model_id_with_prefix="test/model",
        campaign=db_campaign # Passed the ORM campaign
    )
    mock_crud_create_section.assert_called_once()
    assert mock_crud_create_section.call_args.kwargs['section_type'] == "custom_type"

    mock_llm_instance.generate_section_content.assert_called_once()
    # The model passed to generate_section_content should be "model" (extracted from "test/model")
    # and if section_payload["model_id_with_prefix"] was None, it should use campaign's model.
    assert mock_llm_instance.generate_section_content.call_args.kwargs['model'] == "model"
    assert mock_llm_instance.generate_section_content.call_args.kwargs['section_type'] == "custom_type"

    response_data = response.json()
    assert response_data["title"] == "New Section with Type"; assert response_data["content"] == "Generated test content."; assert response_data["type"] == "custom_type"

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.get_campaign') # Need to mock get_campaign as it's called first
@patch('app.api.endpoints.campaigns.crud.get_user')
@patch('app.api.endpoints.campaigns.get_llm_service')
@patch('app.api.endpoints.campaigns.crud.update_campaign_section')
async def test_regenerate_campaign_section_endpoint_uses_type(
    mock_crud_update_section: MagicMock,
    mock_get_llm_service: MagicMock,
    mock_crud_get_user: MagicMock,
    mock_crud_get_campaign: MagicMock, # Added mock for get_campaign
    db_section: ORMCampaignSection, # This fixture provides an existing section
    async_client: AsyncClient,
    current_active_user_override: PydanticUser
):
    # Mock the campaign associated with db_section
    mock_campaign_orm = MagicMock(spec=ORMCampaign)
    mock_campaign_orm.id = db_section.campaign_id
    mock_campaign_orm.owner_id = current_active_user_override.id
    mock_campaign_orm.concept = "Test Concept"
    mock_campaign_orm.selected_llm_id = "default_provider/default_model_campaign" # Campaign default
    mock_crud_get_campaign.return_value = mock_campaign_orm

    # Mock user orm
    mock_user_orm = MagicMock(spec=ORMUser)
    mock_user_orm.id = current_active_user_override.id
    mock_crud_get_user.return_value = mock_user_orm

    mock_llm_instance = AsyncMock(spec=AbstractLLMService)
    # Configure the mock to return the string when awaited
    mock_llm_instance.generate_text = AsyncMock(return_value="Regenerated content.")
    mock_get_llm_service.return_value = mock_llm_instance

    def update_side_effect(db, section_id, campaign_id, section_update_data: pydantic_models.CampaignSectionUpdateInput):
        updated_section_mock = MagicMock(spec=ORMCampaignSection)
        updated_section_mock.id = db_section.id
        updated_section_mock.campaign_id = db_section.campaign_id
        updated_section_mock.title = section_update_data.title if section_update_data.title is not None else db_section.title
        updated_section_mock.content = section_update_data.content if section_update_data.content is not None else db_section.content
        updated_section_mock.order = db_section.order
        updated_section_mock.type = section_update_data.type if section_update_data.type is not None else db_section.type
        updated_section_mock.word_count = len(updated_section_mock.content.split()) if updated_section_mock.content else 0
        if section_update_data.type is not None:
            db_section.type = section_update_data.type
        return updated_section_mock
    mock_crud_update_section.side_effect = update_side_effect

    # Scenario 1: Request specifies model_id_with_prefix
    request_model_prefix = "request_provider/request_model"
    regenerate_payload_with_type_and_model = {
        "section_type": "new_type_from_payload",
        "new_prompt": "A new prompt.",
        "model_id_with_prefix": request_model_prefix
    }
    response1 = await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_orm.id}/sections/{db_section.id}/regenerate", json=regenerate_payload_with_type_and_model
    )
    assert response1.status_code == 200, response1.text
    mock_get_llm_service.assert_called_with(
        db=ANY,
        current_user_orm=mock_user_orm,
        provider_name="request_provider",
        model_id_with_prefix=request_model_prefix,
        campaign=mock_campaign_orm
    )
    mock_llm_instance.generate_text.assert_called_once()
    # Check that the call included the section_type parameter
    call_kwargs = mock_llm_instance.generate_text.call_args.kwargs
    assert call_kwargs['section_type'] == "new_type_from_payload"
    assert call_kwargs['model'] == "request_model"
    
    assert mock_crud_update_section.call_args.kwargs['section_update_data'].type == "new_type_from_payload"
    assert response1.json()["type"] == "new_type_from_payload"

    # Reset mocks for next scenario
    mock_get_llm_service.reset_mock()
    mock_llm_instance.generate_text.reset_mock()
    mock_crud_update_section.reset_mock()

    # Scenario 2: Request does NOT specify model_id_with_prefix, uses campaign's selected_llm_id
    regenerate_payload_no_model = {
        "section_type": "type_from_db_or_new",
        "new_prompt": "Another new prompt."
    }
    db_section.type = "original_section_type_in_db"

    response2 = await async_client.post(
        f"/api/v1/campaigns/{mock_campaign_orm.id}/sections/{db_section.id}/regenerate", json=regenerate_payload_no_model
    )
    assert response2.status_code == 200, response2.text

    mock_get_llm_service.assert_called_with(
        db=ANY,
        current_user_orm=mock_user_orm,
        provider_name="default_provider",
        model_id_with_prefix=mock_campaign_orm.selected_llm_id,
        campaign=mock_campaign_orm
    )
    mock_llm_instance.generate_text.assert_called_once()
    # Check that the call included the section_type parameter
    call_kwargs = mock_llm_instance.generate_text.call_args.kwargs
    assert call_kwargs['section_type'] == "type_from_db_or_new"
    assert call_kwargs['model'] == "default_model_campaign"
    
    assert mock_crud_update_section.call_args.kwargs['section_update_data'].type == "type_from_db_or_new"
    assert response2.json()["type"] == "type_from_db_or_new"

@pytest.mark.asyncio
@patch('app.crud.ImageGenerationService.delete_image_from_blob_storage', new_callable=AsyncMock)
async def test_update_campaign_remove_moodboard_image_deletes_blob(
    mock_delete_blob, db_campaign: ORMCampaign, async_client: AsyncClient, db_session: Session
):
    initial_url1 = f"https://mockaccount.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER_NAME}/blob1.png"
    initial_url2 = f"https://mockaccount.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER_NAME}/blob2.jpg"
    
    campaign_to_update = db_session.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    if not campaign_to_update:
        pytest.fail(f"Campaign with ID {db_campaign.id} not found.")
    campaign_to_update.mood_board_image_urls = [initial_url1, initial_url2]
    db_session.commit()
    
    update_payload = { "mood_board_image_urls": [initial_url1] }
    response = await async_client.put(f"/api/v1/campaigns/{db_campaign.id}", json=update_payload)
    assert response.status_code == 200, response.text
    mock_delete_blob.assert_called_once_with("blob2.jpg")
    
    updated_db_campaign = db_session.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    assert updated_db_campaign.mood_board_image_urls == [initial_url1]

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.ImageGenerationService._save_image_and_log_db', new_callable=AsyncMock)
async def test_upload_moodboard_image_success(
    mock_save_image, db_campaign: ORMCampaign, async_client: AsyncClient, db_session: Session
):
    mock_image_url = "http://example.com/mock_uploaded_image.png"
    mock_save_image.return_value = mock_image_url
    image_content = b"fake image data"
    image_bytes_io = BytesIO(image_content)
    file_name = "test_image.png"
    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/moodboard/upload",
        files={"file": (file_name, image_bytes_io, "image/png")}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["image_url"] == mock_image_url
    assert data["campaign"]["id"] == db_campaign.id
    assert mock_image_url in data["campaign"]["mood_board_image_urls"]
    mock_save_image.assert_called_once()
    assert mock_save_image.call_args[1]['image_bytes'] == image_content
    assert mock_save_image.call_args[1]['user_id'] == db_campaign.owner_id
    assert mock_save_image.call_args[1]['original_filename_from_api'] == file_name
    
    updated_db_campaign = db_session.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    assert mock_image_url in updated_db_campaign.mood_board_image_urls

@pytest.mark.asyncio
async def test_upload_moodboard_image_campaign_not_found(async_client: AsyncClient, current_active_user_override: PydanticUser):
    image_bytes_io = BytesIO(b"fake image data")
    response = await async_client.post(
        "/api/v1/campaigns/99999/moodboard/upload",
        files={"file": ("test.png", image_bytes_io, "image/png")}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Campaign not found"

@pytest.mark.asyncio
async def test_upload_moodboard_image_unauthorized(db_campaign: ORMCampaign, async_client: AsyncClient, db_session: Session):
    other_user_campaign = ORMCampaign(title="Other User Campaign", owner_id=2)
    db_session.add(other_user_campaign)
    db_session.commit()
    db_session.refresh(other_user_campaign)
    other_campaign_id = other_user_campaign.id
    
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
    mock_save_image, db_campaign: ORMCampaign, async_client: AsyncClient, db_session: Session
):
    mock_save_image.side_effect = HTTPException(status_code=500, detail="Azure upload failed")
    initial_moodboard_urls = list(db_campaign.mood_board_image_urls or [])
    image_bytes_io = BytesIO(b"fake image data")
    response = await async_client.post(
        f"/api/v1/campaigns/{db_campaign.id}/moodboard/upload",
        files={"file": ("test.png", image_bytes_io, "image/png")}
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Azure upload failed"
    
    unchanged_db_campaign = db_session.query(ORMCampaign).filter(ORMCampaign.id == db_campaign.id).first()
    assert list(unchanged_db_campaign.mood_board_image_urls or []) == initial_moodboard_urls

# Test campaign creation with skip_concept_generation flag
@pytest.mark.asyncio
@patch('app.crud.get_llm_service')
async def test_create_campaign_api_skip_concept_generation(
    mock_crud_get_llm_service: MagicMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser # To ensure auth
):
    mock_llm_instance_crud = AsyncMock()
    mock_llm_instance_crud.generate_campaign_concept = AsyncMock(return_value="Mocked Concept by CRUD LLM")
    mock_crud_get_llm_service.return_value = mock_llm_instance_crud

    # Scenario 1: skip_concept_generation = True
    payload_skip_true = {
        "title": "API Skip True Campaign",
        "initial_user_prompt": "This prompt should be ignored by LLM.",
        "skip_concept_generation": True
    }
    response_skip_true = await async_client.post("/api/v1/campaigns/", json=payload_skip_true)
    assert response_skip_true.status_code == 200, response_skip_true.text
    data_skip_true = response_skip_true.json()
    assert data_skip_true["title"] == "API Skip True Campaign"
    assert data_skip_true["concept"] is None
    mock_llm_instance_crud.generate_campaign_concept.assert_not_called()

    mock_crud_get_llm_service.reset_mock()
    mock_llm_instance_crud.generate_campaign_concept.reset_mock()
    mock_crud_get_llm_service.return_value = mock_llm_instance_crud


    # Scenario 2: skip_concept_generation = False (or not provided, defaults to False)
    payload_skip_false = {
        "title": "API Skip False Campaign",
        "initial_user_prompt": "Generate concept for this API test.",
        "skip_concept_generation": False # Explicitly false
    }
    response_skip_false = await async_client.post("/api/v1/campaigns/", json=payload_skip_false)
    assert response_skip_false.status_code == 200, response_skip_false.text
    data_skip_false = response_skip_false.json()
    assert data_skip_false["title"] == "API Skip False Campaign"
    assert data_skip_false["concept"] == "Mocked Concept by CRUD LLM"
    mock_llm_instance_crud.generate_campaign_concept.assert_called_once()


# Test manual concept generation endpoint
@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.get_llm_service') # Patching where the endpoint uses it
async def test_generate_concept_manually_api(
    mock_endpoint_get_llm_service: MagicMock, # Mock for get_llm_service used by the endpoint
    async_client: AsyncClient,
    current_active_user_override: PydanticUser,
    db_session: Session
):
    # Create an ORM campaign directly for this test
    test_orm_campaign = ORMCampaign(
        id=123,
        title="Manual Concept Test Campaign",
        owner_id=current_active_user_override.id,
        concept=None,
        initial_user_prompt="Original prompt if any",
        selected_llm_id="default_provider/default_model"
    )
    db_session.add(test_orm_campaign)
    db_session.commit()
    db_session.refresh(test_orm_campaign)
    campaign_id_for_test = test_orm_campaign.id

    # Mock the LLM service for the endpoint
    mock_llm_instance_endpoint = AsyncMock()
    mock_llm_instance_endpoint.generate_campaign_concept = AsyncMock(return_value="Manually Generated Concept")
    mock_endpoint_get_llm_service.return_value = mock_llm_instance_endpoint

    # Call the manual generation endpoint
    generation_payload = {
        "prompt": "New prompt for manual generation.",
        "model_id_with_prefix": "openai/gpt-3.5-turbo-instruct"
    }
    response = await async_client.post(
        f"/api/v1/campaigns/{campaign_id_for_test}/generate-concept",
        json=generation_payload
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == campaign_id_for_test
    assert data["concept"] == "Manually Generated Concept"

    # Assert LLM service was called correctly by the endpoint
    mock_endpoint_get_llm_service.assert_called_once()
    expected_provider, expected_model = generation_payload["model_id_with_prefix"].split('/')

    call_args_get_llm = mock_endpoint_get_llm_service.call_args
    assert call_args_get_llm.kwargs['provider_name'] == expected_provider
    assert call_args_get_llm.kwargs['model_id_with_prefix'] == generation_payload['model_id_with_prefix']

    mock_llm_instance_endpoint.generate_campaign_concept.assert_called_once()
    call_args_generate_concept = mock_llm_instance_endpoint.generate_campaign_concept.call_args
    assert call_args_generate_concept.kwargs['user_prompt'] == generation_payload["prompt"]
    assert call_args_generate_concept.kwargs['model'] == expected_model

    # Clean up
    campaign_to_delete = db_session.query(ORMCampaign).filter(ORMCampaign.id == campaign_id_for_test).first()
    if campaign_to_delete:
        db_session.delete(campaign_to_delete)
        db_session.commit()

# --- Test DELETE /campaigns/{campaign_id} ---

def create_another_user_in_db(db_session: Session, id: int, email: str, username: str) -> ORMUser:
    """Helper to create an additional ORM user for testing ownership."""
    another_user = ORMUser(
        id=id,
        username=username,
        email=email,
        full_name="Another User",
        hashed_password="anotherfakepassword",
        disabled=False,
        is_superuser=False
    )
    db_session.add(another_user)
    db_session.commit()
    db_session.refresh(another_user)
    return another_user

@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.delete_campaign', new_callable=AsyncMock)
async def test_delete_campaign_endpoint_success(
    mock_crud_delete_campaign: AsyncMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser,
    db_session: Session
):
    # Create a campaign owned by the authenticated test user
    owned_campaign = ORMCampaign(id=101, title="Owned Campaign", owner_id=current_active_user_override.id, concept="Test")
    db_session.add(owned_campaign)
    db_session.commit()
    db_session.refresh(owned_campaign)
    campaign_id_to_delete = owned_campaign.id

    # Mock crud.delete_campaign
    #    It should return an object that FastAPI can convert to the response_model (PydanticCampaign)
    #    So, returning a mock ORM campaign object is suitable.
    mock_deleted_orm_campaign = create_mock_campaign_orm(
        id=campaign_id_to_delete,
        title="Owned Campaign",
        owner_id=current_active_user_override.id,
        concept="Test"
    )


    mock_crud_delete_campaign.return_value = mock_deleted_orm_campaign

    # 3. Make a DELETE request
    response = await async_client.delete(f"/api/v1/campaigns/{campaign_id_to_delete}")

    # 4. Assertions
    assert response.status_code == 200, response.text
    mock_crud_delete_campaign.assert_called_once_with(
        db=ANY, campaign_id=campaign_id_to_delete, user_id=current_active_user_override.id
    )

    response_data = response.json()
    assert response_data["id"] == campaign_id_to_delete
    assert response_data["title"] == "Owned Campaign"
    assert response_data["owner_id"] == current_active_user_override.id

    # Clean up - db_session is already a Session object, not a callable
    try:
        db_session.delete(owned_campaign)
        db_session.commit()
    except: # If already deleted by a real CRUD call (which is mocked here, so won't happen)
        pass


@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.delete_campaign', new_callable=AsyncMock)
async def test_delete_campaign_endpoint_not_owned(
    mock_crud_delete_campaign: AsyncMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser,
    db_session: Session
):
    # Create another user and a campaign owned by them
    other_user = create_another_user_in_db(db_session, id=2, email="other@example.com", username="otheruser")
    not_owned_campaign = ORMCampaign(id=102, title="Not Owned Campaign", owner_id=other_user.id, concept="Test")
    db_session.add(not_owned_campaign)
    db_session.commit()
    db_session.refresh(not_owned_campaign)
    campaign_id_to_delete = not_owned_campaign.id

    # 2. Make a DELETE request using the authenticated test user (id=1)
    response = await async_client.delete(f"/api/v1/campaigns/{campaign_id_to_delete}")

    # 3. Assertions
    assert response.status_code == 403, response.text
    assert "Not authorized to delete this campaign" in response.json()["detail"]
    mock_crud_delete_campaign.assert_not_called() # Crucial: CRUD delete should not be called

    # Clean up - db_session is already a Session object, not a callable
    try:
        db_session.delete(not_owned_campaign)
        db_session.delete(other_user)
        db_session.commit()
    except:
        pass

@pytest.mark.asyncio
async def test_delete_campaign_endpoint_not_found(
    async_client: AsyncClient,
    current_active_user_override: PydanticUser # Auth still needed
):
    non_existent_campaign_id = 99999
    response = await async_client.delete(f"/api/v1/campaigns/{non_existent_campaign_id}")
    assert response.status_code == 404, response.text
    assert "Campaign not found" in response.json()["detail"]


@pytest.mark.asyncio
@patch('app.api.endpoints.campaigns.crud.delete_campaign', new_callable=AsyncMock)
async def test_delete_campaign_endpoint_crud_fails_unexpectedly(
    mock_crud_delete_campaign: AsyncMock,
    async_client: AsyncClient,
    current_active_user_override: PydanticUser,
    db_session: Session
):
    owned_campaign = ORMCampaign(id=103, title="Campaign For CRUD Failure", owner_id=current_active_user_override.id, concept="Test")
    db_session.add(owned_campaign)
    db_session.commit()
    db_session.refresh(owned_campaign)
    campaign_id_to_delete = owned_campaign.id

    mock_crud_delete_campaign.side_effect = RuntimeError("Unexpected CRUD error")

    response = await async_client.delete(f"/api/v1/campaigns/{campaign_id_to_delete}")

    # FastAPI typically catches unhandled exceptions and returns a 500 error.
    # If specific exception handling were added to the endpoint for RuntimeError, this would change.
    assert response.status_code == 500, response.text
    # The exact detail message might vary depending on FastAPI's default 500 error handling
    # or if there's a custom exception handler. For now, checking status code is primary.

    mock_crud_delete_campaign.assert_called_once_with(
        db=ANY, campaign_id=campaign_id_to_delete, user_id=current_active_user_override.id
    )

    # Clean up - db_session is already a Session object, not a callable
    try:
        db_session.delete(owned_campaign)
        db_session.commit()
    except:
        pass
