from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import uuid
from pathlib import Path
from io import BytesIO

from app.db import get_db
from app.models import User as UserModel
from app.services.auth_service import get_current_active_user
from app.core.config import settings
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from azure.storage.blob import ContentSettings


router = APIRouter()

# --- Pydantic Models ---
class FileUploadResponse(BaseModel):
    imageUrl: HttpUrl # Using HttpUrl for validation
    filename: str
    content_type: str
    size: int

# --- Helper Functions (placeholder for now, will be expanded) ---
async def _upload_file_to_blob_storage(file: UploadFile, user_id: int) -> str:
    image_bytes = await file.read()
    # It's good practice to seek back to the beginning if the file stream were to be used again,
    # but for a single read-and-upload, it's not strictly necessary.
    # await file.seek(0)

    async_blob_service_client = None
    account_url_base = None
    async_credential = None # Define to ensure it's in scope for finally block if needed

    try:
        if settings.AZURE_STORAGE_ACCOUNT_NAME:
            account_url_base = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            async_credential = AsyncDefaultAzureCredential()
            async_blob_service_client = AsyncBlobServiceClient(account_url_base, credential=async_credential)
        elif settings.AZURE_STORAGE_CONNECTION_STRING:
            async_blob_service_client = AsyncBlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            conn_parts = {part.split('=', 1)[0]: part.split('=', 1)[1] for part in settings.AZURE_STORAGE_CONNECTION_STRING.split(';') if '=' in part}
            account_name_from_conn_str = conn_parts.get('AccountName')
            if account_name_from_conn_str:
                account_url_base = f"https://{account_name_from_conn_str}.blob.core.windows.net"
            else: # Should not happen for valid connection strings with AccountName
                 raise HTTPException(status_code=500, detail="Azure Storage AccountName missing in connection string and AZURE_STORAGE_ACCOUNT_NAME not set.")
        else:
            raise HTTPException(status_code=500, detail="Azure Storage is not configured (missing AZURE_STORAGE_ACCOUNT_NAME or AZURE_STORAGE_CONNECTION_STRING).")

        if not account_url_base: # Should be set if client was created
             raise HTTPException(status_code=500, detail="Azure Storage account URL base could not be determined.")

        file_extension = Path(file.filename).suffix.lower() if file.filename else ".bin" # Default to .bin if no extension
        if not file_extension or len(file_extension) > 5: # Basic sanitization
            file_extension = ".bin"

        # Use a subfolder for user uploads, including user_id for organization
        blob_name = f"user_uploads/{user_id}/{uuid.uuid4().hex}{file_extension}"
        content_type_from_file = file.content_type or 'application/octet-stream'

        content_settings_obj = ContentSettings(content_type=content_type_from_file)

        async with async_blob_service_client: # Manages client lifetime including close
            blob_client = async_blob_service_client.get_blob_client(
                container=settings.AZURE_STORAGE_CONTAINER_NAME,
                blob=blob_name
            )
            with BytesIO(image_bytes) as stream_data:
                await blob_client.upload_blob(
                    stream_data,
                    overwrite=True,
                    content_settings=content_settings_obj
                )

        print(f"Image uploaded to Azure Blob Storage: {blob_name} in container {settings.AZURE_STORAGE_CONTAINER_NAME}")
        permanent_image_url = f"{account_url_base.strip('/')}/{settings.AZURE_STORAGE_CONTAINER_NAME.strip('/')}/{blob_name}"

        return permanent_image_url

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        print(f"Failed to upload image to Azure Blob Storage: {type(e).__name__} - {e}")
        # Optionally log traceback.print_exc() here for more detail in server logs
        raise HTTPException(status_code=500, detail=f"Failed to upload image to cloud storage: {str(e)}")
    finally:
        if async_credential and hasattr(async_credential, 'close'):
            await async_credential.close()
        # AsyncBlobServiceClient is closed by 'async with' if it was successfully created.
        # If client creation failed before 'async with' and it needs explicit close, that's more complex.
        # However, from_connection_string doesn't return a credential to close,
        # and DefaultAzureCredential is closed.

# --- API Endpoint ---
@router.post(
    "/files/upload_image", # Consider a more generic path if it might handle other file types later
    response_model=FileUploadResponse,
    tags=["File Uploads"],
    summary="Upload an image file."
)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db), # db might not be needed if not logging uploads here
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Uploads an image file to blob storage and returns its public URL.

    - **file**: The image file to upload (multipart/form-data).
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

    # Basic size check (e.g., 10MB limit) - optional
    # MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB
    # size = await file.seek(0, 2) # Get file size
    # await file.seek(0) # Reset cursor
    # if size > MAX_FILE_SIZE:
    #     raise HTTPException(status_code=413, detail=f"File too large. Limit is {MAX_FILE_SIZE // (1024*1024)}MB.")

    try:
        # The actual blob upload logic will be in _upload_file_to_blob_storage
        # For now, we call the placeholder
        image_url = await _upload_file_to_blob_storage(file=file, user_id=current_user.id)

        # Get file size after read (if not done before)
        # This is tricky with UploadFile as read consumes it.
        # For now, we'll omit precise size in response or get it before read if needed.
        # For this example, we'll just use a placeholder for size.
        # actual_size = len(await file.read()) # This would consume the file if called after another read
        # await file.seek(0) # And this would be needed if we re-read

        return FileUploadResponse(
            imageUrl=image_url,
            filename=file.filename or "unknown_filename",
            content_type=file.content_type or "unknown_content_type",
            size=file.size if hasattr(file, 'size') and file.size is not None else -1 # FastAPI UploadFile has an optional size attribute
        )
    except HTTPException:
        raise # Re-raise HTTPExceptions (e.g., from validation or placeholder)
    except Exception as e:
        print(f"Unexpected error in upload_image_endpoint: {type(e).__name__} - {e}")
        # Log the full error traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred during file upload.")
