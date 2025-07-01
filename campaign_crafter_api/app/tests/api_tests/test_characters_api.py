import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional, List, Dict, AsyncGenerator

from app.main import app
from app.db import Base, get_db
from app.orm_models import User as ORMUser, Campaign as ORMCampaign, Character as ORMCharacter
from app import crud, models as pydantic_models
from app.services.auth_service import get_current_active_user

# In-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:" # Use a separate in-memory DB for these tests or ensure clean state
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the override at the app level for all tests in this module
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    # Create tables at the beginning of each test function
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables at the end of each test function
    Base.metadata.drop_all(bind=engine)

@pytest_asyncio.fixture
async def async_test_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def test_user_orm(setup_database) -> ORMUser: # Depends on setup_database to ensure schema exists
    db = TestingSessionLocal()
    user_create = pydantic_models.UserCreate(username="char_testuser", email="char_test@example.com", password="password")
    orm_user = crud.create_user(db=db, user=user_create)
    db.close()
    return orm_user

@pytest_asyncio.fixture
async def authenticated_user_override(test_user_orm: ORMUser):
    # This Pydantic user is what get_current_active_user will return
    pydantic_user = pydantic_models.User.from_orm(test_user_orm)

    def _override_get_current_active_user():
        return pydantic_user

    original_dependency = app.dependency_overrides.get(get_current_active_user)
    app.dependency_overrides[get_current_active_user] = _override_get_current_active_user
    yield pydantic_user # The Pydantic model of the user
    # Teardown: restore original dependency
    if original_dependency:
        app.dependency_overrides[get_current_active_user] = original_dependency
    else:
        del app.dependency_overrides[get_current_active_user]


# --- Character API Tests ---

@pytest.mark.asyncio
async def test_create_character_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User):
    char_payload = {
        "name": "Bartholomew Buttercup",
        "description": "A gentle giant.",
        "stats": {"strength": 18, "constitution": 16}
    }
    response = await async_test_client.post("/api/v1/characters/", json=char_payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Bartholomew Buttercup"
    assert data["owner_id"] == authenticated_user_override.id
    assert data["stats"]["strength"] == 18
    assert data["stats"]["dexterity"] == 10 # Default

@pytest.mark.asyncio
async def test_get_user_characters_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User, test_user_orm: ORMUser):
    db = TestingSessionLocal()
    try:
        # Create some characters for the user
        crud.create_character(db, pydantic_models.CharacterCreate(name="Char1"), user_id=test_user_orm.id)
        crud.create_character(db, pydantic_models.CharacterCreate(name="Char2"), user_id=test_user_orm.id)
    finally:
        db.close()

    response = await async_test_client.get("/api/v1/characters/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2
    assert {char["name"] for char in data} == {"Char1", "Char2"}

@pytest.mark.asyncio
async def test_get_single_character_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User, test_user_orm: ORMUser):
    db = TestingSessionLocal()
    try:
        char = crud.create_character(db, pydantic_models.CharacterCreate(name="Specific Char"), user_id=test_user_orm.id)
        char_id = char.id
    finally:
        db.close()

    response = await async_test_client.get(f"/api/v1/characters/{char_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Specific Char"
    assert data["id"] == char_id

    # Test accessing non-existent character
    response_not_found = await async_test_client.get("/api/v1/characters/9999")
    assert response_not_found.status_code == 404

    # Test accessing character of another user (requires another user and character)
    db = TestingSessionLocal()
    try:
        other_user_create = pydantic_models.UserCreate(username="otheruser", email="other@example.com", password="opassword")
        other_user = crud.create_user(db, other_user_create)
        other_char = crud.create_character(db, pydantic_models.CharacterCreate(name="Other's Char"), user_id=other_user.id)
        other_char_id = other_char.id
    finally:
        db.close()

    response_forbidden = await async_test_client.get(f"/api/v1/characters/{other_char_id}")
    assert response_forbidden.status_code == 403


@pytest.mark.asyncio
async def test_update_character_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User, test_user_orm: ORMUser):
    db = TestingSessionLocal()
    try:
        char = crud.create_character(db, pydantic_models.CharacterCreate(name="Update Me"), user_id=test_user_orm.id)
        char_id = char.id
    finally:
        db.close()

    update_payload = {"name": "Updated Name", "stats": {"wisdom": 15}}
    response = await async_test_client.put(f"/api/v1/characters/{char_id}", json=update_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["stats"]["wisdom"] == 15

@pytest.mark.asyncio
async def test_delete_character_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User, test_user_orm: ORMUser):
    db = TestingSessionLocal()
    try:
        char = crud.create_character(db, pydantic_models.CharacterCreate(name="Delete Me"), user_id=test_user_orm.id)
        char_id = char.id
    finally:
        db.close()

    response = await async_test_client.delete(f"/api/v1/characters/{char_id}")
    assert response.status_code == 200, response.text

    db = TestingSessionLocal()
    try:
        deleted_char_db = crud.get_character(db, char_id)
        assert deleted_char_db is None
    finally:
        db.close()

@pytest.mark.asyncio
async def test_link_and_unlink_character_campaign_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User, test_user_orm: ORMUser):
    db = TestingSessionLocal()
    try:
        # Create character
        char_create = pydantic_models.CharacterCreate(name="Linkable Char")
        char = crud.create_character(db, char_create, user_id=test_user_orm.id)
        char_id = char.id

        # Create campaign
        campaign_create = pydantic_models.CampaignCreate(title="Linkable Campaign")
        # crud.create_campaign is async, but we are calling it directly for setup
        # For test setup, if it's complex, consider a synchronous helper or direct ORM object creation
        # Here, let's assume a synchronous way or simplify by direct ORM creation for campaign setup
        campaign = ORMCampaign(title="Linkable Campaign", owner_id=test_user_orm.id)
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        campaign_id = campaign.id
    finally:
        db.close()

    # Link character to campaign
    response_link = await async_test_client.post(f"/api/v1/characters/{char_id}/campaigns/{campaign_id}")
    assert response_link.status_code == 200, response_link.text

    db = TestingSessionLocal()
    try:
        char_db = crud.get_character(db, char_id)
        assert any(c.id == campaign_id for c in char_db.campaigns)
    finally:
        db.close()

    # Get characters for campaign
    response_get_campaign_chars = await async_test_client.get(f"/api/v1/characters/campaign/{campaign_id}/characters")
    assert response_get_campaign_chars.status_code == 200, response_get_campaign_chars.text
    campaign_chars_data = response_get_campaign_chars.json()
    assert len(campaign_chars_data) == 1
    assert campaign_chars_data[0]["id"] == char_id

    # Unlink character from campaign
    response_unlink = await async_test_client.delete(f"/api/v1/characters/{char_id}/campaigns/{campaign_id}")
    assert response_unlink.status_code == 200, response_unlink.text

    db = TestingSessionLocal()
    try:
        char_db_after_unlink = crud.get_character(db, char_id)
        assert not any(c.id == campaign_id for c in char_db_after_unlink.campaigns)
    finally:
        db.close()

    # Get characters for campaign again (should be empty)
    response_get_empty_campaign_chars = await async_test_client.get(f"/api/v1/characters/campaign/{campaign_id}/characters")
    assert response_get_empty_campaign_chars.status_code == 200, response_get_empty_campaign_chars.text
    assert len(response_get_empty_campaign_chars.json()) == 0

    # Test linking with non-existent character
    response_char_not_found = await async_test_client.post(f"/api/v1/characters/999/campaigns/{campaign_id}")
    assert response_char_not_found.status_code == 404

    # Test linking with non-existent campaign
    response_camp_not_found = await async_test_client.post(f"/api/v1/characters/{char_id}/campaigns/999")
    assert response_camp_not_found.status_code == 404

    # Test linking character to campaign owned by another user
    db = TestingSessionLocal()
    try:
        other_user = crud.create_user(db, pydantic_models.UserCreate(username="otherlinker", email="ol@example.com", password="p"))
        other_campaign = ORMCampaign(title="Other User Linkable Campaign", owner_id=other_user.id)
        db.add(other_campaign)
        db.commit()
        db.refresh(other_campaign)
        other_campaign_id = other_campaign.id
    finally:
        db.close()

    response_link_other_campaign = await async_test_client.post(f"/api/v1/characters/{char_id}/campaigns/{other_campaign_id}")
    assert response_link_other_campaign.status_code == 403 # Forbidden, campaign belongs to other user

@pytest.mark.asyncio
async def test_read_character_campaigns_api(async_test_client: AsyncClient, authenticated_user_override: pydantic_models.User, test_user_orm: ORMUser):
    db = TestingSessionLocal()
    try:
        # Create a character
        char_create = pydantic_models.CharacterCreate(name="Campaign Explorer")
        char = crud.create_character(db, char_create, user_id=test_user_orm.id)
        char_id = char.id

        # Create a couple of campaigns for this user
        camp1_orm = ORMCampaign(title="Dungeon of Doom", owner_id=test_user_orm.id)
        camp2_orm = ORMCampaign(title="Skies of Arcadia", owner_id=test_user_orm.id)
        camp3_orm_other_user = ORMCampaign(title="Hidden Realm", owner_id=99) # Belongs to another user
        db.add_all([camp1_orm, camp2_orm, camp3_orm_other_user])
        db.commit()
        camp1_id = camp1_orm.id
        camp2_id = camp2_orm.id

        # Link character to two of their campaigns
        crud.add_character_to_campaign(db, char_id=char_id, campaign_id=camp1_id)
        crud.add_character_to_campaign(db, char_id=char_id, campaign_id=camp2_id)
    finally:
        db.close()

    # 1. Test getting campaigns for the character
    response = await async_test_client.get(f"/api/v1/characters/{char_id}/campaigns")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2
    campaign_titles = {c["title"] for c in data}
    assert "Dungeon of Doom" in campaign_titles
    assert "Skies of Arcadia" in campaign_titles

    # 2. Test with a character that has no campaigns
    db = TestingSessionLocal()
    try:
        lonely_char_create = pydantic_models.CharacterCreate(name="Solo Adventurer")
        lonely_char = crud.create_character(db, lonely_char_create, user_id=test_user_orm.id)
        lonely_char_id = lonely_char.id
    finally:
        db.close()

    response_lonely = await async_test_client.get(f"/api/v1/characters/{lonely_char_id}/campaigns")
    assert response_lonely.status_code == 200, response_lonely.text
    assert response_lonely.json() == []

    # 3. Test for non-existent character
    response_char_not_found = await async_test_client.get("/api/v1/characters/99999/campaigns")
    assert response_char_not_found.status_code == 404

    # 4. Test for character not owned by current user
    db = TestingSessionLocal()
    try:
        other_user = crud.create_user(db, pydantic_models.UserCreate(username="othercharowner", email="oco@example.com", password="p"))
        other_user_char = crud.create_character(db, pydantic_models.CharacterCreate(name="Secret Character"), user_id=other_user.id)
        other_user_char_id = other_user_char.id
        # Link this other character to a campaign (can be any campaign, even one owned by test_user_orm for this test, as we are testing access to char's campaigns)
        # camp_for_other_char = ORMCampaign(title="Other's Camp", owner_id=other_user.id) # or test_user_orm.id
        # db.add(camp_for_other_char); db.commit()
        # crud.add_character_to_campaign(db, other_user_char_id, camp_for_other_char.id)
    finally:
        db.close()

    response_forbidden = await async_test_client.get(f"/api/v1/characters/{other_user_char_id}/campaigns")
    assert response_forbidden.status_code == 403 # User cannot access campaigns of a character they don't own

@pytest.mark.asyncio
@patch('app.api.endpoints.characters.crud.get_llm_service') # Patch where get_llm_service is used
async def test_generate_character_llm_response_api(
    mock_get_llm_service: AsyncMock, # Use AsyncMock if get_llm_service itself is async or returns async obj
    async_test_client: AsyncClient,
    authenticated_user_override: pydantic_models.User,
    test_user_orm: ORMUser
):
    # Mock the LLM service instance and its method
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_character_response = AsyncMock(return_value="The character wisely says: 'Indeed.'")
    mock_get_llm_service.return_value = mock_llm_instance

    db = TestingSessionLocal()
    try:
        # Create a character with notes
        char_with_notes_create = pydantic_models.CharacterCreate(
            name="Sage Whispero",
            notes_for_llm="Very wise, speaks in riddles, loves tea."
        )
        char_with_notes = crud.create_character(db, char_with_notes_create, user_id=test_user_orm.id)
        char_with_notes_id = char_with_notes.id

        # Create a character without notes
        char_no_notes_create = pydantic_models.CharacterCreate(name="Silent Bob")
        char_no_notes = crud.create_character(db, char_no_notes_create, user_id=test_user_orm.id)
        char_no_notes_id = char_no_notes.id
    finally:
        db.close()

    request_payload = {
        "prompt": "What is the meaning of life?",
        "model_id_with_prefix": "openai/gpt-3.5-turbo" # Example
    }

    # 1. Test successful generation for character with notes
    response_success = await async_test_client.post(
        f"/api/v1/characters/{char_with_notes_id}/generate-response",
        json=request_payload
    )
    assert response_success.status_code == 200, response_success.text
    data_success = response_success.json()
    assert data_success["text"] == "The character wisely says: 'Indeed.'"

    mock_get_llm_service.assert_called_once() # Assuming get_llm_service is called once per request
    # Check args for generate_character_response
    # Note: current_user in generate_character_response is Pydantic model, db is Session
    # model in generate_character_response is the specific model_id, not prefixed.
    # provider_name in get_llm_service is "openai", model_id_with_prefix is "openai/gpt-3.5-turbo"

    # Extracting call arguments for get_llm_service
    get_llm_service_call_args = mock_get_llm_service.call_args
    assert get_llm_service_call_args is not None
    assert get_llm_service_call_args.kwargs['provider_name'] == 'openai'
    assert get_llm_service_call_args.kwargs['model_id_with_prefix'] == 'openai/gpt-3.5-turbo'

    # Extracting call arguments for generate_character_response
    generate_char_response_call_args = mock_llm_instance.generate_character_response.call_args
    assert generate_char_response_call_args is not None
    assert generate_char_response_call_args.kwargs['character_name'] == "Sage Whispero"
    assert generate_char_response_call_args.kwargs['character_notes'] == "Very wise, speaks in riddles, loves tea."
    assert generate_char_response_call_args.kwargs['user_prompt'] == "What is the meaning of life?"
    assert generate_char_response_call_args.kwargs['model'] == "gpt-3.5-turbo" # Model part
    assert generate_char_response_call_args.kwargs['current_user'].id == authenticated_user_override.id


    # Reset mocks for next call
    mock_get_llm_service.reset_mock()
    mock_llm_instance.generate_character_response.reset_mock()
    mock_get_llm_service.return_value = mock_llm_instance # Re-assign after reset

    # 2. Test successful generation for character without notes
    response_no_notes = await async_test_client.post(
        f"/api/v1/characters/{char_no_notes_id}/generate-response",
        json=request_payload
    )
    assert response_no_notes.status_code == 200, response_no_notes.text
    generate_char_response_call_args_no_notes = mock_llm_instance.generate_character_response.call_args
    assert generate_char_response_call_args_no_notes is not None
    assert generate_char_response_call_args_no_notes.kwargs['character_name'] == "Silent Bob"
    assert generate_char_response_call_args_no_notes.kwargs['character_notes'] == "" # Expect empty string

    # 3. Test with empty prompt
    empty_prompt_payload = {"prompt": "", "model_id_with_prefix": "openai/gpt-3.5-turbo"}
    response_empty_prompt = await async_test_client.post(
        f"/api/v1/characters/{char_with_notes_id}/generate-response",
        json=empty_prompt_payload
    )
    assert response_empty_prompt.status_code == 400

    # 4. Test for non-existent character
    response_char_not_found = await async_test_client.post(
        "/api/v1/characters/99999/generate-response",
        json=request_payload
    )
    assert response_char_not_found.status_code == 404

    # 5. Test for character not owned by user
    db = TestingSessionLocal()
    try:
        other_user = crud.create_user(db, pydantic_models.UserCreate(username="otherllmuser", email="ollm@example.com", password="p"))
        other_user_char = crud.create_character(db, pydantic_models.CharacterCreate(name="Private Character"), user_id=other_user.id)
        other_user_char_id = other_user_char.id
    finally:
        db.close()

    response_forbidden = await async_test_client.post(
        f"/api/v1/characters/{other_user_char_id}/generate-response",
        json=request_payload
    )
    assert response_forbidden.status_code == 403
