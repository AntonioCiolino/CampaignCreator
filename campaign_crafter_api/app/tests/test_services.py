import unittest
from app.services.random_table_service import RandomTableService
from app import models
import pydantic

# New imports for the pytest async test
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session # Assuming this is needed for db_mock spec

from app.services.openai_service import OpenAILLMService
# FeaturePromptService is patched where it's looked up ('app.services.openai_service.FeaturePromptService')
# from app.services.feature_prompt_service import FeaturePromptService # Not directly used in test
from app.services.llm_service import LLMServiceUnavailableError
from app.services.export_service import HomebreweryExportService
from app.orm_models import Campaign


class TestServices(unittest.TestCase):
    def test_random_table_service_instantiation(self):
        """Tests if RandomTableService can be instantiated."""
        try:
            service = RandomTableService()
            self.assertIsInstance(service, RandomTableService)
        except Exception as e:
            self.fail(f"RandomTableService instantiation failed: {e}")

    def test_pydantic_model_config_from_attributes(self):
        """
        Tests if Pydantic models in app.models have from_attributes = True in their Config.
        """
        for name, obj in vars(models).items():
            # Check if obj is a class and a subclass of pydantic.BaseModel
            if isinstance(obj, type) and issubclass(obj, pydantic.BaseModel) and obj != pydantic.BaseModel:
                # Check if the model has a Config class
                if hasattr(obj, 'Config'):
                    config = obj.Config
                    # Check for from_attributes = True
                    self.assertTrue(
                        getattr(config, 'from_attributes', False),
                        f"Model {name} does not have from_attributes = True in its Config."
                    )
                else:
                    # This case could be a fail or a pass depending on requirements.
                    # If all models are expected to have a Config with from_attributes,
                    # then this should be a self.fail().
                    # For now, we'll assume models without Config are fine or handled elsewhere.
                    print(f"Model {name} does not have a Config class. Skipping from_attributes check.")

    def test_format_campaign_for_homebrewery_with_list_toc(self):
        """
        Tests HomebreweryExportService.format_campaign_for_homebrewery
        with homebrewery_toc as a list.
        """
        service = HomebreweryExportService()

        # Create a Campaign object with necessary fields
        # Based on orm_models.py: title is mandatory.
        # homebrewery_toc is what we're testing with a list.
        # concept is optional. owner_id is not directly relevant for formatting logic.
        campaign = Campaign(
            title="Test Campaign for List TOC",
            concept="A concept for testing list TOC.",
            homebrewery_toc=[
                "Table of Contents:",
                "* Chapter 1: Introduction",
                "* Chapter 2: The Adventure Begins",
                "Section 1: Deeper Dive"
            ]
            # owner_id can be omitted or set to None if model allows for this test context
        )

        sections = [] # No sections needed for this specific TOC test

        try:
            output = service.format_campaign_for_homebrewery(campaign, sections)

            self.assertIsInstance(output, str)
            self.assertIn("# Test Campaign for List TOC", output) # Title
            self.assertIn("## Campaign Overview", output) # From concept
            self.assertIn("A concept for testing list TOC.", output) # Concept text
            self.assertIn("{{toc,wide,frame,box}}", output) # TOC tag
            self.assertIn("- Chapter 1: Introduction", output) # Processed TOC item
            self.assertIn("- Chapter 2: The Adventure Begins", output) # Processed TOC item
            self.assertIn("Section 1: Deeper Dive", output) # Processed TOC item (heading not applied due to early return)

        except Exception as e:
            self.fail(f"format_campaign_for_homebrewery raised an exception: {e}")

# New pytest async test function
@pytest.mark.asyncio
async def test_generate_toc_prompt_formatting():
    # Arrange
    db_mock = MagicMock(spec=Session)
    campaign_concept_test = "A space opera adventure."
    # This is the template *returned by the mocked FeaturePromptService*
    expected_toc_template_from_fps = "TOC for concept: {campaign_concept}. Be creative."

    # Mock FeaturePromptService instance and its get_prompt method
    # This mock_fps_instance will be returned when FeaturePromptService is instantiated
    # within OpenAILLMService thanks to the patch below.
    mock_fps_instance = MagicMock()
    mock_fps_instance.get_prompt.return_value = expected_toc_template_from_fps

    # Patch 'app.services.openai_service.FeaturePromptService'
    # This ensures that when OpenAILLMService creates an instance of FeaturePromptService,
    # it gets our mock_fps_instance.
    with patch('app.services.openai_service.FeaturePromptService', return_value=mock_fps_instance) as mock_fps_class_constructor:
        openai_service = OpenAILLMService() # Instantiating this will use the patched FeaturePromptService

        # Mock other methods on the instance of OpenAILLMService as needed
        openai_service.is_available = AsyncMock(return_value=True) # Ensure service is "available"
        # Mock the actual chat completion call to avoid external API calls
        openai_service._perform_chat_completion = AsyncMock(return_value="Mocked TOC output from LLM")

        # Act
        # Call the method under test
        await openai_service.generate_toc(campaign_concept=campaign_concept_test, db=db_mock, model="gpt-test-model")

        # Assert
        # 1. Verify that FeaturePromptService's get_prompt method was called correctly
        mock_fps_instance.get_prompt.assert_called_once_with("Table of Contents", db=db_mock)

        # 2. Verify that _perform_chat_completion was called with the correctly formatted prompt
        openai_service._perform_chat_completion.assert_called_once()

        # Get the arguments passed to _perform_chat_completion
        # call_args is a tuple. args is call_args[0], kwargs is call_args[1]
        # The signature of _perform_chat_completion is (self, selected_model, messages, temperature, max_tokens)
        # When called as an instance method, 'self' is bound.
        # So, call_args.args will be (selected_model, messages, temperature, max_tokens)
        call_args_tuple = openai_service._perform_chat_completion.call_args

        passed_model_arg = call_args_tuple.args[0]
        passed_messages_arg = call_args_tuple.args[1]
        # temperature = call_args_tuple.args[2]
        # max_tokens = call_args_tuple.args[3]

        assert passed_model_arg == "gpt-test-model"

        # Verify the structure and content of the messages
        assert len(passed_messages_arg) == 2 # Expecting a system message and a user message

        system_message = next((msg for msg in passed_messages_arg if msg["role"] == "system"), None)
        user_message = next((msg for msg in passed_messages_arg if msg["role"] == "user"), None)

        assert system_message is not None, "System message was not found in chat completion."
        # Could add assertion for system_message["content"] if it's static or important for this test
        assert user_message is not None, "User message was not found in chat completion."

        # The user message content should be the template from FPS, formatted with the campaign_concept
        expected_final_user_prompt = expected_toc_template_from_fps.format(campaign_concept=campaign_concept_test)
        assert user_message["content"] == expected_final_user_prompt

# --- RandomTableService Tests ---

@pytest.fixture
def db_mock() -> MagicMock:
    return MagicMock(spec=Session)

@pytest.fixture
def random_table_service() -> RandomTableService:
    return RandomTableService() # Instantiate the service

# --- HomebreweryExportService Tests ---

@pytest.mark.asyncio
async def test_format_campaign_for_homebrewery_front_cover_content():
    """Tests that the front cover is correctly formatted and included."""
    service = HomebreweryExportService()

    # Mock campaign object
    campaign_mock = MagicMock(spec=Campaign)
    campaign_mock.title = "My Test Campaign"
    campaign_mock.concept = "A thrilling adventure."
    campaign_mock.homebrewery_toc = None
    campaign_mock.selected_llm_id = None # Not strictly needed for this part of the test

    # Mocks for db and current_user
    db_mock = MagicMock(spec=Session)
    user_mock = MagicMock() # Spec can be added if specific user attributes are accessed

    output = await service.format_campaign_for_homebrewery(campaign_mock, [], db_mock, user_mock)

    # Construct expected front cover string
    # Note: FRONT_COVER_TEMPLATE already includes the trailing "\n\\page"
    expected_front_cover = service.FRONT_COVER_TEMPLATE
    expected_front_cover = expected_front_cover.replace("TITLE", "My Test Campaign")
    expected_front_cover = expected_front_cover.replace("SUBTITLE", "A Campaign Adventure")
    expected_front_cover = expected_front_cover.replace("BANNER_TEXT", "Exciting Banner Text!")
    expected_front_cover = expected_front_cover.replace("EPISODE_INFO", "Author to provide episode details here.")
    # The background image URL in the template is the onedrive one, it's replaced by the service method
    expected_front_cover = expected_front_cover.replace("https://onedrive.live.com/embed?resid=387fb00e5a1e24c8%2152521&authkey=%21APkOXzEAywQMAwA", "https://via.placeholder.com/816x1056.png?text=Front+Cover+Background")

    # The output is a join of many parts. The first part should be the formatted front cover.
    # The `\n\n` joiner in the service means we should check if output starts with expected_front_cover + "\n\n"
    # However, if it's the only content before style, it might be just expected_front_cover
    # Let's check if the output starts with the fully formatted front cover.
    # The front_cover is added to homebrewery_content list, then other things, then joined by "\n\n"
    # So, the actual output will start with expected_front_cover, then "\n\n", then "<style>..."
    assert output.startswith(expected_front_cover)

    # Verify other key elements are still present if startswith is too broad or tricky due to joining
    assert "# My Test Campaign" in output
    assert "## A Campaign Adventure" in output
    assert "{{banner Exciting Banner Text!}}" in output
    assert "Author to provide episode details here." in output
    assert "![background image](https://via.placeholder.com/816x1056.png?text=Front+Cover+Background)" in output
    assert "![](/assets/naturalCritLogoRed.svg)" in output
    assert expected_front_cover.strip().endswith("\\page")


@pytest.mark.asyncio
async def test_format_campaign_for_homebrewery_back_cover_content():
    """Tests that the back cover is correctly formatted and included."""
    service = HomebreweryExportService()

    # Mock campaign object
    campaign_mock = MagicMock(spec=Campaign)
    campaign_mock.title = "Another Test Campaign"
    campaign_mock.concept = "Another epic journey."
    campaign_mock.homebrewery_toc = None
    campaign_mock.selected_llm_id = None

    # Mocks for db and current_user
    db_mock = MagicMock(spec=Session)
    user_mock = MagicMock()

    output = await service.format_campaign_for_homebrewery(campaign_mock, [], db_mock, user_mock)

    # Construct expected back cover string
    expected_back_cover = service.BACK_COVER_TEMPLATE
    expected_back_cover = expected_back_cover.replace("https://--backcover url image--", "https://via.placeholder.com/816x1056.png?text=Back+Cover+Background")
    expected_back_cover = expected_back_cover.replace("BACKCOVER ONE-LINER", "An Unforgettable Adventure Awaits!")
    expected_back_cover = expected_back_cover.replace("ADD A CAMPAIGN COMMENTARY BLOCK HERE", "Author's notes and commentary on the campaign.")

    # The back_cover is the last element appended to homebrewery_content, then joined by "\n\n"
    # So the output, when stripped of any final whitespace from the join, should end with the expected_back_cover.
    assert output.strip().endswith(expected_back_cover.strip())

    # Keep some specific checks for key elements to be sure
    assert "\\page\n{{backCover}}" in output # This is how BACK_COVER_TEMPLATE starts
    assert "![background image](https://via.placeholder.com/816x1056.png?text=Back+Cover+Background)" in output
    assert "# An Unforgettable Adventure Awaits!" in output
    assert "Author's notes and commentary on the campaign." in output
    assert "![](/assets/naturalCritLogoWhite.svg)" in output
    assert "VTCNP Enterprises" in output # Part of the logo block


def test_service_get_available_table_names_user_priority(random_table_service: RandomTableService, db_mock: MagicMock):
    # Arrange
    user_id = 1
    system_table_same_name = MagicMock(spec=models.RollTable) # Using models.RollTable as per service type hint
    system_table_same_name.name = "Duplicate Name Table"
    system_table_same_name.user_id = None

    user_table_same_name = MagicMock(spec=models.RollTable)
    user_table_same_name.name = "Duplicate Name Table"
    user_table_same_name.user_id = user_id

    another_system_table = MagicMock(spec=models.RollTable)
    another_system_table.name = "Unique System Table"
    another_system_table.user_id = None

    # Mock crud.get_roll_tables to return these tables
    # The service sorts, so the order here shouldn't strictly matter for the test outcome,
    # but good to have user table after system table with same name to test prioritization.
    mock_tables_from_crud = [system_table_same_name, user_table_same_name, another_system_table]

    with patch('app.crud.get_roll_tables', return_value=mock_tables_from_crud) as mock_crud_get_tables:
        # Act
        available_names = random_table_service.get_available_table_names(db=db_mock, user_id=user_id)

        # Assert
        mock_crud_get_tables.assert_called_once_with(db=db_mock, limit=1000, user_id=user_id)

        # Check that "Duplicate Name Table" appears only once
        assert available_names.count("Duplicate Name Table") == 1
        # Check that "Unique System Table" is also present
        assert "Unique System Table" in available_names
        # Total unique names
        assert len(available_names) == 2
        # Ensure the order is not implicitly tested if not guaranteed by the function
        assert set(available_names) == {"Duplicate Name Table", "Unique System Table"}


def test_service_get_random_item_from_table_user_priority(random_table_service: RandomTableService, db_mock: MagicMock):
    # Arrange
    user_id = 1
    table_name = "TestTable"

    # This mock will simulate that the user's table is found and returned by CRUD
    mock_user_table = MagicMock(spec=models.RollTable) # Assuming crud returns ORM model, service handles it
    mock_user_table.name = table_name
    mock_user_table.user_id = user_id
    mock_user_table.description = "d10" # Example for dice roll logic

    # Define some items for the mock table
    item1 = MagicMock()
    item1.min_roll = 1
    item1.max_roll = 5
    item1.description = "User Item A"

    item2 = MagicMock()
    item2.min_roll = 6
    item2.max_roll = 10
    item2.description = "User Item B"
    mock_user_table.items = [item1, item2]

    with patch('app.crud.get_roll_table_by_name', return_value=mock_user_table) as mock_crud_get_by_name:
        # Act
        # We don't need to check the random selection logic here, just that it called the right crud method
        # and would operate on the user's table.
        # To make the test deterministic for item selection, we could mock random.randint
        with patch('random.randint', return_value=3) as mock_randint: # Simulate rolling a 3
            item_description = random_table_service.get_random_item_from_table(
                table_name=table_name, db=db_mock, user_id=user_id
            )

            # Assert
            # Check that crud.get_roll_table_by_name was called with user_id
            mock_crud_get_by_name.assert_called_once_with(db=db_mock, name=table_name, user_id=user_id)
            mock_randint.assert_called_once_with(1, 10) # Based on "d10" description
            assert item_description == "User Item A" # Item for roll 3

# if __name__ == '__main__':
#     unittest.main() # Keep if other unittest tests are still relevant
# Pytest will discover tests without this, so it can be removed if fully on pytest

# Added imports for LLMService tests
import pytest # This was already imported above, but ensure it's available contextually
from sqlalchemy.orm import Session # This was already imported above
from unittest.mock import MagicMock, AsyncMock, patch # Ensure all mock types are available
from app.services.llm_service import LLMService, LLMGenerationError, LLMServiceUnavailableError # LLMService is new here, added LLMServiceUnavailableError
from app.models import User as UserModel # UserModel is new here
from app.services.gemini_service import GeminiLLMService # Import GeminiLLMService
import google.generativeai as genai # To mock the genai module

# Fixtures for LLMService tests
@pytest.fixture
def llm_service():
    return LLMService()

@pytest.fixture
def mock_db_session(): # Renamed from db_mock to avoid conflict if it's used differently elsewhere
    return MagicMock(spec=Session)

@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=UserModel)
    user.id = 1
    return user

# Tests for LLMService
@pytest.mark.asyncio
async def test_generate_toc_dummy_service(llm_service: LLMService, mock_db_session: Session, mock_current_user: UserModel):
    concept = "A heroic fantasy adventure"
    toc_list = await llm_service.generate_toc(
        campaign_concept=concept,
        db=mock_db_session,
        current_user=mock_current_user
    )
    assert isinstance(toc_list, list)
    assert len(toc_list) > 0
    for item in toc_list:
        assert "title" in item
        assert "type" in item
    # Check content of the first item as generated by the dummy service
    assert toc_list[0]["title"] == f"Dummy Section 1 for {concept}"
    assert toc_list[0]["type"] == "generic"

@pytest.mark.asyncio
async def test_generate_homebrewery_toc_from_sections_with_summary(llm_service: LLMService, mock_db_session: Session, mock_current_user: UserModel):
    summary = "Section 1; Section 2"
    homebrewery_toc = await llm_service.generate_homebrewery_toc_from_sections(
        sections_summary=summary,
        db=mock_db_session,
        current_user=mock_current_user
    )
    assert homebrewery_toc == f"Dummy Homebrewery TOC based on sections: {summary}"

@pytest.mark.asyncio
async def test_generate_homebrewery_toc_from_sections_empty_summary(llm_service: LLMService, mock_db_session: Session, mock_current_user: UserModel):
    summary = ""
    homebrewery_toc = await llm_service.generate_homebrewery_toc_from_sections(
        sections_summary=summary,
        db=mock_db_session,
        current_user=mock_current_user
    )
    assert homebrewery_toc == ""


# --- GeminiLLMService Tests ---

@pytest.mark.asyncio
@patch('app.services.gemini_service.genai.GenerativeModel')
async def test_gemini_generate_image_success(mock_generative_model_class, mock_db_session, mock_current_user):
    """Tests successful image generation with GeminiLLMService."""
    # Arrange
    mock_gemini_service = GeminiLLMService()
    mock_gemini_service.is_available = AsyncMock(return_value=True)

    # Configure the mock for the genai.GenerativeModel instance
    mock_model_instance = AsyncMock() # The model instance itself needs to be an AsyncMock if its methods are async

    # Mock the response structure from generate_content_async
    mock_response_part = MagicMock()
    mock_response_part.inline_data.data = b"test_image_bytes"
    mock_response_part.inline_data.mime_type = "image/png"

    mock_gemini_response = MagicMock()
    mock_gemini_response.parts = [mock_response_part]

    mock_model_instance.generate_content_async = AsyncMock(return_value=mock_gemini_response)

    # Patch _get_model_instance to return our fine-tuned mock_model_instance
    # This is often cleaner than patching the class constructor if you only need to control the instance
    # returned by a specific method within your service.
    with patch.object(mock_gemini_service, '_get_model_instance', return_value=mock_model_instance) as mock_get_model:
        prompt = "A beautiful sunset"
        model_name = "gemini-pro-vision"

        # Act
        image_bytes = await mock_gemini_service.generate_image(
            prompt=prompt,
            current_user=mock_current_user,
            db=mock_db_session,
            model=model_name
        )

        # Assert
        mock_get_model.assert_called_once_with(model_id=model_name)
        mock_model_instance.generate_content_async.assert_called_once_with(prompt)
        assert image_bytes == b"test_image_bytes"

@pytest.mark.asyncio
async def test_gemini_generate_image_service_unavailable(mock_db_session, mock_current_user):
    """Tests generate_image when the Gemini service is unavailable."""
    # Arrange
    mock_gemini_service = GeminiLLMService()
    mock_gemini_service.is_available = AsyncMock(return_value=False)

    prompt = "A beautiful sunset"

    # Act & Assert
    with pytest.raises(LLMServiceUnavailableError, match="Gemini service is not available."):
        await mock_gemini_service.generate_image(
            prompt=prompt,
            current_user=mock_current_user,
            db=mock_db_session
        )
    mock_gemini_service.is_available.assert_called_once_with(current_user=mock_current_user, db=mock_db_session)


@pytest.mark.asyncio
@patch('app.services.gemini_service.genai.GenerativeModel')
async def test_gemini_generate_image_no_image_data(mock_generative_model_class, mock_db_session, mock_current_user):
    """Tests generate_image when the API returns no image data."""
    # Arrange
    mock_gemini_service = GeminiLLMService()
    mock_gemini_service.is_available = AsyncMock(return_value=True)

    mock_model_instance = AsyncMock()
    mock_gemini_response = MagicMock()
    mock_gemini_response.parts = [] # No parts, or parts without inline_data
    mock_gemini_response.prompt_feedback = None # No feedback
    mock_gemini_response.candidates = [] # No candidates

    mock_model_instance.generate_content_async = AsyncMock(return_value=mock_gemini_response)

    with patch.object(mock_gemini_service, '_get_model_instance', return_value=mock_model_instance):
        prompt = "A beautiful sunset"

        # Act & Assert
        with pytest.raises(LLMGenerationError, match="Gemini API call for image generation succeeded but returned no image data."):
            await mock_gemini_service.generate_image(
                prompt=prompt,
                current_user=mock_current_user,
                db=mock_db_session
            )

@pytest.mark.asyncio
@patch('app.services.gemini_service.genai.GenerativeModel')
async def test_gemini_generate_image_api_exception(mock_generative_model_class, mock_db_session, mock_current_user):
    """Tests generate_image when the Gemini API call raises an exception."""
    # Arrange
    mock_gemini_service = GeminiLLMService()
    mock_gemini_service.is_available = AsyncMock(return_value=True)

    mock_model_instance = AsyncMock()
    mock_model_instance.generate_content_async = AsyncMock(side_effect=Exception("Gemini API Error"))

    with patch.object(mock_gemini_service, '_get_model_instance', return_value=mock_model_instance):
        prompt = "A beautiful sunset"

        # Act & Assert
        with pytest.raises(LLMGenerationError, match="Failed to generate image with Gemini model gemini-pro-vision: Gemini API Error"):
            await mock_gemini_service.generate_image(
                prompt=prompt,
                current_user=mock_current_user,
                db=mock_db_session,
                model="gemini-pro-vision" # Explicitly pass model for error message check
            )

@pytest.mark.asyncio
async def test_generate_homebrewery_toc_from_sections_none_summary(llm_service: LLMService, mock_db_session: Session, mock_current_user: UserModel):
    summary = None # Intentionally None
    homebrewery_toc = await llm_service.generate_homebrewery_toc_from_sections(
        sections_summary=summary, # Pass None directly
        db=mock_db_session,
        current_user=mock_current_user
    )
    assert homebrewery_toc == ""
