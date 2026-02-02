import pytest
import base64
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from fastapi import HTTPException
from app.services.llm_service import LLMServiceUnavailableError, LLMGenerationError
import requests
from sqlalchemy.orm import Session

from app.services.image_generation_service import ImageGenerationService
from app.core.config import settings
from app.orm_models import GeneratedImage, User
from app.models import User as UserModel


@pytest.fixture
def mock_db_session():
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=UserModel)
    user.id = 1
    user.is_superuser = False
    user.encrypted_gemini_api_key = None
    user.encrypted_openai_api_key = None
    user.encrypted_sd_api_key = None
    user.sd_engine_preference = "automatic1111"
    return user


@pytest.fixture
def mock_orm_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.is_superuser = False
    user.encrypted_gemini_api_key = None
    user.encrypted_openai_api_key = None
    user.encrypted_sd_api_key = None
    return user


@pytest.fixture
def image_service():
    return ImageGenerationService()


# --- Tests for _get_openai_api_key_for_user ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
async def test_get_openai_key_user_key_valid(mock_decrypt_key, mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_openai_api_key = "encrypted_user_openai_key"
    mock_get_user.return_value = mock_orm_user
    mock_decrypt_key.return_value = "decrypted_user_openai_key"

    api_key = await image_service._get_openai_api_key_for_user(mock_current_user, mock_db_session)

    assert api_key == "decrypted_user_openai_key"
    mock_get_user.assert_called_once_with(mock_db_session, user_id=mock_current_user.id)
    mock_decrypt_key.assert_called_once_with("encrypted_user_openai_key")


@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
async def test_get_openai_key_no_user_key_not_superuser(mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_openai_api_key = None
    mock_orm_user.is_superuser = False
    mock_get_user.return_value = mock_orm_user

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_openai_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 403
    assert "OpenAI API key for image generation not available" in exc_info.value.detail


# --- Tests for _get_sd_api_key_for_user ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
async def test_get_sd_key_user_key_valid(mock_decrypt_key, mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_sd_api_key = "encrypted_user_sd_key"
    mock_get_user.return_value = mock_orm_user
    mock_decrypt_key.return_value = "decrypted_user_sd_key"

    api_key = await image_service._get_sd_api_key_for_user(mock_current_user, mock_db_session)

    assert api_key == "decrypted_user_sd_key"
    mock_get_user.assert_called_once_with(mock_db_session, user_id=mock_current_user.id)
    mock_decrypt_key.assert_called_once_with("encrypted_user_sd_key")


# --- Tests for _get_gemini_api_key_for_user ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
async def test_get_gemini_api_key_user_key_valid(mock_decrypt_key, mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_gemini_api_key = "encrypted_user_gemini_key"
    mock_get_user.return_value = mock_orm_user
    mock_decrypt_key.return_value = "decrypted_user_gemini_key"

    api_key = await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert api_key == "decrypted_user_gemini_key"
    mock_get_user.assert_called_once_with(mock_db_session, user_id=mock_current_user.id)
    mock_decrypt_key.assert_called_once_with("encrypted_user_gemini_key")


@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
async def test_get_gemini_api_key_no_user_key_not_superuser(mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_gemini_api_key = None
    mock_orm_user.is_superuser = False
    mock_get_user.return_value = mock_orm_user

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 403
    assert "Gemini API key for image generation not available" in exc_info.value.detail


@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
async def test_get_gemini_api_key_superuser_system_key_set(mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_gemini_api_key = None
    mock_orm_user.is_superuser = True
    mock_get_user.return_value = mock_orm_user

    original_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = "system_gemini_key"
    
    try:
        api_key = await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)
        assert api_key == "system_gemini_key"
    finally:
        settings.GEMINI_API_KEY = original_key


@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
async def test_get_gemini_api_key_user_not_found(mock_get_user, image_service, mock_current_user, mock_db_session):
    mock_get_user.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail


@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
async def test_get_gemini_api_key_decryption_fails_not_superuser(mock_decrypt_key, mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_gemini_api_key = "encrypted_key_that_fails_decryption"
    mock_orm_user.is_superuser = False
    mock_get_user.return_value = mock_orm_user
    mock_decrypt_key.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 403
    assert "Gemini API key for image generation not available" in exc_info.value.detail
    mock_decrypt_key.assert_called_once_with("encrypted_key_that_fails_decryption")


@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
async def test_get_gemini_api_key_decryption_fails_superuser_fallback(mock_decrypt_key, mock_get_user, image_service, mock_current_user, mock_orm_user, mock_db_session):
    mock_orm_user.encrypted_gemini_api_key = "encrypted_key_that_fails_decryption"
    mock_orm_user.is_superuser = True
    mock_get_user.return_value = mock_orm_user
    mock_decrypt_key.return_value = None

    original_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = "system_fallback_gemini_key"
    
    try:
        api_key = await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)
        assert api_key == "system_fallback_gemini_key"
        mock_decrypt_key.assert_called_once_with("encrypted_key_that_fails_decryption")
    finally:
        settings.GEMINI_API_KEY = original_key


# --- Tests for _save_image_and_log_db ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.BlobServiceClient')
@patch('uuid.uuid4')
async def test_save_image_and_log_db_with_image_bytes(mock_uuid, mock_blob_service_client_class, image_service, mock_db_session):
    # Setup
    mock_uuid.return_value.hex = "testuuid"
    prompt = "test prompt"
    model_used = "test-model"
    size_used = "1024x1024"
    user_id = 1
    campaign_id = 10
    image_bytes = b"fake_image_data"
    
    # Mock Azure Blob Storage
    mock_bsc_instance = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_service_client_class.from_connection_string.return_value = mock_bsc_instance
    mock_bsc_instance.get_blob_client.return_value = mock_blob_client
    
    # Mock settings
    original_conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
    original_container = settings.AZURE_STORAGE_CONTAINER_NAME
    settings.AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey;EndpointSuffix=core.windows.net"
    settings.AZURE_STORAGE_CONTAINER_NAME = "testcontainer"
    
    try:
        permanent_url = await image_service._save_image_and_log_db(
            prompt=prompt,
            model_used=model_used,
            size_used=size_used,
            db=mock_db_session,
            image_bytes=image_bytes,
            user_id=user_id,
            campaign_id=campaign_id
        )
        
        # Verify blob upload
        mock_blob_client.upload_blob.assert_called_once()
        
        # Verify database interaction
        mock_db_session.add.assert_called_once()
        added_image = mock_db_session.add.call_args[0][0]
        assert isinstance(added_image, GeneratedImage)
        assert added_image.prompt == prompt
        assert added_image.model_used == model_used
        assert added_image.size == size_used
        assert added_image.user_id == user_id
        assert "user_uploads/1/campaigns/10/files/testuuid" in added_image.filename
        
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        
        # Verify URL format
        assert "testaccount.blob.core.windows.net" in permanent_url
        assert "testcontainer" in permanent_url
    finally:
        settings.AZURE_STORAGE_CONNECTION_STRING = original_conn_str
        settings.AZURE_STORAGE_CONTAINER_NAME = original_container


@pytest.mark.asyncio
async def test_save_image_and_log_db_no_user_id(image_service, mock_db_session):
    with pytest.raises(ValueError) as exc_info:
        await image_service._save_image_and_log_db(
            prompt="test",
            model_used="test",
            size_used="1024x1024",
            db=mock_db_session,
            image_bytes=b"data",
            user_id=None
        )
    assert "user_id cannot be None" in str(exc_info.value)


# --- Tests for generate_image_dalle ---

@pytest.mark.asyncio
@patch('openai.OpenAI')
async def test_generate_image_dalle_success(mock_openai_class, image_service, mock_current_user, mock_db_session):
    # Setup
    prompt = "a cat playing chess"
    expected_temp_url = "http://openai.com/temp_image.png"
    
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(url=expected_temp_url)]
    mock_client.images.generate.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    # Mock key retrieval
    image_service._get_openai_api_key_for_user = AsyncMock(return_value="test_key")
    
    # Mock save method
    image_service._save_image_and_log_db = AsyncMock(return_value="http://permanent.url/image.png")
    
    # Execute
    actual_url = await image_service.generate_image_dalle(
        prompt=prompt,
        db=mock_db_session,
        current_user=mock_current_user,
        model="dall-e-3",
        size="1024x1024",
        quality="standard"
    )
    
    # Verify
    image_service._get_openai_api_key_for_user.assert_called_once_with(mock_current_user, mock_db_session)
    mock_client.images.generate.assert_called_once()
    assert actual_url == "http://permanent.url/image.png"


# --- Tests for generate_image_gemini ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_success(mock_gemini_class, image_service, mock_current_user, mock_db_session):
    # Setup
    prompt = "A test Gemini image"
    expected_url = "http://example.com/gemini_image.png"
    mock_image_bytes = b"gemini_image_data"
    
    # Mock key retrieval
    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_gemini_key")
    
    # Mock GeminiLLMService
    mock_gemini_instance = AsyncMock()
    mock_gemini_instance.generate_image = AsyncMock(return_value=mock_image_bytes)
    mock_gemini_class.return_value = mock_gemini_instance
    
    # Mock save method
    image_service._save_image_and_log_db = AsyncMock(return_value=expected_url)
    
    # Execute
    image_url = await image_service.generate_image_gemini(
        prompt=prompt,
        db=mock_db_session,
        current_user=mock_current_user,
        model="gemini-pro-vision",
        size="1024x1024"
    )
    
    # Verify
    image_service._get_gemini_api_key_for_user.assert_called_once_with(mock_current_user, mock_db_session)
    mock_gemini_instance.generate_image.assert_called_once()
    image_service._save_image_and_log_db.assert_called_once()
    assert image_url == expected_url


@pytest.mark.asyncio
async def test_generate_image_gemini_key_error(image_service, mock_current_user, mock_db_session):
    image_service._get_gemini_api_key_for_user = AsyncMock(
        side_effect=HTTPException(status_code=403, detail="Key not available")
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(
            prompt="test",
            db=mock_db_session,
            current_user=mock_current_user
        )
    assert exc_info.value.status_code == 403
    assert "Key not available" in exc_info.value.detail


@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_service_unavailable_error(mock_gemini_class, image_service, mock_current_user, mock_db_session):
    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_key")
    
    mock_gemini_instance = AsyncMock()
    mock_gemini_instance.generate_image = AsyncMock(
        side_effect=LLMServiceUnavailableError("Gemini down")
    )
    mock_gemini_class.return_value = mock_gemini_instance
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(
            prompt="test",
            db=mock_db_session,
            current_user=mock_current_user
        )
    assert exc_info.value.status_code == 503
    assert "Gemini service is unavailable" in exc_info.value.detail


@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_generation_error(mock_gemini_class, image_service, mock_current_user, mock_db_session):
    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_key")
    
    mock_gemini_instance = AsyncMock()
    mock_gemini_instance.generate_image = AsyncMock(
        side_effect=LLMGenerationError("Bad prompt for Gemini")
    )
    mock_gemini_class.return_value = mock_gemini_instance
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(
            prompt="test",
            db=mock_db_session,
            current_user=mock_current_user
        )
    assert exc_info.value.status_code == 400  # Changed from 500 to 400
    assert "Gemini image generation failed" in exc_info.value.detail


# --- Tests for delete_image_from_blob_storage ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.BlobServiceClient')
async def test_delete_image_successfully(mock_blob_service_client_class, image_service):
    mock_bsc_instance = MagicMock()
    mock_blob_client = MagicMock()
    # delete_blob is NOT async in the actual service - it's a sync method
    mock_blob_client.delete_blob = MagicMock()
    
    mock_blob_service_client_class.from_connection_string.return_value = mock_bsc_instance
    mock_bsc_instance.get_blob_client.return_value = mock_blob_client
    
    original_conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
    settings.AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net"
    
    try:
        blob_name = "test_blob.png"
        await image_service.delete_image_from_blob_storage(blob_name)
        
        mock_blob_client.delete_blob.assert_called_once()
    finally:
        settings.AZURE_STORAGE_CONNECTION_STRING = original_conn_str


@pytest.mark.asyncio
async def test_delete_image_no_blob_name(image_service):
    with pytest.raises(HTTPException) as exc_info:
        await image_service.delete_image_from_blob_storage("")
    assert exc_info.value.status_code == 400
    assert "Blob name must be provided" in exc_info.value.detail
