import json
from typing import Optional, List, Dict, Any, Union, Annotated # Added Annotated

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.import_service import ImportService # DEFAULT_OWNER_ID removed from here
from app.external_models.import_models import ImportSummaryResponse, ImportErrorDetail
from app.models import User as UserModel # For current_user type hint
from app.services.auth_service import get_current_active_user # For auth dependency


router = APIRouter()

# Dependency for ImportService
def get_import_service():
    return ImportService()

@router.post(
    "/json_file", 
    response_model=ImportSummaryResponse, 
    tags=["Import"],
    summary="Import campaign data from a JSON file."
)
async def import_json_file_endpoint(
    db: Annotated[Session, Depends(get_db)],
    import_service: Annotated[ImportService, Depends(get_import_service)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    file: UploadFile = File(..., description="JSON file containing campaign data, potentially exported from another Campaign Crafter instance or compatible system."),
    target_campaign_id: Optional[int] = Form(None, description="If provided, import data into this existing campaign ID. Otherwise, a new campaign is created.")
):
    """
    Imports campaign data from a JSON file.
    The JSON file can contain:
    1.  A single JSON object representing a full campaign structure (e.g., `{"title": "My Campaign", "sections": [{"title": "Intro", "content": "..."}]}`).
        If `target_campaign_id` is NOT provided, a new campaign is created.
        If `target_campaign_id` IS provided, only the 'sections' from the JSON are imported into the existing campaign.
    2.  A JSON array of section objects (e.g., `[{"title": "Section 1", "content": "..."}, {"title": "Section 2", "content": "..."}]`).
        If `target_campaign_id` is NOT provided, a new campaign is created (e.g., titled "Imported from JSON Sections") for these sections.
        If `target_campaign_id` IS provided, these sections are added to the existing campaign.
    """
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .json file.")

    try:
        file_content_bytes = await file.read()
        file_content_str = file_content_bytes.decode('utf-8')
        parsed_json_data: Union[Dict[str, Any], List[Dict[str, Any]]] = json.loads(file_content_str)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding is not valid UTF-8.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in the uploaded file.")
    except Exception as e:
        # Catch other potential errors during file read/decode
        raise HTTPException(status_code=500, detail=f"Error processing uploaded file: {str(e)}")
    finally:
        await file.close()

    try:
        summary = import_service.import_from_json_content(
            parsed_json_data=parsed_json_data,
            owner_id=current_user.id,
            db=db,
            target_campaign_id=target_campaign_id
        )
        return summary
    except HTTPException: # Re-raise HTTPExceptions from service if any
        raise
    except Exception as e:
        # Catch-all for unexpected errors from the service layer
        print(f"Error during JSON import service call: {type(e).__name__} - {e}")
        errors = [ImportErrorDetail(error=f"An unexpected error occurred during import: {str(e)}")]
        return ImportSummaryResponse(
            message="Import process failed due to an unexpected server error.",
            errors=errors
        )

@router.post(
    "/zip_file",
    response_model=ImportSummaryResponse,
    tags=["Import"],
    summary="Import campaign data from a Zip archive."
)
async def import_zip_file_endpoint(
    db: Annotated[Session, Depends(get_db)],
    import_service: Annotated[ImportService, Depends(get_import_service)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    file: UploadFile = File(..., description="ZIP file containing campaign data, typically exported from Homebrewery or a similar Markdown-based format."),
    target_campaign_id: Optional[int] = Form(None, description="If provided, import data into this existing campaign ID. Otherwise, a new campaign is created."),
    process_folders_as_structure: bool = Form(False, description="If true, interpret folder structure within the ZIP as campaign sections and sub-sections.")
):
    """
    Imports campaign data from a Zip archive containing .txt and/or .json files.

    - **.txt files**: Each .txt file is treated as a section. The filename (without extension) is used as the section title, and its content as the section body.
    - **.json files**: Can be a single Campaign object or a list of Section objects, processed like the `/json_file` import.
        - If a .json file represents a full Campaign and `target_campaign_id` is not set, it might create a new campaign.
    - **`target_campaign_id`**:
        - If provided, all extracted valid sections are added to this existing campaign. JSON files representing full campaigns will have their sections imported into this target campaign.
        - If not provided:
            - Loose .txt/.json (section lists) at the root of the Zip will be grouped into one new campaign (e.g., "Imported from Zip").
            - JSON files representing full campaigns at the root will create new campaigns.
    - **`process_folders_as_structure`**:
        - If `False` (default): The Zip is treated as a flat collection of files. Folder hierarchy is largely ignored, though file paths might still inform titles.
        - If `True`:
            - If `target_campaign_id` is **not set**: Top-level folders in the Zip can become titles of new campaigns. Files within these folders become sections of that campaign.
            - If `target_campaign_id` **is set**: Top-level folders can become new top-level sections within the existing campaign. Files within those folders become sub-content (this interpretation needs refinement in service).
            - *Note: Deeply nested structures might have simplified interpretations.*
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .zip file.")

    try:
        file_content_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading uploaded Zip file: {str(e)}")
    finally:
        await file.close()

    try:
        summary = import_service.import_from_zip_file(
            file_bytes=file_content_bytes,
            owner_id=current_user.id,
            db=db,
            target_campaign_id=target_campaign_id,
            process_folders_as_structure=process_folders_as_structure
        )
        return summary
    except HTTPException: # Re-raise HTTPExceptions from service if any
        raise
    except Exception as e:
        print(f"Error during Zip import service call: {type(e).__name__} - {e}")
        errors = [ImportErrorDetail(error=f"An unexpected error occurred during Zip import: {str(e)}")]
        return ImportSummaryResponse(
            message="Import process failed due to an unexpected server error.",
            errors=errors
        )
