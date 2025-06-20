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

# Service and error imports
from app.services.llm_service import LLMService, LLMGenerationError, LLMServiceUnavailableError
from app.services.gemini_service import GeminiLLMService
from app.models import User as UserModel
from app.core.config import settings # Added import for settings

# Google GenAI SDK related imports (actual and for mocking)
# We will mock 'app.services.gemini_service.new_genai' for most tests
# For simulating errors, we might need direct access to exception types
try:
    from google.api_core import exceptions as google_api_exceptions
    # For creating mock responses or types, we might need these, but usually mocked via new_genai patch
    # from google.genai import types as google_types
except ImportError:
    # Define dummy exceptions if google.api_core is not available in test env (should be)
    class MockGoogleAPIError(Exception): pass
    google_api_exceptions = MagicMock()
    google_api_exceptions.PermissionDenied = type('PermissionDenied', (MockGoogleAPIError,), {})
    google_api_exceptions.InvalidArgument = type('InvalidArgument', (MockGoogleAPIError,), {})
    google_api_exceptions.APIError = MockGoogleAPIError # General API error

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

# --- GeminiLLMService Tests (New SDK) ---

# Helper to create a mock SdkModel object (as would be returned by new_genai client)
def create_mock_sdk_model(name: str, display_name: str, supported_generation_methods: list):
    mock_model = MagicMock()
    mock_model.name = name
    mock_model.display_name = display_name
    mock_model.supported_generation_methods = supported_generation_methods
    return mock_model

@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_llm_service_init_success_api_key(MockNewGenAIClient, mock_current_user, mock_db_session):
    """Tests successful client creation with API key when Vertex AI is False."""
    valid_api_key = "test_gemini_api_key"
    with patch.object(settings, 'GOOGLE_GENAI_USE_VERTEXAI', False), \
         patch.object(settings, 'GEMINI_API_KEY', valid_api_key):

        mock_client_instance = MagicMock()
        MockNewGenAIClient.return_value = mock_client_instance

        # Test with direct key
        service_direct_key = GeminiLLMService(api_key=valid_api_key)
        assert service_direct_key.configured_successfully is True
        assert service_direct_key.client == mock_client_instance
        MockNewGenAIClient.assert_called_once_with(api_key=valid_api_key)

        MockNewGenAIClient.reset_mock()
        # Test with system key (api_key=None to service constructor)
        service_system_key = GeminiLLMService(api_key=None)
        assert service_system_key.configured_successfully is True
        assert service_system_key.client == mock_client_instance
        MockNewGenAIClient.assert_called_once_with(api_key=valid_api_key)


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_llm_service_init_no_key_or_placeholder(MockNewGenAIClient, mock_current_user, mock_db_session):
    """Tests client creation failure if API key is missing or placeholder when Vertex AI is False."""
    with patch.object(settings, 'GOOGLE_GENAI_USE_VERTEXAI', False):
        # Scenario 1: No key provided to constructor, and system key is None
        with patch.object(settings, 'GEMINI_API_KEY', None):
            service_no_key = GeminiLLMService(api_key=None)
            assert service_no_key.configured_successfully is False
            assert service_no_key.client is None
            MockNewGenAIClient.assert_not_called()

        # Scenario 2: Placeholder key provided to constructor
        service_placeholder_direct = GeminiLLMService(api_key="YOUR_GEMINI_API_KEY")
        assert service_placeholder_direct.configured_successfully is False
        assert service_placeholder_direct.client is None
        MockNewGenAIClient.assert_not_called()

        # Scenario 3: No key provided to constructor, and system key is placeholder
        with patch.object(settings, 'GEMINI_API_KEY', "YOUR_GEMINI_API_KEY"):
            service_placeholder_system = GeminiLLMService(api_key=None)
            assert service_placeholder_system.configured_successfully is False
            assert service_placeholder_system.client is None
            MockNewGenAIClient.assert_not_called()

        # Scenario 4: Empty string API key
        with patch.object(settings, 'GEMINI_API_KEY', ""): # System key is empty
            service_empty_system = GeminiLLMService(api_key=None)
            assert service_empty_system.configured_successfully is False
            assert service_empty_system.client is None
            MockNewGenAIClient.assert_not_called()

        service_empty_direct = GeminiLLMService(api_key=" ") # Direct empty/whitespace key
        assert service_empty_direct.configured_successfully is False
        assert service_empty_direct.client is None
        MockNewGenAIClient.assert_not_called()


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_llm_service_init_vertex_ai_success(MockNewGenAIClient, mock_current_user, mock_db_session):
    """Tests successful client creation for Vertex AI."""
    with patch.object(settings, 'GOOGLE_GENAI_USE_VERTEXAI', True), \
         patch.object(settings, 'GOOGLE_CLOUD_PROJECT', "test-project-id"), \
         patch.object(settings, 'GOOGLE_CLOUD_LOCATION', "test-location"):

        mock_vertex_client_instance = MagicMock()
        MockNewGenAIClient.return_value = mock_vertex_client_instance

        service = GeminiLLMService(api_key=None) # API key should be ignored for Vertex AI path

        assert service.configured_successfully is True
        assert service.client == mock_vertex_client_instance
        MockNewGenAIClient.assert_called_once_with(
            vertexai=True,
            project="test-project-id",
            location="test-location"
        )

@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_llm_service_init_vertex_ai_missing_project(MockNewGenAIClient, mock_current_user, mock_db_session):
    """Tests Vertex AI init failure if GOOGLE_CLOUD_PROJECT is missing."""
    with patch.object(settings, 'GOOGLE_GENAI_USE_VERTEXAI', True), \
         patch.object(settings, 'GOOGLE_CLOUD_PROJECT', None), \
         patch.object(settings, 'GOOGLE_CLOUD_LOCATION', "test-location"):

        service = GeminiLLMService(api_key=None)

        assert service.configured_successfully is False
        assert service.client is None
        MockNewGenAIClient.assert_not_called()

@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_llm_service_init_vertex_ai_missing_location(MockNewGenAIClient, mock_current_user, mock_db_session):
    """Tests Vertex AI init failure if GOOGLE_CLOUD_LOCATION is missing."""
    with patch.object(settings, 'GOOGLE_GENAI_USE_VERTEXAI', True), \
         patch.object(settings, 'GOOGLE_CLOUD_PROJECT', "test-project-id"), \
         patch.object(settings, 'GOOGLE_CLOUD_LOCATION', None):

        service = GeminiLLMService(api_key=None)

        assert service.configured_successfully is False
        assert service.client is None
        MockNewGenAIClient.assert_not_called()

@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_llm_service_init_vertex_ai_client_exception(MockNewGenAIClient, mock_current_user, mock_db_session):
    """Tests Vertex AI init failure due to client instantiation exception."""
    with patch.object(settings, 'GOOGLE_GENAI_USE_VERTEXAI', True), \
         patch.object(settings, 'GOOGLE_CLOUD_PROJECT', "test-project-id"), \
         patch.object(settings, 'GOOGLE_CLOUD_LOCATION', "test-location"):

        MockNewGenAIClient.side_effect = Exception("Vertex AI Client Init Failed")

        service = GeminiLLMService(api_key=None)

        assert service.configured_successfully is False
        assert service.client is None
        MockNewGenAIClient.assert_called_once_with(
            vertexai=True,
            project="test-project-id",
            location="test-location"
        )


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_is_available_success(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests is_available returns True on successful API check."""
    # Arrange
    mock_aio_models = AsyncMock()
    mock_aio_models.list = AsyncMock() # Successfully returns (doesn't raise)

    mock_client_instance = MagicMock()
    mock_client_instance.aio.models = mock_aio_models
    mock_new_genai_client_constructor.return_value = mock_client_instance

    service = GeminiLLMService(api_key="fake_key") # Assume configured

    # Act
    available = await service.is_available(current_user=mock_current_user, db=mock_db_session)

    # Assert
    assert available is True
    mock_aio_models.list.assert_called_once_with(page_size=1)

@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_is_available_permission_denied(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests is_available returns False on PermissionDenied."""
    mock_aio_models = AsyncMock()
    mock_aio_models.list = AsyncMock(side_effect=google_api_exceptions.PermissionDenied("Test permission denied"))

    mock_client_instance = MagicMock()
    mock_client_instance.aio.models = mock_aio_models
    mock_new_genai_client_constructor.return_value = mock_client_instance

    service = GeminiLLMService(api_key="fake_key")
    available = await service.is_available(current_user=mock_current_user, db=mock_db_session)
    assert available is False

@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_is_available_api_error(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests is_available returns False on general APIError."""
    mock_aio_models = AsyncMock()
    # Assuming new_genai.errors.APIError exists and can be raised
    # If new_genai.errors is not directly importable for error types, use a generic Exception
    # or a more specific google.api_core.exceptions if that's what the SDK throws.
    # For now, let's use google_api_exceptions.APIError as a stand-in if new_genai.errors.APIError isn't easily mockable.
    mock_aio_models.list = AsyncMock(side_effect=google_api_exceptions.APIError("Test API error"))

    mock_client_instance = MagicMock()
    mock_client_instance.aio.models = mock_aio_models
    mock_new_genai_client_constructor.return_value = mock_client_instance

    service = GeminiLLMService(api_key="fake_key")
    available = await service.is_available(current_user=mock_current_user, db=mock_db_session)
    assert available is False


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_list_available_models_success(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests list_available_models successfully retrieves and maps models."""
    # Arrange
    mock_sdk_models_data = [
        create_mock_sdk_model("models/gemini-1.5-pro-latest", "Gemini 1.5 Pro", ["generateContent"]),
        create_mock_sdk_model("models/gemini-1.5-flash-latest", "Gemini 1.5 Flash", ["generateContent", "embedContent"]),
        create_mock_sdk_model("models/imagen-005", "Imagen 005", ["generateImages"]),
        create_mock_sdk_model("models/text-embedding-004", "Embedding Model 004", ["embedContent"]),
    ]

    # Mock the async iterator behavior for client.aio.models.list()
    async def mock_model_list_iterator():
        for model_data in mock_sdk_models_data:
            yield model_data

    mock_aio_models_client = AsyncMock()
    mock_aio_models_client.list = MagicMock(return_value=mock_model_list_iterator()) # Return the async generator

    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.aio.models = mock_aio_models_client
    mock_new_genai_client_constructor.return_value = mock_genai_client_instance

    service = GeminiLLMService(api_key="fake_key")
    service.is_available = AsyncMock(return_value=True) # Ensure service is considered available

    # Act
    models_list = await service.list_available_models(current_user=mock_current_user, db=mock_db_session)

    # Assert
    assert len(models_list) == 4

    gemini_pro = next(m for m in models_list if m["id"] == "gemini-1.5-pro-latest")
    assert gemini_pro["name"] == "Gemini 1.5 Pro"
    assert gemini_pro["model_type"] == "chat"
    assert "chat" in gemini_pro["capabilities"]
    assert gemini_pro["provider"] == "gemini"

    imagen = next(m for m in models_list if m["id"] == "imagen-005")
    assert imagen["name"] == "Imagen 005"
    assert imagen["model_type"] == "image"
    assert "image_generation" in imagen["capabilities"]

    embedding_model = next(m for m in models_list if m["id"] == "text-embedding-004")
    assert "embedding" in embedding_model["capabilities"]
    # Model type for embedding only might be 'chat' or 'other' depending on definition, check service logic
    # Current logic: model_type = "image" if "image_generation" in capabilities else "chat"
    # So, an embedding-only model would be "chat". This might need refinement.
    assert embedding_model["model_type"] == "chat"


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_generate_text_success(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests successful text generation."""
    # Arrange
    mock_aio_models_client = AsyncMock()
    mock_generate_content_response = MagicMock(text="Generated text from Gemini")
    mock_aio_models_client.generate_content = AsyncMock(return_value=mock_generate_content_response)

    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.aio.models = mock_aio_models_client
    mock_new_genai_client_constructor.return_value = mock_genai_client_instance

    service = GeminiLLMService(api_key="fake_key")
    service.is_available = AsyncMock(return_value=True)

    prompt = "Tell me a story."
    model_id = "gemini-1.5-flash-latest" # Short ID

    # Act
    # Ensure google_types.GenerationConfig can be instantiated or is also mocked if needed
    # For this test, we can assume it's fine or pass None for config if generate_text handles it.
    # The service creates GenerationConfig internally.
    with patch('app.services.gemini_service.google_types.GenerationConfig') as mock_google_types_gen_config:
        mock_config_instance = MagicMock()
        mock_google_types_gen_config.return_value = mock_config_instance

        generated_text = await service.generate_text(
            prompt=prompt,
            current_user=mock_current_user,
            db=mock_db_session,
            model=model_id,
            temperature=0.5,
            max_tokens=100
        )

        # Assert
        assert generated_text == "Generated text from Gemini"
        mock_aio_models_client.generate_content.assert_called_once_with(
            model=f"models/{model_id}",
            contents=[prompt],
            generation_config=mock_config_instance # Check that the config object was passed
        )
        mock_google_types_gen_config.assert_called_once_with(temperature=0.5, max_output_tokens=100)


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_generate_text_api_error(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests text generation failure due to API error."""
    mock_aio_models_client = AsyncMock()
    mock_aio_models_client.generate_content = AsyncMock(side_effect=google_api_exceptions.APIError("LLM Error"))

    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.aio.models = mock_aio_models_client
    mock_new_genai_client_constructor.return_value = mock_genai_client_instance

    service = GeminiLLMService(api_key="fake_key")
    service.is_available = AsyncMock(return_value=True)

    with pytest.raises(LLMServiceUnavailableError, match="Failed to generate text with Gemini model models/gemini-1.5-flash-latest due to API error: LLM Error"):
        await service.generate_text("A prompt", mock_current_user, mock_db_session, model="gemini-1.5-flash-latest")


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_generate_image_success_imagen(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests successful image generation with Imagen model via GeminiLLMService."""
    # Arrange
    mock_aio_models_client = AsyncMock()

    # Mock the structure for generate_images response
    # Assuming the response has 'generated_images' list, and each item has '_image_bytes'
    mock_image_object = MagicMock()
    mock_image_object._image_bytes = b"test_imagen_bytes"
    mock_generate_images_response = MagicMock(generated_images=[mock_image_object])
    mock_aio_models_client.generate_images = AsyncMock(return_value=mock_generate_images_response)

    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.aio.models = mock_aio_models_client
    mock_new_genai_client_constructor.return_value = mock_genai_client_instance

    service = GeminiLLMService(api_key="fake_key")
    service.is_available = AsyncMock(return_value=True)

    prompt = "A futuristic city"
    model_id = "imagen-005" # Short ID for an Imagen model

    # Act
    image_bytes = await service.generate_image(
        prompt=prompt,
        current_user=mock_current_user,
        db=mock_db_session,
        model=model_id
    )

    # Assert
    assert image_bytes == b"test_imagen_bytes"
    mock_aio_models_client.generate_images.assert_called_once_with(
        model=f"models/{model_id}",
        prompt=prompt
        # config is not passed in current service.generate_image implementation
    )


@pytest.mark.asyncio
@patch('app.services.gemini_service.new_genai.Client')
async def test_gemini_generate_image_api_error_imagen(mock_new_genai_client_constructor, mock_current_user, mock_db_session):
    """Tests Imagen image generation failure due to API error."""
    mock_aio_models_client = AsyncMock()
    mock_aio_models_client.generate_images = AsyncMock(side_effect=google_api_exceptions.APIError("Imagen LLM Error"))

    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.aio.models = mock_aio_models_client
    mock_new_genai_client_constructor.return_value = mock_genai_client_instance

    service = GeminiLLMService(api_key="fake_key")
    service.is_available = AsyncMock(return_value=True)

    with pytest.raises(LLMGenerationError, match="Failed to generate image with Imagen model models/imagen-005: Imagen LLM Error"):
        await service.generate_image("A prompt for Imagen", mock_current_user, mock_db_session, model="imagen-005")


@pytest.mark.asyncio
async def test_generate_homebrewery_toc_from_sections_none_summary(llm_service: LLMService, mock_db_session: Session, mock_current_user: UserModel):
    summary = None # Intentionally None
    homebrewery_toc = await llm_service.generate_homebrewery_toc_from_sections(
        sections_summary=summary, # Pass None directly
        db=mock_db_session,
        current_user=mock_current_user
    )
    assert homebrewery_toc == ""
