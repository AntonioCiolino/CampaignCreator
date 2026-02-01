import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from unittest.mock import patch, AsyncMock

from app.core.config import settings
from app.main import app # Assuming your FastAPI app instance is here
from app.models import Campaign, CampaignSection # Pydantic models for response validation
from app.orm_models import Campaign as ORMCampaign, CampaignSection as ORMSection # DB models
from app import orm_models  # For type hints using orm_models.X
from app.services.llm_service import LLMGenerationError # For mocking

# Fixtures (consider placing in a conftest.py if widely used)
@pytest.fixture
async def test_client() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def db_session_mock(mocker):
    mock = mocker.MagicMock(spec=Session)
    # Add more specific mock behaviors if needed for CRUD operations directly
    return mock

@pytest.fixture
def mock_llm_service(mocker):
    mock_service = AsyncMock()
    # Default behavior for generate_section_content
    mock_service.generate_section_content = AsyncMock(return_value="Mocked LLM Content")
    # Mock is_available to always be true for these tests
    mock_service.is_available = AsyncMock(return_value=True)

    # Patch get_llm_service in the campaigns endpoint module
    # The path to patch is where 'get_llm_service' is *looked up*, not where it's defined.
    mocker.patch('app.api.endpoints.campaigns.get_llm_service', return_value=mock_service)
    return mock_service

@pytest.fixture
async def test_campaign(db_session_mock: Session) -> ORMCampaign:
    # This fixture should ideally create a campaign in a test DB.
    # For now, mocking its retrieval via CRUD.
    campaign = ORMCampaign(
        id=1,
        title="Test Campaign",
        concept="A grand adventure concept.",
        display_toc="- Chapter 1: The Beginning\n- NPC: Gandalf\n- Location: The Shire",
        homebrewery_toc="HB TOC",
        owner_id=1,
        selected_llm_id=f"{settings.DEFAULT_LLM_PROVIDER}/{settings.DEFAULT_LLM_MODEL_CHAT}",
        temperature=0.7
    )
    # Mock crud.get_campaign to return this campaign
    with patch('app.api.endpoints.campaigns.crud.get_campaign', return_value=campaign) as mock_get_campaign:
        # Mock crud.get_campaign_sections for the regenerate endpoint context
        with patch('app.api.endpoints.campaigns.crud.get_campaign_sections', return_value=[]) as mock_get_sections:
            yield campaign


# --- Tests for seed_sections_from_toc ---

async def test_seed_sections_from_toc_no_autopopulate(
    test_client: AsyncClient,
    test_campaign: ORMCampaign,
    db_session_mock: Session,
    mock_llm_service: AsyncMock # To ensure it's NOT called
):
    # Mock crud.delete_sections_for_campaign
    with patch('app.api.endpoints.campaigns.crud.delete_sections_for_campaign', return_value=0) as mock_delete:
        # Mock crud.create_section_with_placeholder_content
        created_sections_mock = [
            ORMSection(id=1, campaign_id=test_campaign.id, title="Chapter 1: The Beginning", content="Content for 'Chapter 1: The Beginning' to be generated.", order=0),
            ORMSection(id=2, campaign_id=test_campaign.id, title="NPC: Gandalf", content="Content for 'NPC: Gandalf' to be generated.", order=1),
            ORMSection(id=3, campaign_id=test_campaign.id, title="Location: The Shire", content="Content for 'Location: The Shire' to be generated.", order=2),
        ]
        with patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content', side_effect=created_sections_mock) as mock_create:
            response = await test_client.post(
                f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=false"
            )
            assert response.status_code == 200
            sections_data = response.json()
            assert len(sections_data) == 3
            assert sections_data[0]['title'] == "Chapter 1: The Beginning"
            assert sections_data[0]['content'] == "Content for 'Chapter 1: The Beginning' to be generated."
            assert sections_data[1]['title'] == "NPC: Gandalf"
            assert sections_data[2]['title'] == "Location: The Shire"

            mock_delete.assert_called_once_with(db=db_session_mock, campaign_id=test_campaign.id)
            assert mock_create.call_count == 3
            mock_llm_service.generate_section_content.assert_not_called()


async def test_seed_sections_from_toc_with_autopopulate(
    test_client: AsyncClient,
    test_campaign: ORMCampaign,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    # Mock crud operations
    with patch('app.api.endpoints.campaigns.crud.delete_sections_for_campaign', return_value=0):
        # Titles that will be extracted by the endpoint from test_campaign.display_toc
        parsed_titles_from_toc = ["Chapter 1: The Beginning", "NPC: Gandalf", "Location: The Shire"]

        created_sections_side_effect = [
            ORMSection(id=i+1, campaign_id=test_campaign.id, title=parsed_titles_from_toc[i], content="Mocked LLM Content", order=i)
            for i in range(len(parsed_titles_from_toc))
        ]
        with patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content', side_effect=created_sections_side_effect) as mock_create:
            response = await test_client.post(
                f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=true"
            )
            assert response.status_code == 200
            sections_data = response.json()
            assert len(sections_data) == len(parsed_titles_from_toc)
            for section in sections_data:
                assert section['content'] == "Mocked LLM Content"

            assert mock_llm_service.generate_section_content.call_count == len(parsed_titles_from_toc)

            found_npc_prompt_call = False
            for call_args in mock_llm_service.generate_section_content.call_args_list:
                kwargs = call_args.kwargs
                if kwargs.get("section_title_suggestion") == "NPC: Gandalf" and \
                   "NPC named 'Gandalf'" in kwargs.get("section_creation_prompt", ""):
                    found_npc_prompt_call = True
                    assert kwargs.get("campaign_concept") == test_campaign.concept
                    # Extract model_specific_id from the format provider/model_id
                    provider_name, model_specific_id = test_campaign.selected_llm_id.split('/',1)
                    assert kwargs.get("model") == model_specific_id
                    break
            assert found_npc_prompt_call, "NPC specific prompt for Gandalf was not called as expected."

async def test_seed_sections_from_toc_autopopulate_llm_error(
    test_client: AsyncClient,
    test_campaign: ORMCampaign,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    mock_llm_service.generate_section_content.side_effect = LLMGenerationError("LLM failed")

    parsed_titles_from_toc = ["Chapter 1: The Beginning", "NPC: Gandalf", "Location: The Shire"]
    with patch('app.api.endpoints.campaigns.crud.delete_sections_for_campaign', return_value=0):
        created_sections_side_effect = [
            ORMSection(id=i+1, campaign_id=test_campaign.id, title=parsed_titles_from_toc[i], content=f"Content for '{parsed_titles_from_toc[i]}' to be generated.", order=i)
            for i in range(len(parsed_titles_from_toc))
        ]
        with patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content', side_effect=created_sections_side_effect) as mock_create:
            response = await test_client.post(
                f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=true"
            )
            assert response.status_code == 200
            sections_data = response.json()
            assert len(sections_data) == len(parsed_titles_from_toc)
            for i, section in enumerate(sections_data):
                assert section['content'] == f"Content for '{parsed_titles_from_toc[i]}' to be generated."

            assert mock_llm_service.generate_section_content.call_count == len(parsed_titles_from_toc)

# --- Tests for regenerate section endpoint ---

@pytest.fixture
async def test_section(db_session_mock: Session, test_campaign: ORMCampaign) -> ORMSection:
    section = ORMSection(
        id=1, # Ensure this ID is distinct or managed if multiple sections are created
        campaign_id=test_campaign.id,
        title="Original Section Title",
        content="Original section content.",
        order=0
    )
    # Mock crud.get_section (used by regenerate endpoint)
    with patch('app.api.endpoints.campaigns.crud.get_section', return_value=section) as mock_get_section:
        yield section

async def test_regenerate_section_default(
    test_client: AsyncClient,
    test_campaign: ORMCampaign,
    test_section: ORMSection,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    # Create a dictionary from the ORM model to simulate data that might be used for updating
    # This helps avoid issues if the ORM object itself is modified by the service/crud call
    section_dict = {column.name: getattr(test_section, column.name) for column in test_section.__table__.columns}
    updated_section_mock = ORMSection(**section_dict)
    updated_section_mock.content = "Mocked LLM Content"

    with patch('app.api.endpoints.campaigns.crud.update_campaign_section', return_value=updated_section_mock) as mock_update:
        response = await test_client.post(
            f"/api/v1/campaigns/{test_campaign.id}/sections/{test_section.id}/regenerate",
            json={} # Empty payload for default regeneration
        )
        assert response.status_code == 200
        section_data = response.json()
        assert section_data['content'] == "Mocked LLM Content"
        assert section_data['title'] == test_section.title

        mock_llm_service.generate_section_content.assert_called_once()
        call_kwargs = mock_llm_service.generate_section_content.call_args.kwargs
        assert call_kwargs.get("campaign_concept") == test_campaign.concept
        assert call_kwargs.get("section_title_suggestion") == test_section.title
        assert "Generate content for a section titled" in call_kwargs.get("section_creation_prompt")

        mock_update.assert_called_once()


async def test_regenerate_section_with_new_prompt_and_title(
    test_client: AsyncClient,
    test_campaign: ORMCampaign,
    test_section: ORMSection,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    new_title = "Regenerated NPC: Boromir"
    new_prompt = "Focus on Boromir's internal conflict and his views on Minas Tirith."

    section_dict = {column.name: getattr(test_section, column.name) for column in test_section.__table__.columns}
    updated_section_mock = ORMSection(**section_dict)
    updated_section_mock.title = new_title
    updated_section_mock.content = "Mocked LLM Content for Boromir"
    mock_llm_service.generate_section_content.return_value = "Mocked LLM Content for Boromir"

    with patch('app.api.endpoints.campaigns.crud.update_campaign_section', return_value=updated_section_mock) as mock_update:
        response = await test_client.post(
            f"/api/v1/campaigns/{test_campaign.id}/sections/{test_section.id}/regenerate",
            json={
                "new_title": new_title,
                "new_prompt": new_prompt,
                "section_type": "NPC"
            }
        )
        assert response.status_code == 200
        section_data = response.json()
        assert section_data['content'] == "Mocked LLM Content for Boromir"
        assert section_data['title'] == new_title

        mock_llm_service.generate_section_content.assert_called_once()
        call_kwargs = mock_llm_service.generate_section_content.call_args.kwargs
        assert call_kwargs.get("section_title_suggestion") == new_title
        assert call_kwargs.get("section_creation_prompt") == new_prompt

        mock_update.assert_called_once()
        update_payload = mock_update.call_args.kwargs['section_update_data']
        assert update_payload.title == new_title
        assert update_payload.content == "Mocked LLM Content for Boromir"

async def test_regenerate_section_llm_fails(
    test_client: AsyncClient,
    test_campaign: ORMCampaign,
    test_section: ORMSection,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    mock_llm_service.generate_section_content.side_effect = LLMGenerationError("LLM regeneration failed")

    response = await test_client.post(
        f"/api/v1/campaigns/{test_campaign.id}/sections/{test_section.id}/regenerate",
        json={}
    )
    assert response.status_code == 500
    assert "LLM regeneration failed" in response.json()['detail']

# Note: The ORMSection doesn't have an as_dict() method by default.
# For test_regenerate_section_default and test_regenerate_section_with_new_prompt_and_title,
# I've used a dictionary comprehension to create a dict from the ORM model attributes.
# This is a common way to get a plain dict for creating copies or for assertions.
# Test for selected_llm_id parsing in test_seed_sections_from_toc_with_autopopulate was also refined.
# Placeholder titles in test_seed_sections_from_toc_with_autopopulate and _llm_error were made more specific.

# --- SSE Test Helper and Tests ---

async def consume_sse_events(client: AsyncClient, url: str) -> list:
    events = []
    try:
        async with client.stream("POST", url) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        data_str = line[len("data:"):].strip()
                        if data_str:
                             events.append(json.loads(data_str))
                    except json.JSONDecodeError:
                        print(f"Warning: Failed to decode JSON from SSE event: {line}")
                elif line.strip() == "" and events and events[-1].get("event_type") == "complete":
                    pass
    except Exception as e:
        print(f"Error consuming SSE stream: {type(e).__name__} - {e}")
    return events

async def test_seed_sections_from_toc_sse_no_autopopulate(
    test_client: AsyncClient,
    test_campaign: orm_models.Campaign,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    # Assuming test_campaign.display_toc = "- Chapter 1: The Beginning\n- NPC: Gandalf\n- Location: The Shire"
    expected_titles = ["Chapter 1: The Beginning", "NPC: Gandalf", "Location: The Shire"]

    def mock_create_section_side_effect(db, campaign_id, title, order, placeholder_content):
        mock_orm_section = orm_models.CampaignSection(
            id=order + 1,
            campaign_id=campaign_id,
            title=title,
            content=placeholder_content,
            order=order
        )
        return mock_orm_section

    with patch('app.api.endpoints.campaigns.crud.delete_sections_for_campaign', return_value=0) as mock_delete, \
         patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content', side_effect=mock_create_section_side_effect) as mock_create:

        url = f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=false"
        events = await consume_sse_events(test_client, url)

        assert len(events) > 0, "No SSE events received"

        section_update_events = [e for e in events if e.get("event_type") == "section_update"]
        assert len(section_update_events) == len(expected_titles)

        for i, event in enumerate(section_update_events):
            assert event["current_section_title"] == expected_titles[i]
            assert event["section_data"]["title"] == expected_titles[i]
            assert event["section_data"]["content"] == f"Content for '{expected_titles[i]}' to be generated."
            assert event["progress_percent"] == round(((i + 1) / len(expected_titles)) * 100, 2)

        completion_events = [e for e in events if e.get("event_type") == "complete"]
        assert len(completion_events) == 1
        assert completion_events[0]["message"] == "Section seeding process finished."
        assert completion_events[0]["total_sections_processed"] == len(expected_titles)


        mock_delete.assert_called_once_with(db=db_session_mock, campaign_id=test_campaign.id)
        assert mock_create.call_count == len(expected_titles)
        mock_llm_service.generate_section_content.assert_not_called()


async def test_seed_sections_from_toc_sse_with_autopopulate(
    test_client: AsyncClient,
    test_campaign: orm_models.Campaign,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    # Ensure test_campaign has selected_llm_id and concept for this test
    assert test_campaign.selected_llm_id, "Test campaign must have selected_llm_id for auto-populate tests"
    assert test_campaign.concept, "Test campaign must have a concept for auto-populate tests"

    expected_titles = ["Chapter 1: The Beginning", "NPC: Gandalf", "Location: The Shire"]
    mock_llm_service.generate_section_content.return_value = "Mocked LLM Content via SSE"

    def mock_create_section_side_effect(db, campaign_id, title, order, placeholder_content):
        mock_orm_section = orm_models.CampaignSection(
            id=order + 1, campaign_id=campaign_id, title=title, content=placeholder_content, order=order
        )
        return mock_orm_section

    with patch('app.api.endpoints.campaigns.crud.delete_sections_for_campaign', return_value=0), \
         patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content', side_effect=mock_create_section_side_effect):

        url = f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=true"
        events = await consume_sse_events(test_client, url)

        assert len(events) > 0, "No SSE events received"
        section_update_events = [e for e in events if e.get("event_type") == "section_update"]
        assert len(section_update_events) == len(expected_titles)

        for i, event in enumerate(section_update_events):
            assert event["current_section_title"] == expected_titles[i]
            assert event["section_data"]["content"] == "Mocked LLM Content via SSE"

        completion_events = [e for e in events if e.get("event_type") == "complete"]
        assert len(completion_events) == 1
        assert completion_events[0]["total_sections_processed"] == len(expected_titles)

        assert mock_llm_service.generate_section_content.call_count == len(expected_titles)
        # Example: Check arguments for the "NPC: Gandalf" call specifically
        gandalf_call = next((c for c in mock_llm_service.generate_section_content.call_args_list
                             if c.kwargs.get("section_title_suggestion") == "NPC: Gandalf"), None)
        assert gandalf_call is not None
        assert "NPC named 'Gandalf'" in gandalf_call.kwargs.get("section_creation_prompt", "")


async def test_seed_sections_from_toc_sse_autopopulate_llm_error_per_section(
    test_client: AsyncClient,
    test_campaign: orm_models.Campaign,
    db_session_mock: Session,
    mock_llm_service: AsyncMock
):
    expected_titles = ["Chapter 1: The Beginning", "NPC: Gandalf", "Location: The Shire"]

    async def llm_side_effect(*args, **kwargs):
        if kwargs.get("section_title_suggestion") == "NPC: Gandalf": # Target specific title
            raise LLMGenerationError("LLM failed for Gandalf")
        return "Successfully generated content"
    mock_llm_service.generate_section_content.side_effect = llm_side_effect

    def mock_create_section_side_effect(db, campaign_id, title, order, placeholder_content):
        return orm_models.CampaignSection(id=order + 1, campaign_id=campaign_id, title=title, content=placeholder_content, order=order)

    with patch('app.api.endpoints.campaigns.crud.delete_sections_for_campaign', return_value=0), \
         patch('app.api.endpoints.campaigns.crud.create_section_with_placeholder_content', side_effect=mock_create_section_side_effect):

        url = f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=true"
        events = await consume_sse_events(test_client, url)

        section_update_events = [e for e in events if e.get("event_type") == "section_update"]
        assert len(section_update_events) == len(expected_titles)

        for event in section_update_events:
            if event["current_section_title"] == "NPC: Gandalf":
                assert event["section_data"]["content"] == "Content for 'NPC: Gandalf' to be generated."
            else:
                assert event["section_data"]["content"] == "Successfully generated content"

        assert mock_llm_service.generate_section_content.call_count == len(expected_titles)

        completion_events = [e for e in events if e.get("event_type") == "complete"]
        assert len(completion_events) == 1
        assert completion_events[0]["total_sections_processed"] == len(expected_titles)

async def test_seed_sections_from_toc_sse_empty_toc(
    test_client: AsyncClient,
    test_campaign: orm_models.Campaign,
    db_session_mock: Session
):
    # Temporarily override test_campaign's display_toc for this test
    with patch.object(test_campaign, 'display_toc', ""): # Empty TOC
        url = f"/api/v1/campaigns/{test_campaign.id}/seed_sections_from_toc?auto_populate=false"
        events = await consume_sse_events(test_client, url)

        assert len(events) == 1
        assert events[0]["event_type"] == "complete"
        assert "No titles found in TOC" in events[0]["message"]
        # No sections should be processed
        assert events[0].get("total_sections_processed") is None # Or 0, depending on backend logic for this case. The current SSE impl might not send it.

# Consider adding pytest-asyncio and an event_loop fixture if not already configured.
