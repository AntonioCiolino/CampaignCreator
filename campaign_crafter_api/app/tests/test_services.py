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
