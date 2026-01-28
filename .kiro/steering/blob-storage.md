# Azure Blob Storage - Campaign Crafter API

## Configuration

Environment variables in `.env`:

```env
# Option 1: Connection String (preferred for local dev)
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"

# Option 2: Account Name + DefaultAzureCredential (for production/managed identity)
AZURE_STORAGE_ACCOUNT_NAME="yourstorageaccount"

# Container name (default: campaignimages)
AZURE_STORAGE_CONTAINER_NAME="campaignimages"
```

Authentication priority:
1. Connection string (if `AZURE_STORAGE_CONNECTION_STRING` is set)
2. DefaultAzureCredential with account name (if `AZURE_STORAGE_ACCOUNT_NAME` is set)

## Service Location

All blob operations are in `app/services/image_generation_service.py`:

```python
from app.services.image_generation_service import ImageGenerationService

image_service = ImageGenerationService()
```

## Key Methods

### Upload Image
```python
permanent_url = await image_service._save_image_and_log_db(
    prompt="description",
    model_used="dall-e-3",
    size_used="1024x1024",
    db=db,
    temporary_url=temp_url,      # OR
    image_bytes=raw_bytes,       # provide one of these
    user_id=user.id,
    campaign_id=campaign.id      # Optional, affects path
)
```

### Delete Image
```python
await image_service.delete_image_from_blob_storage(blob_name)
```

### List Campaign Files
```python
files: list[BlobFileMetadata] = await image_service.list_campaign_files(
    user_id=user.id,
    campaign_id=campaign.id
)
```

## Blob Path Structure

```
user_uploads/{user_id}/campaigns/{campaign_id}/files/{uuid}.{ext}
user_uploads/{user_id}/general/files/{uuid}.{ext}  # non-campaign images
```

## URL Format

```
https://{account_name}.blob.core.windows.net/{container}/{blob_path}
```

## BlobFileMetadata Model

Defined in `app/models.py`:

```python
class BlobFileMetadata(BaseModel):
    name: str              # Base filename
    blob_name: str         # Full path in blob storage
    url: str               # Public URL
    size: int              # Bytes
    last_modified: datetime
    content_type: str | None
```

## Error Handling

- `ResourceNotFoundError` on delete is logged but not raised (idempotent)
- Connection errors raise `HTTPException(500)`
- Missing config raises `HTTPException(500)` with descriptive message

## Database Tracking

Images are logged in `GeneratedImage` table:

```python
class GeneratedImage(Base):
    id: int
    filename: str          # blob_name
    image_url: str         # permanent URL
    prompt: str
    model_used: str
    size: str
    created_at: datetime
    user_id: int
```

Delete with: `crud.delete_generated_image_by_blob_name(db, blob_name, user_id)`
