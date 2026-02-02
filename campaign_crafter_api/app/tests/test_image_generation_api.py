from fastapi import HTTPException
import pytest
from unittest.mock import AsyncMock, MagicMock 

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.image_generation_service import ImageGenerationService
from app.db import get_db
from app.api.endpoints.image_generation import get_image_generation_service
from app.services.auth_service import get_current_active_user
from app.models import User as UserModel

# --- Test Client Fixture ---
@pytest.fixture(scope="module")
def client():
    return TestClient(app)

# --- Mock User Fixture ---
@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=UserModel)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_superuser = False
    user.sd_engine_preference = "automatic1111"
    return user

# --- Mock ImageGenerationService Fixture ---
@pytest.fixture
def mock_image_service():
    service_mock = MagicMock(spec=ImageGenerationService)
    # Configure async methods on the mock
    service_mock.generate_image_dalle = AsyncMock()
    service_mock.generate_image_stable_diffusion = AsyncMock()
    service_mock.generate_image_gemini = AsyncMock()
    return service_mock

# --- Mock DB Session Fixture ---
@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

# --- Override Dependency ---
@pytest.fixture(autouse=True)
def override_dependencies(mock_image_service, mock_current_user, mock_db):
    app.dependency_overrides[get_image_generation_service] = lambda: mock_image_service
    app.dependency_overrides[get_current_active_user] = lambda: mock_current_user
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

# --- API Tests ---
def test_generate_image_dalle_success(client, mock_image_service):
    expected_url = "http://example.com/generated_dalle_image.png"
    mock_image_service.generate_image_dalle.return_value = expected_url

    response = client.post(
        "/api/v1/images/generate",
        json={"prompt": "A white cat on a red carpet", "model": "dall-e", "size": "1024x1024"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] == expected_url
    assert data["prompt_used"] == "A white cat on a red carpet"
    assert data["model_used"] == "dall-e"
    assert data["size_used"] == "1024x1024"
    
    mock_image_service.generate_image_dalle.assert_called_once()


def test_generate_image_stable_diffusion_success(client, mock_image_service):
    expected_url = "http://example.com/generated_sd_image.png"
    mock_image_service.generate_image_stable_diffusion.return_value = expected_url

    response = client.post(
        "/api/v1/images/generate",
        json={
            "prompt": "A futuristic city skyline", 
            "model": "stable-diffusion", 
            "size": "512x512",
            "steps": 30,
            "cfg_scale": 7.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] == expected_url
    assert data["prompt_used"] == "A futuristic city skyline"
    assert data["model_used"] == "stable-diffusion"
    assert data["size_used"] == "512x512"
    assert data["steps_used"] == 30
    assert data["cfg_scale_used"] == 7.0

    mock_image_service.generate_image_stable_diffusion.assert_called_once()

def test_generate_image_gemini_success(client, mock_image_service):
    expected_url = "http://example.com/generated_gemini_image.png"
    mock_image_service.generate_image_gemini.return_value = expected_url

    test_prompt = "A magical forest scene with Gemini"
    test_gemini_model = "gemini-pro-vision"

    response = client.post(
        "/api/v1/images/generate",
        json={
            "prompt": test_prompt,
            "model": "gemini",
            "gemini_model_name": test_gemini_model,
            "size": "1024x1024" # Conceptual size for Gemini
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] == expected_url
    assert data["prompt_used"] == test_prompt
    assert data["model_used"] == "gemini"
    assert data["gemini_model_name_used"] == test_gemini_model
    assert data["size_used"] == "1024x1024" # As passed in request, used for logging by service

    mock_image_service.generate_image_gemini.assert_called_once()
    # Check arguments passed to the service method
    called_args_kwargs = mock_image_service.generate_image_gemini.call_args
    assert called_args_kwargs.kwargs['prompt'] == test_prompt
    assert called_args_kwargs.kwargs['model'] == test_gemini_model # Endpoint passes gemini_model_name as 'model' to service
    assert called_args_kwargs.kwargs['size'] == "1024x1024"
    # current_user and db are passed by Depends, not directly asserted here unless crucial for a specific test logic flow.

def test_generate_image_gemini_service_exception(client, mock_image_service):
    mock_image_service.generate_image_gemini.side_effect = HTTPException(status_code=503, detail="Gemini service is overloaded")

    response = client.post(
        "/api/v1/images/generate",
        json={"prompt": "test gemini failure", "model": "gemini", "gemini_model_name": "gemini-pro-vision"}
    )
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Gemini service is overloaded"
    mock_image_service.generate_image_gemini.assert_called_once()


def test_generate_image_missing_prompt(client):
    response = client.post(
        "/api/v1/images/generate",
        json={"model": "dall-e"} # Prompt is missing
    )
    assert response.status_code == 422 # FastAPI's Unprocessable Entity for validation errors
    data = response.json()
    assert "detail" in data
    # Example check, structure might vary slightly based on FastAPI version
    assert any(err["loc"] == ["body", "prompt"] and err["type"] == "missing" for err in data["detail"])


def test_generate_image_invalid_model(client):
    response = client.post(
        "/api/v1/images/generate",
        json={"prompt": "test", "model": "invalid-model-name"}
    )
    assert response.status_code == 422 # Validation error for enum
    data = response.json()
    assert "detail" in data
    assert any(err["loc"] == ["body", "model"] for err in data["detail"])


def test_image_generation_endpoint_exists(client: TestClient):
    """
    Tests if the /api/v1/images/generate endpoint is registered and does not return 404.
    It's expected to return 422 if payload is empty/invalid, or 5xx if service has issues.
    """
    response = client.post("/api/v1/images/generate", json={}) # Minimal payload
    assert response.status_code != 404


# TODO: Add tests for other specific error scenarios from the service,
# e.g., if the service raises HTTPException for API key issues or other failures.
# These would involve configuring the mock_image_service methods to raise those exceptions.
# For example:
# def test_generate_image_service_exception(client, mock_image_service):
#     mock_image_service.generate_image_dalle.side_effect = HTTPException(status_code=503, detail="Service unavailable")
#     response = client.post("/api/images/generate", json={"prompt": "test", "model": "dall-e"})
#     assert response.status_code == 503
#     assert response.json()["detail"] == "Service unavailable"

# Remember to clean up app.dependency_overrides if you're not using autouse=True for the override fixture
# or if you have multiple test files that might interfere. The provided `override_dependencies` fixture handles this.
