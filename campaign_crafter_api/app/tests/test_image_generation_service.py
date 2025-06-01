import pytest
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

    # Mock the _save_image_and_log_db method for this test
    expected_permanent_url = "http://localhost/static/generated_images/dalle_test.png"
    with patch.object(image_service, '_save_image_and_log_db', new_callable=AsyncMock) as mock_save_method:
        mock_save_method.return_value = expected_permanent_url

        actual_url = await image_service.generate_image_dalle(
            prompt=prompt,
            db=mock_db_session,
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
        mock_save_method.assert_called_once_with(
            temporary_url=expected_temp_url,
            prompt=prompt,
            model_used="dall-e-3",
            size_used="1024x1024",
            db=mock_db_session,
            user_id=user_id
        )
        assert actual_url == expected_permanent_url

# --- Tests for generate_image_stable_diffusion ---
@pytest.mark.asyncio
async def test_generate_image_stable_diffusion_success(image_service, mock_db_session):
    prompt = "a futuristic city"
    user_id = 1
    expected_temp_url_from_api = "http://sd-api.com/temp_image.png"

    # Mock requests.post for Stable Diffusion
    with patch('requests.post') as mock_requests_post:
        mock_sd_api_response = MagicMock()
        mock_sd_api_response.raise_for_status = MagicMock()
        # Simulate a response structure that the service expects, e.g., with an image_url
        mock_sd_api_response.json.return_value = {"image_url": expected_temp_url_from_api}
        mock_requests_post.return_value = mock_sd_api_response

        # Mock the _save_image_and_log_db method
        expected_permanent_url = "http://localhost/static/generated_images/sd_test.png"
        with patch.object(image_service, '_save_image_and_log_db', new_callable=AsyncMock) as mock_save_method:
            mock_save_method.return_value = expected_permanent_url

            actual_url = await image_service.generate_image_stable_diffusion(
                prompt=prompt,
                db=mock_db_session,
                user_id=user_id,
                size=settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE,
                steps=settings.STABLE_DIFFUSION_DEFAULT_STEPS,
                cfg_scale=settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE,
                sd_model_checkpoint=settings.STABLE_DIFFUSION_DEFAULT_MODEL
            )

            width, height = map(int, settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE.split('x'))
            expected_payload = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": settings.STABLE_DIFFUSION_DEFAULT_STEPS,
                "cfg_scale": settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE,
            }
            # If model checkpoint is part of payload, add check here:
            # if settings.STABLE_DIFFUSION_DEFAULT_MODEL:
            #    payload["override_settings"] = {"sd_model_checkpoint": settings.STABLE_DIFFUSION_DEFAULT_MODEL}

            mock_requests_post.assert_called_once_with(
                image_service.stable_diffusion_api_url, # Check URL from service instance
                headers=pytest.approx({ # Use approx for headers if some are dynamic or less critical
                    "Authorization": f"Bearer {image_service.stable_diffusion_api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }),
                json=expected_payload
            )

            model_used_for_log = f"stable-diffusion ({settings.STABLE_DIFFUSION_DEFAULT_MODEL})" \
                if settings.STABLE_DIFFUSION_DEFAULT_MODEL else "stable-diffusion"

            mock_save_method.assert_called_once_with(
                temporary_url=expected_temp_url_from_api,
                prompt=prompt,
                model_used=model_used_for_log,
                size_used=settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE,
                db=mock_db_session,
                user_id=user_id,
                original_filename_from_api=None # Assuming API doesn't provide this in current mock
            )
            assert actual_url == expected_permanent_url

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
