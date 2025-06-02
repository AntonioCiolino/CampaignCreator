import pytest
import base64 # Added for data URL construction
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.image_generation_service import ImageGenerationService
from app.core.config import settings
from app.orm_models import GeneratedImage # Ensure this is imported if used directly in tests

# Mock settings before importing the service, if service uses settings at import time
# For this service, settings are accessed within methods or __init__, so direct patching is fine.

@pytest.fixture
def mock_db_session():
    db = MagicMock(spec=Session)
    return db

@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    # .images.generate() is now a synchronous method, so it should be a MagicMock
    client.images.generate = MagicMock() 
    return client

@pytest.fixture
def image_service(mock_openai_client):
    with patch('openai.OpenAI', return_value=mock_openai_client):
        service = ImageGenerationService()
        # Override specific settings if necessary for testing, e.g., API keys if checks are stringent
        service.stable_diffusion_api_key = "test_sd_api_key"
        service.stable_diffusion_api_url = "http://test-sd-api.com/generate"
        # service.openai_client is already mocked via patch on openai.OpenAI
    return service

# --- Tests for _save_image_and_log_db ---
@pytest.mark.asyncio
async def test_save_image_and_log_db_success(image_service, mock_db_session):
    temporary_url = "http://temp-image.com/image.png"
    prompt = "test prompt"
    model_used = "test-model"
    size_used = "1024x1024"
    user_id = 1
    expected_filename_partial = ".png" # from uuid.uuid4().hex + .png
    
    # Mock external calls made by _save_image_and_log_db
    with patch('requests.get') as mock_requests_get, \
         patch('shutil.copyfileobj') as mock_shutil_copy, \
         patch('uuid.uuid4') as mock_uuid, \
         patch('pathlib.Path.mkdir') as mock_mkdir:

        mock_uuid.return_value.hex = "testuuid"
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.raw = MagicMock()
        mock_requests_get.return_value = mock_response

        permanent_url = await image_service._save_image_and_log_db(
            temporary_url, prompt, model_used, size_used, mock_db_session, user_id
        )

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_requests_get.assert_called_once_with(temporary_url, stream=True)
        mock_shutil_copy.assert_called_once()
        
        # Check DB interaction
        mock_db_session.add.assert_called_once()
        added_image = mock_db_session.add.call_args[0][0]
        assert isinstance(added_image, GeneratedImage)
        assert added_image.filename == f"testuuid{expected_filename_partial}"
        assert added_image.image_url == f"{settings.IMAGE_BASE_URL}testuuid{expected_filename_partial}"
        assert added_image.prompt == prompt
        assert added_image.model_used == model_used
        assert added_image.size == size_used
        assert added_image.user_id == user_id
        
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(added_image)
        
        assert permanent_url == f"{settings.IMAGE_BASE_URL}testuuid{expected_filename_partial}"

# --- Tests for generate_image_dalle ---
@pytest.mark.asyncio
async def test_generate_image_dalle_success(image_service, mock_db_session, mock_openai_client):
    prompt = "a cat playing chess"
    user_id = 1
    expected_temp_url = "http://openai.com/temp_image.png"

    # Configure mock OpenAI client response
    mock_openai_response = MagicMock()
    mock_openai_response.data = [MagicMock(url=expected_temp_url)]
    mock_openai_client.images.generate.return_value = mock_openai_response

    # _save_image_and_log_db is no longer called directly in this flow, so no need to mock it here.
    # The method now returns the temporary URL.
    actual_url = await image_service.generate_image_dalle(
        prompt=prompt, 
        db=mock_db_session, # db session is still a param, even if _save_image_and_log_db is not used by this flow.
        user_id=user_id,
        model="dall-e-3", # Specify model for clarity in test
        size="1024x1024",
        quality="standard"
    )

    mock_openai_client.images.generate.assert_called_once_with(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="url"
    )
    # Assert that the returned URL is the temporary URL from the API response
    assert actual_url == expected_temp_url

# --- Tests for generate_image_stable_diffusion ---
@pytest.mark.asyncio
async def test_generate_image_stable_diffusion_success(image_service, mock_db_session):
    prompt = "a futuristic city"
    user_id = 1
    mock_image_bytes = b'fake_webp_image_content'
    output_format = "webp" # As hardcoded in the service method's form_data
    mime_type = f"image/{output_format}"

    # Expected data URL
    expected_base64_content = base64.b64encode(mock_image_bytes).decode('utf-8')
    expected_data_url = f"data:{mime_type};base64,{expected_base64_content}"

    # Mock requests.post for Stable Diffusion
    with patch('app.services.image_generation_service.requests.post') as mock_requests_post:
        mock_sd_api_response = MagicMock()
        mock_sd_api_response.status_code = 200
        mock_sd_api_response.content = mock_image_bytes
        mock_sd_api_response.headers = {'Content-Type': mime_type}
        # No longer need mock_sd_api_response.json as we expect image bytes for success
        mock_requests_post.return_value = mock_sd_api_response

        actual_url = await image_service.generate_image_stable_diffusion(
            prompt=prompt,
            db=mock_db_session, 
            user_id=user_id,
            size=settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE, # This is used for logging, not direct payload now
            steps=settings.STABLE_DIFFUSION_DEFAULT_STEPS,
            cfg_scale=settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE,
            sd_model_checkpoint=settings.STABLE_DIFFUSION_DEFAULT_MODEL # Used for logging
        )
        
        assert actual_url == expected_data_url

        # Check the arguments passed to requests.post
        mock_requests_post.assert_called_once()
        args, kwargs = mock_requests_post.call_args
        
        assert args[0] == image_service.stable_diffusion_api_url
        
        # Check headers (Accept header is key)
        assert kwargs['headers']['Authorization'] == f"Bearer {image_service.stable_diffusion_api_key}"
        assert kwargs['headers']['Accept'] == "image/*"
        # Content-Type is not explicitly set in headers by service, requests infers it for multipart

        # Check form data
        expected_form_data = {
            "prompt": prompt,
            "output_format": output_format, # Service uses 'webp'
            "steps": str(settings.STABLE_DIFFUSION_DEFAULT_STEPS),
            "cfg_scale": str(settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE),
        }
        assert kwargs['data'] == expected_form_data
        
        # Check files payload
        assert 'none' in kwargs['files']
        assert kwargs['files']['none'] == (None, '')


# TODO: Add tests for error handling in all three methods
# e.g., API connection errors, API returning error status, _save_image failure scenarios.
# Test DALL-E client initialization failure if API key is missing (if not already covered by service startup)
# Test Stable Diffusion key/URL missing in __init__ behavior (e.g. methods should fail clearly)

# Example of testing an error case for _save_image_and_log_db
@pytest.mark.asyncio
async def test_save_image_and_log_db_download_fails(image_service, mock_db_session):
    with patch('requests.get') as mock_requests_get, \
         patch('pathlib.Path.mkdir'): # Mock other parts to isolate the test
        mock_requests_get.side_effect = requests.exceptions.RequestException("Download failed")

        with pytest.raises(HTTPException) as exc_info:
            await image_service._save_image_and_log_db(
                "http://fail-url.com/img.png", "p", "m", "s", mock_db_session, 1
            )
        assert exc_info.value.status_code == 502
        assert "Failed to download image from source" in exc_info.value.detail
        mock_db_session.add.assert_not_called() # Ensure DB not touched on failure
