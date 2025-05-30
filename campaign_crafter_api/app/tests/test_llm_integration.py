# campaign_crafter_api/app/tests/test_llm_integration.py

import pytest
import os
from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError
from app.services.openai_service import OpenAILLMService # Specific service for this test
from app.core.config import settings # To check API key state
from app.services.llm_service import AbstractLLMService # For type hinting

# Mark for pytest to identify this as an integration test
pytestmark = pytest.mark.integration

@pytest.fixture(scope="module")
def openai_llm_service() -> AbstractLLMService | None:
    """
    Fixture to provide an instance of OpenAILLMService.
    It will only yield a service if the API key is configured.
    Tests using this fixture should handle the case where the service is None or raises an error.
    """
    # Ensure settings are loaded
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ["YOUR_OPENAI_API_KEY", "YOUR_API_KEY_HERE"]:
        pytest.skip("OpenAI API key not configured. Skipping OpenAI integration tests.")
        return None

    try:
        # Attempt to get the service specifically for "openai"
        service = get_llm_service(provider_name="openai")
        if not isinstance(service, OpenAILLMService):
             pytest.fail("Failed to get a specific OpenAILLMService instance from the factory for testing.")
        return service
    except LLMServiceUnavailableError as e:
        # This case might occur if the key is present but invalid, or service has other init issues
        pytest.skip(f"OpenAI LLM Service unavailable, skipping test: {e}")
        return None
    except Exception as e:
        # For any other unexpected error during service acquisition
        pytest.fail(f"Unexpected error getting OpenAI LLM service for testing: {e}")
        return None


def test_openai_hello_world(openai_llm_service: AbstractLLMService | None):
    """
    Tests a simple 'hello world' style call to the OpenAI LLM service.
    This is an integration test and requires a valid OpenAI API key.
    """
    if openai_llm_service is None:
        # This safeguard handles cases where the fixture might not have explicitly skipped
        # (e.g., if pytest.skip wasn't effective or an unexpected path led to None).
        pytest.skip("OpenAI LLM Service not available for testing (likely due to configuration or fixture error).")
        return # Ensure no further execution if service is None

    prompt = "Say 'Hello, World!' in a short, friendly tone."

    try:
        response = openai_llm_service.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo", # Specify a common, cost-effective model for this test
            max_tokens=50,       # Keep it short
            temperature=0.7
        )

        assert response is not None, "LLM response should not be None"
        assert isinstance(response, str), "LLM response should be a string"
        assert len(response.strip()) > 0, "LLM response should not be empty or just whitespace"
        # Optional: print for visibility when running tests with -s
        # print(f"OpenAI 'Hello, World!' test response: {response}")

    except LLMServiceUnavailableError:
        # This specific exception should ideally be caught by the fixture or service's own init.
        # If it reaches here, it means an active service instance threw it during generate_text,
        # which might indicate an intermittent issue or a problem not caught at setup.
        pytest.fail("LLMServiceUnavailableError occurred during the generate_text call unexpectedly.")
    except Exception as e:
        # Catch any other exception during the API call
        pytest.fail(f"OpenAI LLM call failed with an unexpected error: {type(e).__name__} - {e}")
