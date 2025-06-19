import pytest
import base64 # Added for data URL construction
from unittest.mock import patch, MagicMock, AsyncMock
import uuid # Added for UUID assertion

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.image_generation_service import ImageGenerationService, LLMGenerationError, LLMServiceUnavailableError
from app.core.config import settings
from app.orm_models import GeneratedImage, User # User might not be needed directly if only user_id is used

# Mock settings before importing the service, if service uses settings at import time
# For this service, settings are accessed within methods or __init__, so direct patching is fine.

@pytest.fixture
def mock_db_session():
    db = MagicMock(spec=Session)
    return db

@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=User) # Assuming User is the ORM model for this context
    user.id = 1
    user.is_superuser = False
    user.encrypted_gemini_api_key = None
    # Add other key attributes as needed for tests, e.g. encrypted_openai_api_key
    return user

@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    client.images.generate = MagicMock()
    return client

@pytest.fixture
def image_service(mock_openai_client): # This fixture might need to be adjusted if OpenAI specific setup is too much
    # For general ImageGenerationService tests not focused on OpenAI,
    # we might not need to mock openai.OpenAI specifically here,
    # or we can make it more generic.
    # For now, keeping it as is, but tests for Gemini won't rely on mock_openai_client.
    with patch('openai.OpenAI', return_value=mock_openai_client): # This patches OpenAI for all tests using this fixture
        service = ImageGenerationService()
        # Default settings for SD can remain if they don't interfere
        service.stable_diffusion_api_key = "test_sd_api_key" # This is not used by Gemini tests
        service.stable_diffusion_api_url = "http://test-sd-api.com/generate" # Not used by Gemini
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

@pytest.mark.asyncio
async def test_generate_image_stable_diffusion_missing_base_url(image_service, mock_db_session, mock_current_user):
    # Ensure _get_sd_api_key_for_user is mocked to prevent its own HTTPException
    # if the test environment doesn't have SD keys set up for the mock_current_user.
    image_service._get_sd_api_key_for_user = AsyncMock(return_value="dummy_sd_key")

    original_sd_base_url = settings.STABLE_DIFFUSION_API_BASE_URL
    settings.STABLE_DIFFUSION_API_BASE_URL = None  # Simulate missing base URL
    try:
        with pytest.raises(HTTPException) as exc_info:
            await image_service.generate_image_stable_diffusion(
                prompt="test prompt",
                db=mock_db_session,
                current_user=mock_current_user
                # Other parameters can use defaults or be explicitly None
            )
        assert exc_info.value.status_code == 503
        assert "Stable Diffusion API base URL or engine configuration is missing/invalid" in exc_info.value.detail
    finally:
        settings.STABLE_DIFFUSION_API_BASE_URL = original_sd_base_url # Restore original setting

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


# --- Tests for delete_image_from_blob_storage ---

class TestImageGenerationServiceDeletion:
    def setup_method(self):
        # Store original settings to restore them later if necessary,
        # though for this specific setting, it's often set per test run or globally for tests.
        self.original_conn_string = settings.AZURE_STORAGE_CONNECTION_STRING
        settings.AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=mockaccount;AccountKey=mockkey;EndpointSuffix=core.windows.net"
        self.image_service = ImageGenerationService()

    def teardown_method(self):
        # Restore original settings
        settings.AZURE_STORAGE_CONNECTION_STRING = self.original_conn_string

    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.BlobServiceClient')
    async def test_delete_image_successfully(self, mock_blob_service_client_constructor):
        mock_bsc_instance = MagicMock()
        mock_blob_client_instance = MagicMock()
        mock_blob_client_instance.delete_blob = AsyncMock()

        mock_blob_service_client_constructor.from_connection_string.return_value = mock_bsc_instance
        mock_bsc_instance.get_blob_client.return_value = mock_blob_client_instance

        blob_name = "test_blob.png"
        await self.image_service.delete_image_from_blob_storage(blob_name)

        mock_blob_service_client_constructor.from_connection_string.assert_called_once_with(settings.AZURE_STORAGE_CONNECTION_STRING)
        mock_bsc_instance.get_blob_client.assert_called_once_with(container=settings.AZURE_STORAGE_CONTAINER_NAME, blob=blob_name)
        mock_blob_client_instance.delete_blob.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.BlobServiceClient')
    async def test_delete_image_blob_not_found(self, mock_blob_service_client_constructor, capsys):
        mock_bsc_instance = MagicMock()
        mock_blob_client_instance = MagicMock()
        # Simulate Azure's ResourceNotFoundError or similar by raising an exception with "BlobNotFound"
        mock_blob_client_instance.delete_blob = AsyncMock(side_effect=Exception("ErrorCode:BlobNotFound"))

        mock_blob_service_client_constructor.from_connection_string.return_value = mock_bsc_instance
        mock_bsc_instance.get_blob_client.return_value = mock_blob_client_instance

        blob_name = "non_existent_blob.png"
        try:
            await self.image_service.delete_image_from_blob_storage(blob_name)
        except HTTPException:
            pytest.fail("HTTPException was raised when it should have been handled as BlobNotFound.")

        mock_blob_client_instance.delete_blob.assert_awaited_once()
        captured = capsys.readouterr()
        assert f"Warning: Blob {blob_name} not found" in captured.out
        assert f"Nothing to delete." in captured.out


    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.BlobServiceClient')
    async def test_delete_image_azure_error(self, mock_blob_service_client_constructor):
        mock_bsc_instance = MagicMock()
        mock_blob_client_instance = MagicMock()
        mock_blob_client_instance.delete_blob = AsyncMock(side_effect=Exception("AzureConnectionError"))

        mock_blob_service_client_constructor.from_connection_string.return_value = mock_bsc_instance
        mock_bsc_instance.get_blob_client.return_value = mock_blob_client_instance

        blob_name = "error_blob.png"
        with pytest.raises(HTTPException) as exc_info:
            await self.image_service.delete_image_from_blob_storage(blob_name)

        assert exc_info.value.status_code == 500
        assert "Failed to delete image from cloud storage" in exc_info.value.detail
        mock_blob_client_instance.delete_blob.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_image_no_blob_name(self):
        with pytest.raises(HTTPException) as exc_info:
            await self.image_service.delete_image_from_blob_storage("")
        assert exc_info.value.status_code == 400
        assert "Blob name must be provided" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.settings')
    async def test_delete_image_azure_config_missing_conn_str(self, mock_settings_temp):
        # Temporarily mock settings to simulate only account name being set, or neither
        mock_settings_temp.AZURE_STORAGE_CONNECTION_STRING = None
        mock_settings_temp.AZURE_STORAGE_ACCOUNT_NAME = None # Simulate neither is set

        # Re-initialize service with mocked settings if __init__ depends on them,
        # but delete_image_from_blob_storage reads them directly.
        # No, this service reads settings within the method, so we just need to ensure settings are mocked correctly.

        blob_name = "any_blob.png"
        with pytest.raises(HTTPException) as exc_info:
             await self.image_service.delete_image_from_blob_storage(blob_name) # service instance already created with original settings

        # To test this properly, settings should be modified BEFORE service instantiation,
        # or the service should re-evaluate settings each time, or take them as params.
        # Given the current service structure, the image_service instance in self.image_service
        # was created with the connection string set in setup_method.
        # A more robust test would be to patch settings *before* ImageGenerationService() is called.

        # Let's refine this test:
        # We need to control the settings *as seen by the method when it runs*.
        # The current self.image_service will use the conn string from setup_method.
        # So, this test as is might not reflect "missing conn string" scenario accurately for the *method's logic*
        # unless the method *re-reads* settings.AZURE_STORAGE_CONNECTION_STRING *every time*.
        # The method *does* re-read settings.

        # Correct approach for this specific service design:
        original_conn_string = settings.AZURE_STORAGE_CONNECTION_STRING
        original_account_name = settings.AZURE_STORAGE_ACCOUNT_NAME

        settings.AZURE_STORAGE_CONNECTION_STRING = None
        settings.AZURE_STORAGE_ACCOUNT_NAME = None

        # ImageGenerationService() does not initialize BlobServiceClient in __init__
        # It's initialized within the delete_image_from_blob_storage method
        # So, modifying global settings object directly should work here.

        with pytest.raises(HTTPException) as exc_info_no_config:
            await self.image_service.delete_image_from_blob_storage(blob_name)

        assert exc_info_no_config.value.status_code == 500
        assert "Azure Storage is not configured" in exc_info_no_config.value.detail

        # Restore settings
        settings.AZURE_STORAGE_CONNECTION_STRING = original_conn_string
        settings.AZURE_STORAGE_ACCOUNT_NAME = original_account_name
        # The @patch for settings might not be the best way here if we need to restore.
        # Direct modification and restoration is clearer. The patch on settings was removed for this test.

    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.BlobServiceClient.from_connection_string', side_effect=Exception("Connection Invalid"))
    async def test_delete_image_azure_conn_str_invalid(self, mock_from_conn_string):
        # settings.AZURE_STORAGE_CONNECTION_STRING is already set by setup_method
        blob_name = "any_blob.png"
        with pytest.raises(HTTPException) as exc_info:
            await self.image_service.delete_image_from_blob_storage(blob_name)

        assert exc_info.value.status_code == 500
        assert "Azure Storage configuration error (connection string)" in exc_info.value.detail
        mock_from_conn_string.assert_called_once()


# --- Tests for _save_image_and_log_db user-specific path ---
class TestSaveImageAndLogDbUserSpecificPath:
    def setup_method(self):
        self.original_conn_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.original_account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.original_container_name = settings.AZURE_STORAGE_CONTAINER_NAME

        settings.AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey;EndpointSuffix=core.windows.net"
        settings.AZURE_STORAGE_ACCOUNT_NAME = None # Explicitly None for this test case
        settings.AZURE_STORAGE_CONTAINER_NAME = "testcontainer"

        self.image_service = ImageGenerationService()
        self.mock_db_session = MagicMock(spec=Session)

    def teardown_method(self):
        settings.AZURE_STORAGE_CONNECTION_STRING = self.original_conn_string
        settings.AZURE_STORAGE_ACCOUNT_NAME = self.original_account_name
        settings.AZURE_STORAGE_CONTAINER_NAME = self.original_container_name

    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.DefaultAzureCredential') # Patch DefaultAzureCredential
    @patch('app.services.image_generation_service.BlobServiceClient') # Patch BlobServiceClient
    async def test_save_image_and_log_db_uses_user_specific_path(self, mock_blob_service_client_constructor, mock_default_azure_credential):
        test_user_id = 123
        prompt = "test prompt for user path"
        model_used = "dall-e-test"
        size_used = "512x512"
        image_bytes = b"fakeimagedata"

        # Configure mocks
        mock_bsc_instance = MagicMock()
        mock_blob_service_client_constructor.from_connection_string.return_value = mock_bsc_instance

        mock_blob_client_instance = MagicMock()
        mock_bsc_instance.get_blob_client.return_value = mock_blob_client_instance
        mock_blob_client_instance.upload_blob = MagicMock()

        # Call the method
        returned_url = await self.image_service._save_image_and_log_db(
            prompt=prompt,
            model_used=model_used,
            size_used=size_used,
            db=self.mock_db_session,
            image_bytes=image_bytes,
            user_id=test_user_id,
            original_filename_from_api="original.png" # Provide a default to ensure .png extension
        )

        # Assert BlobServiceClient was called with connection string
        mock_blob_service_client_constructor.from_connection_string.assert_called_once_with(settings.AZURE_STORAGE_CONNECTION_STRING)

        # Assert get_blob_client call
        mock_bsc_instance.get_blob_client.assert_called_once()
        call_args = mock_bsc_instance.get_blob_client.call_args
        assert call_args[1]['container'] == "testcontainer"

        # Assert blob name format
        blob_name_arg = call_args[1]['blob']
        assert blob_name_arg.startswith(f"user_uploads/{test_user_id}/")
        assert blob_name_arg.endswith(".png")

        # Assert UUID part of blob name
        filename_part = blob_name_arg.split(f"user_uploads/{test_user_id}/")[1].split(".png")[0]
        try:
            uuid.UUID(filename_part, version=4)
        except ValueError:
            pytest.fail(f"Filename part '{filename_part}' is not a valid UUID hex.")

        # Assert upload_blob call
        mock_blob_client_instance.upload_blob.assert_called_once()
        # Check that the stream passed to upload_blob contains the image_bytes
        upload_args, upload_kwargs = mock_blob_client_instance.upload_blob.call_args
        uploaded_stream_content = upload_args[0].read()
        assert uploaded_stream_content == image_bytes


        # Assert returned URL
        # The URL construction logic in the service is:
        # f"{final_account_url_base}/{settings.AZURE_STORAGE_CONTAINER_NAME.strip('/')}/{blob_name}"
        # final_account_url_base is derived from conn string if AZURE_STORAGE_ACCOUNT_NAME is None
        # For "DefaultEndpointsProtocol=https;AccountName=testaccount;..." it becomes "https://testaccount.blob.core.windows.net"
        expected_account_url_base = "https://testaccount.blob.core.windows.net" # From dummy conn string
        expected_url = f"{expected_account_url_base}/{settings.AZURE_STORAGE_CONTAINER_NAME}/{blob_name_arg}"
        assert returned_url == expected_url

        # Assert database interaction
        self.mock_db_session.add.assert_called_once()
        added_image_instance = self.mock_db_session.add.call_args[0][0]
        assert isinstance(added_image_instance, GeneratedImage)
        assert added_image_instance.user_id == test_user_id
        assert added_image_instance.filename == blob_name_arg
        assert added_image_instance.image_url == expected_url
        assert added_image_instance.prompt == prompt

        self.mock_db_session.commit.assert_called_once()
        self.mock_db_session.refresh.assert_called_once_with(added_image_instance)

        # Ensure DefaultAzureCredential was NOT called because connection string was used
        mock_default_azure_credential.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.image_generation_service.requests.get') # Mock requests.get for this test
    @patch('app.services.image_generation_service.DefaultAzureCredential')
    @patch('app.services.image_generation_service.BlobServiceClient')
    async def test_save_image_and_log_db_temp_url_path_correction(
        self,
        mock_blob_service_client_constructor,
        mock_default_azure_credential,
        mock_requests_get
    ):
        test_user_id = 456
        prompt = "test prompt for temp url correction"
        model_used = "dall-e-temp-url"
        size_used = "1024x1024"
        temporary_url = "http://example.com/image.png" # Initial extension is .png
        image_content_bytes = b"fakejpegdata"

        # Configure mock for requests.get()
        mock_http_response = MagicMock()
        mock_http_response.raise_for_status = MagicMock()
        mock_http_response.content = image_content_bytes
        mock_http_response.headers = {'Content-Type': 'image/jpeg'} # Actual type is JPEG
        mock_requests_get.return_value = mock_http_response

        # Configure Azure mocks (BlobServiceClient, DefaultAzureCredential are parameters)
        mock_bsc_instance = MagicMock()
        mock_blob_service_client_constructor.from_connection_string.return_value = mock_bsc_instance

        mock_blob_client_instance = MagicMock()
        mock_bsc_instance.get_blob_client.return_value = mock_blob_client_instance
        mock_blob_client_instance.upload_blob = MagicMock()

        # Call the method with temporary_url, no image_bytes directly
        returned_url = await self.image_service._save_image_and_log_db(
            prompt=prompt,
            model_used=model_used,
            size_used=size_used,
            db=self.mock_db_session,
            temporary_url=temporary_url,
            image_bytes=None, # Explicitly None
            user_id=test_user_id
            # original_filename_from_api is not provided, so initial extension from URL is used
        )

        # Assert requests.get was called
        mock_requests_get.assert_called_once_with(temporary_url, stream=True)

        # Assert BlobServiceClient was called
        mock_blob_service_client_constructor.from_connection_string.assert_called_once_with(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )

        # Assert get_blob_client call
        mock_bsc_instance.get_blob_client.assert_called_once()
        call_args = mock_bsc_instance.get_blob_client.call_args
        assert call_args[1]['container'] == "testcontainer"

        # Assert blob name format - this is crucial
        blob_name_arg = call_args[1]['blob']
        assert blob_name_arg.startswith(f"user_uploads/{test_user_id}/")
        assert blob_name_arg.endswith(".jpg") # Should be .jpg due to Content-Type header

        # Assert UUID part of blob name
        # The split needs to account for the dynamic part of the path
        expected_prefix = f"user_uploads/{test_user_id}/"
        expected_suffix = ".jpg"
        filename_part = blob_name_arg[len(expected_prefix):-len(expected_suffix)]
        try:
            uuid.UUID(filename_part, version=4)
        except ValueError:
            pytest.fail(f"Filename part '{filename_part}' is not a valid UUID hex.")

        # Assert upload_blob call with correct data
        mock_blob_client_instance.upload_blob.assert_called_once()
        upload_args, upload_kwargs = mock_blob_client_instance.upload_blob.call_args
        uploaded_stream_content = upload_args[0].read()
        assert uploaded_stream_content == image_content_bytes # Should be the JPEG data
        assert upload_kwargs['headers']['Content-Type'] == 'image/jpeg'


        # Assert returned URL
        expected_account_url_base = "https://testaccount.blob.core.windows.net" # From dummy conn string in setup_method
        expected_url = f"{expected_account_url_base}/{settings.AZURE_STORAGE_CONTAINER_NAME}/{blob_name_arg}"
        assert returned_url == expected_url

        # Assert database interaction
        self.mock_db_session.add.assert_called_once()
        added_image_instance = self.mock_db_session.add.call_args[0][0]
        assert isinstance(added_image_instance, GeneratedImage)
        assert added_image_instance.user_id == test_user_id
        assert added_image_instance.filename == blob_name_arg # Filename should end with .jpg
        assert added_image_instance.image_url == expected_url
        assert added_image_instance.prompt == prompt

        self.mock_db_session.commit.assert_called_once()
        self.mock_db_session.refresh.assert_called_once_with(added_image_instance)

        # Ensure DefaultAzureCredential was NOT called
        mock_default_azure_credential.assert_not_called()


# --- Tests for _get_gemini_api_key_for_user ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
@patch('app.services.image_generation_service.settings')
async def test_get_gemini_api_key_user_key_valid(mock_settings, mock_decrypt_key, mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 1
    mock_user_orm = MagicMock(spec=User)
    mock_user_orm.id = mock_current_user.id
    mock_user_orm.is_superuser = False
    mock_user_orm.encrypted_gemini_api_key = "encrypted_user_gemini_key"
    mock_get_user.return_value = mock_user_orm
    mock_decrypt_key.return_value = "decrypted_user_gemini_key"

    api_key = await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert api_key == "decrypted_user_gemini_key"
    mock_get_user.assert_called_once_with(mock_db_session, user_id=mock_current_user.id)
    mock_decrypt_key.assert_called_once_with("encrypted_user_gemini_key")

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.settings')
async def test_get_gemini_api_key_no_user_key_not_superuser(mock_settings, mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 2
    mock_user_orm = MagicMock(spec=User)
    mock_user_orm.id = mock_current_user.id
    mock_user_orm.is_superuser = False
    mock_user_orm.encrypted_gemini_api_key = None
    mock_get_user.return_value = mock_user_orm

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 403
    assert "Gemini API key for image generation not available" in exc_info.value.detail

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key') # Still need to patch decrypt even if not called
@patch('app.services.image_generation_service.settings')
async def test_get_gemini_api_key_superuser_system_key_set(mock_settings, mock_decrypt_key, mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 3
    mock_user_orm = MagicMock(spec=User)
    mock_user_orm.id = mock_current_user.id
    mock_user_orm.is_superuser = True
    mock_user_orm.encrypted_gemini_api_key = None # No user-specific key
    mock_get_user.return_value = mock_user_orm

    mock_settings.GEMINI_API_KEY = "system_gemini_key"

    api_key = await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert api_key == "system_gemini_key"
    mock_decrypt_key.assert_not_called() # Should not be called as there's no encrypted key

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.settings')
async def test_get_gemini_api_key_superuser_system_key_not_set(mock_settings, mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 4
    mock_user_orm = MagicMock(spec=User)
    mock_user_orm.id = mock_current_user.id
    mock_user_orm.is_superuser = True
    mock_user_orm.encrypted_gemini_api_key = None
    mock_get_user.return_value = mock_user_orm

    mock_settings.GEMINI_API_KEY = None # System key not set

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 403
    assert "Gemini API key for image generation not available" in exc_info.value.detail

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
async def test_get_gemini_api_key_user_not_found(mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 5
    mock_get_user.return_value = None # User not found

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
@patch('app.services.image_generation_service.settings') # Mock settings for fallback check
async def test_get_gemini_api_key_decryption_fails_not_superuser(mock_settings, mock_decrypt_key, mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 6
    mock_user_orm = MagicMock(spec=User)
    mock_user_orm.id = mock_current_user.id
    mock_user_orm.is_superuser = False
    mock_user_orm.encrypted_gemini_api_key = "encrypted_key_that_fails_decryption"
    mock_get_user.return_value = mock_user_orm
    mock_decrypt_key.return_value = None # Simulate decryption failure

    # No system key fallback for non-superuser if decryption fails
    mock_settings.GEMINI_API_KEY = None

    with pytest.raises(HTTPException) as exc_info:
        await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert exc_info.value.status_code == 403
    assert "Gemini API key for image generation not available" in exc_info.value.detail
    mock_decrypt_key.assert_called_once_with("encrypted_key_that_fails_decryption")

@pytest.mark.asyncio
@patch('app.services.image_generation_service.crud.get_user')
@patch('app.services.image_generation_service.decrypt_key')
@patch('app.services.image_generation_service.settings')
async def test_get_gemini_api_key_decryption_fails_superuser_fallback(mock_settings, mock_decrypt_key, mock_get_user, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    mock_current_user.id = 7
    mock_user_orm = MagicMock(spec=User)
    mock_user_orm.id = mock_current_user.id
    mock_user_orm.is_superuser = True
    mock_user_orm.encrypted_gemini_api_key = "encrypted_key_that_fails_decryption"
    mock_get_user.return_value = mock_user_orm
    mock_decrypt_key.return_value = None # Simulate decryption failure

    mock_settings.GEMINI_API_KEY = "system_fallback_gemini_key" # Superuser has system key fallback

    api_key = await image_service._get_gemini_api_key_for_user(mock_current_user, mock_db_session)

    assert api_key == "system_fallback_gemini_key"
    mock_decrypt_key.assert_called_once_with("encrypted_key_that_fails_decryption")


# --- Tests for generate_image_gemini ---

@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_success_with_imagen(mock_gemini_llm_service_class, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    # Arrange
    prompt = "A test image for Imagen via GeminiLLMService"
    expected_image_bytes = b"fake_imagen_bytes"
    expected_url = "http://example.com/imagen_image.png"
    imagen_model_id_to_use = "imagen-005" # Example Imagen model ID

    # Mock _get_gemini_api_key_for_user to return a dummy key
    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_gemini_key")

    # Mock GeminiLLMService instance and its generate_image method (which now uses Imagen)
    mock_gemini_service_instance = AsyncMock() # This is the instance of GeminiLLMService
    mock_gemini_service_instance.generate_image = AsyncMock(return_value=expected_image_bytes)
    mock_gemini_llm_service_class.return_value = mock_gemini_service_instance # When ImageGenerationService instantiates GeminiLLMService

    # Mock _save_image_and_log_db
    image_service._save_image_and_log_db = AsyncMock(return_value=expected_url)

    # Act
    image_url = await image_service.generate_image_gemini(
        prompt=prompt,
        db=mock_db_session,
        current_user=mock_current_user,
        model=imagen_model_id_to_use, # Pass the Imagen model ID
        size="1024x1024" # Conceptual size
    )

    # Assert
    image_service._get_gemini_api_key_for_user.assert_called_once_with(mock_current_user, mock_db_session)
    # Check GeminiLLMService was instantiated with the key
    mock_gemini_llm_service_class.assert_called_once_with(api_key="dummy_gemini_key")

    # Assert that the generate_image method on the GeminiLLMService instance was called correctly
    mock_gemini_service_instance.generate_image.assert_called_once_with(
        prompt=prompt,
        current_user=mock_current_user,
        db=mock_db_session,
        model=imagen_model_id_to_use, # Should be the Imagen model
        size="1024x1024"
    )

    # Assert that _save_image_and_log_db was called with the correct parameters
    image_service._save_image_and_log_db.assert_called_once_with(
        prompt=prompt,
        model_used=imagen_model_id_to_use, # Log the actual Imagen model used
        size_used="1024x1024",
        db=mock_db_session,
        image_bytes=expected_image_bytes,
        user_id=mock_current_user.id,
        original_filename_from_api="gemini_imagen_image.png" # Updated filename hint
    )
    assert image_url == expected_url

@pytest.mark.asyncio
async def test_generate_image_gemini_key_error(image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    # Arrange
    image_service._get_gemini_api_key_for_user = AsyncMock(side_effect=HTTPException(status_code=403, detail="Key not available"))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(prompt="test", db=mock_db_session, current_user=mock_current_user)
    assert exc_info.value.status_code == 403
    assert "Key not available" in exc_info.value.detail

@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_service_unavailable_error(mock_gemini_llm_service_class, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    # Arrange
    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_key") # Ensures _get_gemini_api_key_for_user is called
    mock_gemini_service_instance = AsyncMock()
    # Simulate LLMServiceUnavailableError from the GeminiLLMService (e.g., new SDK client not available)
    mock_gemini_service_instance.generate_image = AsyncMock(side_effect=LLMServiceUnavailableError("Gemini/Imagen service down"))
    mock_gemini_llm_service_class.return_value = mock_gemini_service_instance

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(prompt="test", db=mock_db_session, current_user=mock_current_user, model="imagen-005")
    assert exc_info.value.status_code == 503
    # The detail message comes from ImageGenerationService's exception handling
    assert "Gemini/Imagen service is unavailable: Gemini/Imagen service down" in exc_info.value.detail

@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_generation_error_from_service(mock_gemini_llm_service_class, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    # Arrange
    # This error message simulates an error coming from the new google-genai SDK via GeminiLLMService
    sdk_error_message = "Imagen API Error: Blocked by content policy (Safety)"

    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_key")
    mock_gemini_service_instance = AsyncMock()
    mock_gemini_service_instance.generate_image = AsyncMock(side_effect=LLMGenerationError(sdk_error_message))
    mock_gemini_llm_service_class.return_value = mock_gemini_service_instance

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(prompt="a risky prompt", db=mock_db_session, current_user=mock_current_user, model="imagen-005")

    # Based on current ImageGenerationService logic:
    # if "content policy" in str(e).lower() or "prompt" in str(e).lower() or "permission" in str(e).lower() or "allowlist" in str(e).lower():
    #    raise HTTPException(status_code=400, detail=f"Image generation failed (Gemini/Imagen): {str(e)}")
    # else:
    #    raise HTTPException(status_code=500, detail=f"Failed to generate image with Gemini/Imagen: {str(e)}")

    if "content policy" in sdk_error_message.lower() or "prompt" in sdk_error_message.lower():
        assert exc_info.value.status_code == 400
    else:
        assert exc_info.value.status_code == 500
    assert f"Image generation failed (Gemini/Imagen): {sdk_error_message}" in exc_info.value.detail

@pytest.mark.asyncio
@patch('app.services.image_generation_service.GeminiLLMService')
async def test_generate_image_gemini_save_error(mock_gemini_llm_service_class, image_service: ImageGenerationService, mock_current_user: User, mock_db_session: Session):
    # Arrange
    image_service._get_gemini_api_key_for_user = AsyncMock(return_value="dummy_key")
    mock_gemini_service_instance = AsyncMock()
    mock_gemini_service_instance.generate_image = AsyncMock(return_value=b"fake_imagen_bytes") # Simulate successful image byte generation
    mock_gemini_llm_service_class.return_value = mock_gemini_service_instance

    # Simulate an error during the saving process
    image_service._save_image_and_log_db = AsyncMock(side_effect=HTTPException(status_code=500, detail="Disk full or Azure upload failed"))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await image_service.generate_image_gemini(prompt="test", db=mock_db_session, current_user=mock_current_user, model="imagen-005")
    assert exc_info.value.status_code == 500
    assert "Disk full or Azure upload failed" in exc_info.value.detail
