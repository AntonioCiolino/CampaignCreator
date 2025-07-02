from typing import Optional, List, Dict, Annotated # Added Annotated
import re
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import external_models, crud, orm_models, models # Standardized
from app.db import get_db # Standardized
from app.services.image_generation_service import ImageGenerationService
from app.services.auth_service import get_current_active_user # Standardized
from sse_starlette.sse import EventSourceResponse
from app.services.llm_service import LLMServiceUnavailableError, LLMGenerationError # Standardized
from app.services.llm_factory import get_llm_service # Standardized
from app.services.export_service import HomebreweryExportService # Standardized
from app.external_models.export_models import PrepareHomebreweryPostResponse # Standardized

router = APIRouter()

# --- Helper Functions ---

def _extract_provider_and_model(model_id_with_prefix: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Helper to extract provider and model_specific_id."""
    if model_id_with_prefix and "/" in model_id_with_prefix:
        try:
            provider, model_id = model_id_with_prefix.split("/", 1)
            return provider.lower(), model_id
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model_id_with_prefix format: '{model_id_with_prefix}'. Expected 'provider/model_name'.")
    elif model_id_with_prefix: 
        return None, model_id_with_prefix 
    return None, None

# --- Campaign Endpoints ---

@router.post("/", response_model=models.Campaign)
async def create_new_campaign(
    campaign_input: models.CampaignCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    owner_id = current_user.id # Use authenticated user's ID
    try:
        # crud.create_campaign will now need to handle campaign_input.skip_concept_generation
        db_campaign = await crud.create_campaign(
            db=db,
            campaign_payload=campaign_input, # This now includes skip_concept_generation
            current_user_obj=current_user
        )
        if campaign_input.skip_concept_generation:
            print(f"Campaign {db_campaign.id} created for user {owner_id}. Concept generation was skipped by user.")
        elif db_campaign.concept is None and campaign_input.initial_user_prompt:
            # This condition implies an attempt was made to generate concept but it might have failed in CRUD
            print(f"Campaign {db_campaign.id} created for user {owner_id}, but concept generation might have failed (or prompt was empty but not skipped).")
    # Note: crud.create_campaign now internally handles LLMServiceUnavailableError and LLMGenerationError
    # by logging them and returning a campaign without a concept.
    # The endpoint will only catch errors if crud.create_campaign re-raises them, or for other ValueErrors.
    except LLMServiceUnavailableError as e: # This might be raised if get_llm_service fails in crud
        raise HTTPException(status_code=503, detail=f"LLM Service Error for concept generation: {str(e)}")
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during campaign creation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create campaign due to an external service or unexpected error: {str(e)}")
    return db_campaign

@router.get("/", response_model=List[models.Campaign])
async def list_campaigns(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
    # TODO: Modify crud.get_all_campaigns to filter by current_user.id
):
    campaigns = crud.get_all_campaigns(db=db) # This currently gets ALL campaigns
    # Filter campaigns for the current user (temporary fix until CRUD is updated)
    user_campaigns = [c for c in campaigns if c.owner_id == current_user.id]
    return user_campaigns

@router.get("/{campaign_id}", response_model=models.Campaign)
async def read_campaign(
    campaign_id: int, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    print(f"Attempting to generate concept for campaign_id: {campaign_id}") # DEBUG PRINT
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    return db_campaign

@router.put("/{campaign_id}", response_model=models.Campaign)
async def update_existing_campaign(
    campaign_id: int,
    campaign_update: models.CampaignUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this campaign")

    updated_campaign = await crud.update_campaign(db=db, campaign_id=campaign_id, campaign_update=campaign_update)
    # crud.update_campaign itself doesn't check ownership, so the check above is important.
    # updated_campaign will be None if not found by crud.update_campaign, already handled by initial get.
    return updated_campaign

@router.delete("/{campaign_id}", response_model=models.Campaign, tags=["Campaigns"]) # Added a DELETE endpoint for campaigns
async def delete_campaign_endpoint(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this campaign")

    deleted_campaign_orm = crud.delete_campaign(db=db, campaign_id=campaign_id)
    if deleted_campaign_orm is None: # Should not happen if get_campaign found it
        raise HTTPException(status_code=404, detail="Campaign not found during deletion attempt")
    return deleted_campaign_orm # FastAPI will convert ORM to Pydantic model

# --- Campaign Files Endpoint ---
@router.get("/{campaign_id}/files", response_model=List[models.BlobFileMetadata], tags=["Campaigns", "Files"])
async def list_campaign_files_endpoint(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    image_service: Annotated[ImageGenerationService, Depends(ImageGenerationService)] # Re-use ImageGenerationService
):
    """
    Retrieve a list of files associated with a specific campaign for the current user.
    """
    # Authorization: Check if campaign exists and belongs to the current user
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        # Assuming no other access rules like shared campaigns for now
        raise HTTPException(status_code=403, detail="Not authorized to access files for this campaign")

    try:
        # Call the service method (renamed to list_campaign_files)
        files = await image_service.list_campaign_files(user_id=current_user.id, campaign_id=campaign_id)
        return files
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions from the service layer (e.g., Azure config issues)
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors from the service layer
        print(f"Error retrieving files for user {current_user.id}, campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving campaign files.")

@router.delete("/{campaign_id}/files/{blob_name:path}", status_code=204, tags=["Campaigns", "Files"])
async def delete_campaign_file_endpoint(
    campaign_id: int,
    blob_name: str, # This will capture the full path thanks to :path
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    image_service: Annotated[ImageGenerationService, Depends(ImageGenerationService)]
):
    """
    Deletes a specific file (identified by its full blob_name) associated with a campaign.
    Ensures the campaign belongs to the current user.
    Deletes from both Azure Blob Storage and the GeneratedImage database records.
    """
    # Authorization: Check if campaign exists and belongs to the current user
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete files for this campaign")

    # Step 1: Delete from Database (GeneratedImage record)
    # This also serves as a check if the user is authorized for this specific image record,
    # as delete_generated_image_by_blob_name checks user_id.
    deleted_db_record = crud.delete_generated_image_by_blob_name(db=db, blob_name=blob_name, user_id=current_user.id)

    if deleted_db_record is None:
        # If the DB record wasn't found (or user_id didn't match), it's possible the file doesn't exist
        # in our records, or it's a blob not tracked by GeneratedImage (e.g. direct upload not logged there),
        # or it's a file belonging to another user but under this campaign (less likely with current structure).
        # For now, we'll proceed to attempt blob deletion if the campaign auth passed.
        # A stricter approach might be to 404 here if no DB record.
        # However, if the goal is to ensure a blob is gone, deleting it from storage even if DB record is missing might be desired.
        # Let's assume for now if there's no DB record for THIS user, we might not want to delete the blob
        # unless we are sure only this user could have created it under this campaign.
        # Given `GeneratedImage.user_id`, if no record for this user, then they shouldn't delete.
        # If the file exists in blob but not DB, `delete_image_from_blob_storage` will handle "blob not found" gracefully.
        print(f"No database record found for blob '{blob_name}' and user '{current_user.id}'. It might have been already deleted or not tracked for this user.")
        # Depending on strictness, could raise 404 here.
        # For now, let's allow blob deletion attempt to proceed if campaign auth is okay,
        # as the file might be an "orphan" in blob storage the user wants to remove.

    # Step 2: Delete from Azure Blob Storage
    try:
        await image_service.delete_image_from_blob_storage(blob_name=blob_name)
        # delete_image_from_blob_storage handles "blob not found" by printing a warning but not raising an error,
        # which is acceptable (idempotent delete).
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions from the service layer (e.g., Azure config issues)
        # If the DB delete succeeded but blob delete failed, this is a partial failure state.
        # Consider logging this inconsistency or potential manual cleanup.
        print(f"Database record for '{blob_name}' was deleted (if it existed), but blob storage deletion failed: {http_exc.detail}")
        raise http_exc # Re-raise the original exception from service
    except Exception as e:
        # Catch any other unexpected errors from the service layer
        print(f"Error deleting blob '{blob_name}' from storage: {e}")
        # Similar to above, DB record might be gone but blob deletion failed.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while deleting the file from storage: {str(e)}")

    # If we reach here, operations were successful or handled gracefully (e.g., blob already gone)
    return PlainTextResponse(status_code=204) # No content


# --- LLM-Related Endpoints for Campaigns ---

@router.post("/{campaign_id}/toc", response_model=models.Campaign, tags=["Campaigns", "LLM"])
async def generate_campaign_toc_endpoint(
    campaign_id: int,
    request_body: models.LLMGenerationRequest, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. TOC cannot be generated.")

    try:
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="Current user ORM object not found.")
        provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_name,
            model_id_with_prefix=request_body.model_id_with_prefix,
            campaign=db_campaign
        )

        final_model_id_for_generation = model_specific_id
        if not request_body.model_id_with_prefix: # If no model was specified in the request
            if db_campaign and db_campaign.selected_llm_id and "/" in db_campaign.selected_llm_id:
                _, campaign_model_id = db_campaign.selected_llm_id.split("/", 1)
                final_model_id_for_generation = campaign_model_id
            # Placeholder for user preference logic:
            # elif current_user_orm and hasattr(current_user_orm, 'preferred_llm_id') ...
            # This ensures that if request is generic, we use campaign's specific model, else None for service default.

        # LLM service now returns a List[Dict[str, str]]
        display_toc_list = await llm_service.generate_toc(
            campaign_concept=db_campaign.concept,
            db=db,
            model=final_model_id_for_generation,
            current_user=current_user
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for TOC generation: {str(e)}")
    except LLMGenerationError as e: # This will catch errors from LLM service if content is empty or template not found
        raise HTTPException(status_code=500, detail=f"LLM Generation Error for TOC: {str(e)}")
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="TOC generation is not implemented for the selected LLM provider.")
    except Exception as e:
        print(f"Error during TOC generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Table of Contents: {str(e)}")

    # display_toc_list is now the direct result from the service.
    if not display_toc_list: # Check if the list is empty or None
        error_detail = "Display TOC generation returned an empty list or no content."
        # If you need to log the (now non-existent) raw string, this part of the log would change or be removed.
        # For now, just logging that the list is empty.
        print(f"Error: {error_detail} - List received: {display_toc_list}")
        raise HTTPException(status_code=500, detail=error_detail)

    # The internal parse_toc_string_to_list function is no longer needed
    # as the service now returns the parsed list.

    # The check `if not display_toc_list and display_toc_str:` is no longer needed
    # as display_toc_str doesn't exist and display_toc_list is checked above.

    # Homebrewery TOC is no longer handled here by the endpoint for update content

    updated_campaign_with_toc = crud.update_campaign_toc(
        db=db,
        campaign_id=campaign_id,
        display_toc_content=display_toc_list,
        homebrewery_toc_content=None # Explicitly pass None for homebrewery_toc
    )
    if updated_campaign_with_toc is None:
        # This specific check for campaign existence after update might be redundant if get_campaign above already confirmed it.
        # However, it ensures that crud.update_campaign_toc didn't unexpectedly fail to return the campaign.
        raise HTTPException(status_code=404, detail="Campaign not found when attempting to update TOC after generation.")
    return updated_campaign_with_toc

@router.post("/{campaign_id}/titles", response_model=models.CampaignTitlesResponse, tags=["Campaigns"])
async def generate_campaign_titles_endpoint(
    campaign_id: int,
    request_body: models.LLMGenerationRequest, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    count: int = Query(5, ge=1, le=10)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. Titles cannot be generated.")
    try:
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="Current user ORM object not found.")
        provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_name,
            model_id_with_prefix=request_body.model_id_with_prefix,
            campaign=db_campaign
        )

        final_model_id_for_generation = model_specific_id
        if not request_body.model_id_with_prefix:
            if db_campaign and db_campaign.selected_llm_id and "/" in db_campaign.selected_llm_id:
                _, campaign_model_id = db_campaign.selected_llm_id.split("/", 1)
                final_model_id_for_generation = campaign_model_id
            # Placeholder for user preference logic

        generated_titles = await llm_service.generate_titles( # Added await
            campaign_concept=db_campaign.concept,
            db=db,
            count=count, 
            model=final_model_id_for_generation,
            current_user=current_user # Add this
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for title generation: {str(e)}")
    except LLMGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Title generation is not implemented for the selected LLM provider.")
    except Exception as e:
        print(f"Error during title generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate titles: {str(e)}")

    if not generated_titles:
        raise HTTPException(status_code=500, detail="Title generation resulted in empty content.")
    return models.CampaignTitlesResponse(titles=generated_titles)

@router.post("/{campaign_id}/generate-concept", response_model=models.Campaign, tags=["Campaigns", "LLM"])
async def generate_campaign_concept_manually_endpoint(
    campaign_id: int,
    request_body: models.LLMGenerationRequest, # Reusing this for prompt and model_id
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")

    if not request_body.prompt:
        raise HTTPException(status_code=400, detail="A prompt is required to generate the campaign concept.")

    try:
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="Current user ORM object not found.")

        # Determine LLM service and model ID
        model_id_for_concept = request_body.model_id_with_prefix or db_campaign.selected_llm_id
        if not model_id_for_concept:
            raise HTTPException(status_code=400, detail="LLM model ID not specified in request or campaign settings. Cannot generate concept.")

        provider_name, model_specific_id = _extract_provider_and_model(model_id_for_concept)

        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_name,
            model_id_with_prefix=model_id_for_concept, # Use the resolved model_id_with_prefix
            campaign=db_campaign
        )

        # Generate concept using the LLM service
        # The llm_service.generate_concept might need to be adjusted or a new method created
        # if it doesn't align with this usage pattern (e.g., if it always uses campaign.initial_user_prompt)
        # For now, assume generate_concept can take a direct prompt.
        generated_concept_text = await llm_service.generate_campaign_concept( # Corrected method name
            user_prompt=request_body.prompt, # Pass the prompt from the request, use 'user_prompt'
            db=db,
            current_user=current_user,
            model=model_specific_id,
            # temperature is not directly supported by generate_campaign_concept signature in AbstractLLMService
            # The service method itself would use campaign.temperature or a default.
            # If temperature needs to be passed, the service method signature needs update.
            # For now, removing it from this call to match the abstract method.
        )

        if not generated_concept_text:
            raise LLMGenerationError("LLM generated empty content for the campaign concept.")

        # Update the campaign with the new concept
        campaign_update_payload = models.CampaignUpdate(concept=generated_concept_text)
        updated_campaign = await crud.update_campaign(db=db, campaign_id=campaign_id, campaign_update=campaign_update_payload)

        if updated_campaign is None:
            # This should not happen if db_campaign was found earlier
            raise HTTPException(status_code=500, detail="Failed to update campaign with the new concept.")

        return updated_campaign

    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for concept generation: {str(e)}")
    except LLMGenerationError as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Error for concept: {str(e)}")
    except ValueError as ve: # Catches _extract_provider_and_model errors or other ValueErrors
        raise HTTPException(status_code=400, detail=str(ve))
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Concept generation is not implemented for the selected LLM provider.")
    except Exception as e:
        print(f"Error during manual concept generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate campaign concept: {str(e)}")


@router.post(
    "/{campaign_id}/seed_sections_from_toc",
    # response_model=List[models.CampaignSection], # Removed for SSE
    tags=["Campaigns", "Campaign Sections"]
)
async def seed_sections_from_toc_endpoint(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    auto_populate: bool = False
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")

    print(f"--- Seeding sections for campaign {campaign_id} (SSE) ---")
    if not db_campaign.display_toc:
        print(f"Campaign {campaign_id} has no display_toc. Cannot seed sections.")
        raise HTTPException(status_code=400, detail="No display_toc found for this campaign. Cannot seed sections.")

    # Step 1: Parse TOC (which is now List[Dict[str, str]])
    if not db_campaign.display_toc: # display_toc is List[Dict[str, str]] or None
        print(f"Campaign {campaign_id} display_toc is empty or None. Cannot seed sections.")
        async def empty_toc_generator():
            yield f"data: {json.dumps({'event_type': 'complete', 'message': 'Display TOC is empty. No sections created.'})}\n\n"
        return EventSourceResponse(empty_toc_generator())

    # Extract title and type from each TOC entry
    parsed_toc_entries = []
    for toc_entry in db_campaign.display_toc:
        title = toc_entry.get("title", "").strip()
        if title: # Ensure title exists and is not just whitespace
            type_from_toc = toc_entry.get("type", "generic") or "generic" # Default to "generic" if type is None or empty
            parsed_toc_entries.append({"title": title, "type": type_from_toc})

    if not parsed_toc_entries:
        print(f"No valid titles found in display_toc for campaign {campaign_id}. TOC content: {db_campaign.display_toc}. No sections will be created.")
        async def no_titles_generator():
            yield f"data: {json.dumps({'event_type': 'complete', 'message': 'No valid titles found in TOC. No sections created.'})}\n\n"
        return EventSourceResponse(no_titles_generator())

    print(f"Extracted {len(parsed_toc_entries)} TOC entries for campaign {campaign_id}: {parsed_toc_entries}")

    # Step 2: Delete existing sections (outside the generator)
    print(f"About to delete existing sections for campaign {campaign_id}.")
    deleted_count = crud.delete_sections_for_campaign(db=db, campaign_id=campaign_id)
    print(f"Deleted {deleted_count} existing sections for campaign {campaign_id} before seeding from TOC.")

    # Initialize LLM service (outside the generator, if applicable)
    llm_service_instance = None
    if auto_populate and db_campaign.selected_llm_id and db_campaign.concept:
        try:
            current_user_orm = crud.get_user(db, user_id=current_user.id)
            if not current_user_orm:
                print(f"LLM service initialization failed for SSE: User ORM not found for user {current_user.id}")
                llm_service_instance = None
            else:
                provider_name, _ = _extract_provider_and_model(db_campaign.selected_llm_id)
                llm_service_instance = get_llm_service(
                    db=db,
                    current_user_orm=current_user_orm,
                    provider_name=provider_name, # Extracted from campaign's selected_llm_id
                    model_id_with_prefix=db_campaign.selected_llm_id, # Original prefix from campaign
                    campaign=db_campaign
                )
                print(f"LLM Service for auto-population initialized: {bool(llm_service_instance)}")
        except Exception as e:
            print(f"LLM service initialization failed for SSE auto-population: {type(e).__name__} - {e}")
            llm_service_instance = None # Ensure it's None if init fails
    elif auto_populate:
        print(f"Auto-population requested but campaign.selected_llm_id ('{db_campaign.selected_llm_id}') or campaign.concept (available: {bool(db_campaign.concept)}) is not set appropriately. Skipping LLM generation.")


    async def event_generator():
        total_sections = len(parsed_toc_entries) # Use parsed_toc_entries
        if total_sections == 0:
            # Ensure SSE format is correct with "data:" prefix and double newline
            yield f"data: {json.dumps({'event_type': 'complete', 'message': 'No sections to process.'})}\n\n"
            return

        # Check for LLM service issues before starting the loop if auto-population is requested
        if auto_populate and llm_service_instance is None:
            error_payload = {
                "event_type": "error",
                "message": "Auto-population failed: No LLM provider is configured or available. Please check your API key settings or local LLM setup in the application configuration. Sections will be created with placeholder content."
            }
            try:
                yield f"data: {json.dumps(error_payload)}\n\n"
                await asyncio.sleep(0.01) # Ensure event is sent
            except Exception as e_yield_error:
                print(f"Error yielding initial auto-population error event: {type(e_yield_error).__name__} - {e_yield_error}")
                # If we can't even yield this error, not much else to do for SSE for this request

        for order, toc_item in enumerate(parsed_toc_entries): # Iterate over toc_item
            title = toc_item["title"]
            type_from_toc = toc_item["type"]
            section_content_for_crud = f"Content for '{title}' to be generated."
            section_type_for_llm = type_from_toc # Base type for LLM

            # Define AVAILABLE_SECTION_TYPES - ordered by specificity (more specific first)
            AVAILABLE_SECTION_TYPES = [
                "monster", "character", "npc", "location", "item", "quest", "chapter", "note", "world_detail", "generic"
            ] # "npc" is included as it was in previous logic, "generic" as a fallback

            if type_from_toc.lower() in ["unknown", "generic", "other", ""]:
                title_lower = title.lower()
                for potential_type in AVAILABLE_SECTION_TYPES:
                    # Use \b for whole word matching
                    if re.search(r"\b" + re.escape(potential_type) + r"\b", title_lower):
                        section_type_for_llm = potential_type
                        break # Found the first, most specific match

            if auto_populate and llm_service_instance and db_campaign.concept:
                # Construct prompt based on refined section_type_for_llm
                prompt = ""
                if section_type_for_llm == "character" or section_type_for_llm == "npc": # Combined NPC and Character
                    prompt = f"Generate a detailed description for a character named '{title}'. Include their appearance, personality, motivations, and potential plot hooks related to them."
                elif section_type_for_llm == "location":
                    prompt = f"Describe the location '{title}'. Include its key features, atmosphere, inhabitants (if any), and any notable points of interest or secrets."
                elif section_type_for_llm == "monster":
                    prompt = f"Generate a detailed description for a monster named '{title}'. Include its appearance, abilities, lair, and potential combat tactics."
                elif section_type_for_llm == "item":
                    prompt = f"Describe the magical item '{title}'. Include its appearance, powers, history, and how it can be obtained or used."
                elif section_type_for_llm == "quest":
                    prompt = f"Outline the quest '{title}'. Include the objectives, key NPCs involved, steps to complete it, and potential rewards or consequences."
                elif section_type_for_llm == "chapter": # Added specific prompt for chapter
                    prompt = f"Outline the main events and encounters for the chapter titled '{title}'. Provide a brief overview of the objectives, challenges, and potential rewards."
                # Note: "note", "world_detail" will fall into the else "generic" category for now, which is acceptable.
                else: # Generic or other specific types from TOC not explicitly handled above
                    prompt = f"Generate content for a section titled '{title}' of type '{section_type_for_llm}' as part of a larger campaign document."

                try:
                    print(f"Attempting LLM generation for section: '{title}' (Type for LLM: {section_type_for_llm})")
                    _, model_specific_id_for_call = _extract_provider_and_model(db_campaign.selected_llm_id)
                    generated_llm_content = await llm_service_instance.generate_section_content(
                        db_campaign=db_campaign, # Changed campaign_concept to db_campaign
                        db=db,
                        current_user=current_user,
                        existing_sections_summary=None,
                        section_creation_prompt=prompt,
                        section_title_suggestion=title,
                        section_type=section_type_for_llm,
                        model=model_specific_id_for_call
                    )
                    if generated_llm_content:
                        section_content_for_crud = generated_llm_content
                        print(f"LLM content generated for '{title}' (excerpt): {section_content_for_crud[:50]}...")
                    else:
                        print(f"LLM generated empty content for section '{title}'. Using placeholder.")
                        error_payload = {
                            "event_type": "error",
                            "message": f"Auto-population for section '{title}' failed: LLM returned empty content. Check configuration. Using placeholder content."
                        }
                        try:
                            yield f"data: {json.dumps(error_payload)}\n\n"
                            await asyncio.sleep(0.01)
                        except Exception as e_yield_error:
                            print(f"Error yielding empty content error event for '{title}': {type(e_yield_error).__name__} - {e_yield_error}")
                except Exception as e_llm:
                    print(f"LLM generation failed for section '{title}': {type(e_llm).__name__} - {e_llm}. Using placeholder.")
                    error_payload = {
                        "event_type": "error",
                        "message": f"Auto-population for section '{title}' failed: {type(e_llm).__name__} - {e_llm}. Check LLM provider configuration. Using placeholder content."
                    }
                    try:
                        yield f"data: {json.dumps(error_payload)}\n\n"
                        await asyncio.sleep(0.01)
                    except Exception as e_yield_error:
                        print(f"Error yielding LLM exception error event for '{title}': {type(e_yield_error).__name__} - {e_yield_error}")

            # Create section in DB, passing the original type from TOC
            created_section_orm = crud.create_section_with_placeholder_content(
                db=db,
                campaign_id=campaign_id,
                title=title,
                order=order,
                placeholder_content=section_content_for_crud,
                type=type_from_toc # Pass the type from the TOC to be saved in DB
            )
            pydantic_section = models.CampaignSection.from_orm(created_section_orm)

            current_progress = round(((order + 1) / total_sections) * 100, 2)
            event_payload = {
                "event_type": "section_update",
                "progress_percent": current_progress,
                "current_section_title": title,
                "section_data": pydantic_section.model_dump()
            }

            try:
                yield f"data: {json.dumps(event_payload)}\n\n"
                await asyncio.sleep(0.01)
            except Exception as e_yield:
                print(f"Error yielding SSE event for section '{title}': {type(e_yield).__name__} - {e_yield}. Stopping.")
                # Optionally, send one last error event to the client if possible
                error_event = {"event_type": "error", "message": f"Failed to stream update for section '{title}'. Process halted."}
                try:
                    yield f"data: {json.dumps(error_event)}\n\n"
                except:
                    pass # If this also fails, nothing more can be done here
                break # Stop processing further sections

        # After the loop completes (or if broken by yield error)
        # This completion event might not be sent if the client disconnects due to the break.
        completion_message = "Section seeding process finished."
        if order + 1 < total_sections : # if loop was broken early
             completion_message = f"Section seeding process interrupted after processing {order + 1} of {total_sections} sections."

        completion_event = {"event_type": "complete", "message": completion_message, "total_sections_processed": order +1}
        try:
            yield f"data: {json.dumps(completion_event)}\n\n"
        except Exception as e_complete:
            print(f"Error yielding final completion event: {type(e_complete).__name__} - {e_complete}")

        print(f"--- Finished SSE event_generator for campaign {campaign_id} ---")

    return EventSourceResponse(event_generator())

# --- Campaign Section Endpoints ---

# Pydantic model for the request body of section order update
class SectionOrderUpdate(BaseModel): # Changed to use pydantic.BaseModel
    section_ids: List[int]

@router.put("/{campaign_id}/sections/order", status_code=204, tags=["Campaign Sections"])
async def update_section_order_endpoint(
    campaign_id: int,
    order_update: SectionOrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Updates the order of sections within a campaign.
    The list of section_ids should be in the desired new order.
    """
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")

    # Fetch all sections for the campaign to ensure all IDs are valid and belong to this campaign
    existing_sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=None) # Get all
    existing_section_ids = {section.id for section in existing_sections}

    if len(order_update.section_ids) != len(existing_section_ids):
        raise HTTPException(status_code=400, detail="The number of section IDs provided does not match the number of sections in the campaign.")

    for section_id in order_update.section_ids:
        if section_id not in existing_section_ids:
            raise HTTPException(status_code=400, detail=f"Section ID {section_id} is invalid or does not belong to campaign {campaign_id}.")
    
    try:
        await crud.update_section_order(db=db, campaign_id=campaign_id, ordered_section_ids=order_update.section_ids)
        return PlainTextResponse(status_code=204, content="") # No content response
    except Exception as e:
        # Log the error e
        print(f"Error updating section order for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while updating section order.")


@router.post("/{campaign_id}/sections", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def create_new_campaign_section_endpoint(
    campaign_id: int,
    section_input: models.CampaignSectionCreateInput,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")
    if not db_campaign.concept and not section_input.prompt:
        raise HTTPException(status_code=400, detail="Campaign concept is missing and no specific prompt for section. Section content cannot be generated.")

    existing_sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    existing_sections_summary = "; ".join([s.title for s in existing_sections if s.title]) if existing_sections else None

    type_from_input = section_input.type or "generic" # Default to "generic" if not provided

    try:
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="Current user ORM object not found.")
        provider_name, model_specific_id = _extract_provider_and_model(section_input.model_id_with_prefix)
        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_name, # Already extracted
            model_id_with_prefix=section_input.model_id_with_prefix,
            campaign=db_campaign # Pass the fetched campaign
        )

        final_model_id_for_generation = model_specific_id
        if not section_input.model_id_with_prefix: # If no model specified in request
            if db_campaign and db_campaign.selected_llm_id and "/" in db_campaign.selected_llm_id:
                _, campaign_model_id = db_campaign.selected_llm_id.split("/", 1)
                final_model_id_for_generation = campaign_model_id
            # Placeholder for user preference logic

        generated_content = await llm_service.generate_section_content(
            db_campaign=db_campaign, # Changed campaign_concept to db_campaign
            db=db,
            existing_sections_summary=existing_sections_summary,
            section_creation_prompt=section_input.prompt,
            section_title_suggestion=section_input.title,
            section_type=type_from_input,
            model=final_model_id_for_generation,
            current_user=current_user # Add this
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for section content generation: {str(e)}")
    except LLMGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Section content generation is not implemented for the selected LLM provider.")
    except Exception as e: 
        print(f"Error during section content generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate section content: {str(e)}")

    if not generated_content:
        raise HTTPException(status_code=500, detail="LLM generated empty content for the section.")

    new_section_title = section_input.title if section_input.title else "Untitled Section"

    try:
        db_section = crud.create_campaign_section(
            db=db,
            campaign_id=campaign_id,
            section_title=new_section_title,
            section_content=generated_content,
            section_type=type_from_input # Pass the type to CRUD
        )
    except Exception as e:
        print(f"Error saving new section for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save the new campaign section.")
    return db_section

@router.put("/{campaign_id}/sections/{section_id}", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def update_campaign_section_endpoint(
    campaign_id: int,
    section_id: int,
    section_data: models.CampaignSectionUpdateInput,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    # First, check if the campaign itself belongs to the user
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify sections for this campaign")

    updated_section = crud.update_campaign_section(
        db=db, 
        section_id=section_id, 
        campaign_id=campaign_id, 
        section_update_data=section_data
    ) # This CRUD already checks if section belongs to campaign
    if updated_section is None:
        raise HTTPException(status_code=404, detail="Campaign section not found or does not belong to the specified campaign.")
    return updated_section

@router.get("/{campaign_id}/sections", response_model=models.CampaignSectionListResponse, tags=["Campaign Sections"])
async def list_campaign_sections(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view sections for this campaign")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    return {"sections": sections}

@router.delete("/{campaign_id}/sections/{section_id}", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def delete_campaign_section_endpoint(
    campaign_id: int,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    # First, check if the campaign itself belongs to the user
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete sections for this campaign")

    deleted_section = crud.delete_campaign_section(db=db, section_id=section_id, campaign_id=campaign_id)
    # This CRUD already checks if section belongs to campaign
    if deleted_section is None:
        raise HTTPException(status_code=404, detail="Campaign section not found or does not belong to this campaign.")
    return deleted_section

# --- Export Endpoints ---

@router.get("/{campaign_id}/export/homebrewery", tags=["Campaigns", "Export"])
async def export_campaign_homebrewery(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) 
    export_service = HomebreweryExportService()
    try:
        # Ensure db and current_user are passed
        formatted_text = await export_service.format_campaign_for_homebrewery(
            campaign=db_campaign,
            sections=sections,
            db=db,
            current_user=current_user
        )
    except Exception as e:
        print(f"Error during Homebrewery export formatting for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to format campaign for Homebrewery export: {str(e)}")
    filename_title_part = db_campaign.title.replace(' ', '_') if db_campaign.title else 'campaign_export'
    filename = f"{filename_title_part}_{db_campaign.id}_homebrewery.md"
    return PlainTextResponse(
        content=formatted_text, 
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )

@router.get("/{campaign_id}/full_content", response_model=models.CampaignFullContentResponse, tags=["Campaigns"])
async def get_campaign_full_content_endpoint(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000)
    all_content_parts = []
    if db_campaign.concept:
        concept_title = db_campaign.title if db_campaign.title else "Campaign Concept"
        all_content_parts.append(f"# {concept_title}\n\n{db_campaign.concept}\n\n")

    # Use display_toc (which is List[Dict[str, str]]) and format it
    if db_campaign.display_toc:
        toc_str_parts = []
        for entry in db_campaign.display_toc:
            title = entry.get('title', 'Untitled')
            # type_info = f" (Type: {entry.get('type', 'unknown')})" # Optionally include type
            toc_str_parts.append(f"- {title}") # Simple list format
        if toc_str_parts:
            all_content_parts.append(f"## Table of Contents\n\n{chr(10).join(toc_str_parts)}\n\n")

    for section in sections:
        if section.title:
            all_content_parts.append(f"## {section.title}\n\n{section.content}\n\n")
        else:
            all_content_parts.append(f"{section.content}\n\n")
    full_content_str = "".join(all_content_parts).strip()
    response = external_models.CampaignFullContentResponse(
        campaign_id=db_campaign.id,
        title=db_campaign.title,
        full_content=full_content_str
    )
    return response

@router.get("/{campaign_id}/prepare_for_homebrewery", response_model=PrepareHomebreweryPostResponse, tags=["Campaigns", "Export"])
async def prepare_campaign_for_homebrewery_posting(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000)
    export_service = HomebreweryExportService()
    try:
        # Ensure db and current_user are passed
        markdown_content = await export_service.format_campaign_for_homebrewery(
            campaign=db_campaign,
            sections=sections,
            db=db,
            current_user=current_user
        )
    except Exception as e:
        print(f"Error during Homebrewery content generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Homebrewery Markdown: {str(e)}")
    homebrewery_new_url = "https://homebrewery.naturalcrit.com/new"
    filename_title_part = db_campaign.title.replace(' ', '_') if db_campaign.title else 'campaign_export'
    filename_suggestion = f"{filename_title_part}_{db_campaign.id}_homebrewery.md"
    return PrepareHomebreweryPostResponse(
        markdown_content=markdown_content,
        homebrewery_new_url=homebrewery_new_url,
        filename_suggestion=filename_suggestion
    )

@router.post("/{campaign_id}/sections/{section_id}/regenerate", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def regenerate_campaign_section_endpoint(
    campaign_id: int,
    section_id: int,
    section_input: models.SectionRegenerateInput,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this campaign")

    db_section = crud.get_section(db=db, section_id=section_id, campaign_id=campaign_id)
    if db_section is None:
        raise HTTPException(status_code=404, detail="Campaign section not found")

    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. Section content cannot be regenerated without it.")

    # Determine title for regeneration
    current_title = section_input.new_title if section_input.new_title is not None else db_section.title
    # Ensure current_title is a string, even if db_section.title was None and new_title wasn't provided.
    if current_title is None:
        current_title = "Untitled Section"


    # Determine title for regeneration (remains the same)
    current_title = section_input.new_title if section_input.new_title is not None else db_section.title
    if current_title is None:
        current_title = "Untitled Section"

    # Prioritize input type, then existing DB type, then generic
    determined_section_type = section_input.section_type or db_section.type or "generic"

    # Prepare comprehensive context from backend
    backend_context = {
        "campaign_concept": db_campaign.concept,
        "campaign_title": db_campaign.title,
        "section_title": current_title, # current_title of the section being regenerated
        "section_type": determined_section_type, # current type of the section
        # campaign_characters: needs to be fetched and summarized
        # existing_sections_summary: needs to be fetched (excluding current section)
    }

    # Fetch and summarize campaign characters
    campaign_chars = crud.get_characters_by_campaign(db, campaign_id=campaign_id)
    if campaign_chars:
        backend_context["campaign_characters"] = "; ".join([char.name + (f" ({char.description[:30]}...)" if char.description else "") for char in campaign_chars])
    else:
        backend_context["campaign_characters"] = "No specific characters defined for this campaign yet."

    # Fetch and summarize other sections
    all_campaign_sections_for_summary = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=None)
    other_sections_summary_list = [
        s.title for s in all_campaign_sections_for_summary if s.id != section_id and s.title
    ]
    if other_sections_summary_list:
        backend_context["existing_sections_summary"] = "; ".join(other_sections_summary_list)
    else:
        backend_context["existing_sections_summary"] = "This is the first section or other sections have no titles."


    feature_template = None
    final_context_for_template = {}

    if section_input.feature_id:
        # Snippet feature workflow
        db_feature = crud.get_feature(db, feature_id=section_input.feature_id)
        if not db_feature:
            raise HTTPException(status_code=404, detail=f"Feature with ID {section_input.feature_id} not found.")
        if db_feature.feature_category == "FullSection": # Basic check
            print(f"Warning: Feature {db_feature.name} (ID: {db_feature.id}) is a FullSection feature but was called with a feature_id, likely for a snippet. Proceeding, but this might indicate a UI/logic mismatch.")

        feature_template = db_feature.template
        # Combine frontend context with backend context, frontend takes precedence for shared keys
        final_context_for_template = {**backend_context, **(section_input.context_data or {})}
        # Ensure selected_text from payload is used as the primary prompt for snippet if template expects it
        # The feature_template itself should contain placeholders like {selected_text}
        # The `section_input.new_prompt` (which is editorSelectionText) should be part of context_data if needed by template.
        if 'selected_text' not in final_context_for_template and section_input.new_prompt:
             final_context_for_template['selected_text'] = section_input.new_prompt

        # For snippet features, the new_prompt from input is often the main subject.
        # The feature template will dictate how it's used.
        # We don't auto-generate a prompt like in the old logic here.

    else:
        # Type-driven full section generation workflow
        master_feature = crud.get_master_feature_for_type(db, section_type=determined_section_type)
        if not master_feature:
            # Fallback to a very generic prompt if no master feature is found
            print(f"Warning: No master feature found for section type '{determined_section_type}'. Using a generic generation prompt.")
            # This is the old generic prompt logic
            if determined_section_type == "NPC":
                feature_template = "Generate a detailed description for an NPC named '{section_title}'. Include their appearance, personality, motivations, and potential plot hooks related to them. Campaign Context: {campaign_concept}. Other sections: {existing_sections_summary}. Characters: {campaign_characters}."
            elif determined_section_type == "Location":
                feature_template = "Describe the location '{section_title}'. Include its key features, atmosphere, inhabitants (if any), and any notable points of interest or secrets. Campaign Context: {campaign_concept}. Other sections: {existing_sections_summary}."
            elif determined_section_type == "Chapter/Quest": # Assuming Chapter and Quest use similar master features
                feature_template = "Outline the main events and encounters for the adventure chapter titled '{section_title}'. Provide a brief overview of the objectives, challenges, and potential rewards. Campaign Context: {campaign_concept}. Other sections: {existing_sections_summary}. Characters: {campaign_characters}."
            else: # Generic
                feature_template = "Generate content for a section titled '{section_title}' of type '{section_type}' as part of a larger campaign document. Campaign Context: {campaign_concept}. Other sections: {existing_sections_summary}. Characters: {campaign_characters}."
        else:
            feature_template = master_feature.template

        # For full generation, context_data from payload is less likely to be used, backend context is primary
        final_context_for_template = backend_context
        # If section_input.new_prompt has content, it might be user's specific instruction for full gen.
        # Add it to context if feature template is designed to use it e.g. as {user_instructions}
        if section_input.new_prompt:
            final_context_for_template['user_instructions'] = section_input.new_prompt


    # Render the template
    # A more robust templating engine like Jinja2 would be better for complex templates.
    # For now, simple string replacement.
    final_prompt_for_llm = feature_template
    for key, value in final_context_for_template.items():
        final_prompt_for_llm = final_prompt_for_llm.replace(f"{{{key}}}", str(value))

    # Check for any unreplaced placeholders (optional, for debugging)
    # unreplaced_placeholders = re.findall(r"\{[a-zA-Z0-9_]+\}", final_prompt_for_llm)
    # if unreplaced_placeholders:
    #     print(f"Warning: Unreplaced placeholders in final prompt: {unreplaced_placeholders}")


    # Initialize LLM Service (remains similar)
    llm_model_to_use = section_input.model_id_with_prefix or db_campaign.selected_llm_id
    if not llm_model_to_use:
        # Fallback if no model is specified in input or campaign defaults
        raise HTTPException(status_code=400, detail="LLM model ID not specified in request or campaign settings. Cannot regenerate section.")

    try:
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="Current user ORM object not found.")

        provider_name, model_specific_id = _extract_provider_and_model(llm_model_to_use)
        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_name,
            model_id_with_prefix=llm_model_to_use, # Pass the determined model_id_with_prefix
            campaign=db_campaign # Add this
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service unavailable: {str(e)}")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid LLM model ID format ('{llm_model_to_use}'): {ve}")

    # Fetch existing sections summary for context -- This is now done above as part of backend_context

    # Call LLM Service using the generic generate_text method
    try:
        print(f"Regenerating section '{current_title}' (ID: {section_id}) using LLM: {llm_model_to_use} with final prompt (first 100 chars): '{final_prompt_for_llm[:100]}...'")

        # Convert current_user (Pydantic model) to ORM model if needed by get_llm_service,
        # but llm_service.generate_text expects Pydantic user.
        # current_user_orm is already fetched and available.

        # The llm_service instance is already initialized.
        # We need to ensure generate_text can use the fully constructed prompt (final_prompt_for_llm)
        # and doesn't try to re-fetch campaign concept etc. if they are already in the prompt.
        # The dummy generate_text tries to fill placeholders, which is what we want.

        generated_content = await llm_service.generate_text(
            prompt=final_prompt_for_llm, # This is the fully rendered template
            current_user=current_user,   # Pass Pydantic user model
            db=db,
            model=model_specific_id,     # Specific model ID for the provider
            temperature=db_campaign.temperature if db_campaign.temperature is not None else 0.7, # Use campaign temp or default
            # max_tokens can be default or configured
            # Context fields for generate_text are not strictly needed if prompt is pre-rendered,
            # but passing them for completeness or if service uses them for other logic.
            db_campaign=db_campaign,
            section_title_suggestion=current_title,
            section_type=determined_section_type,
            section_creation_prompt=section_input.new_prompt if section_input.feature_id else None # Pass original user prompt only if it's a snippet modification
        )

        if not generated_content:
            raise HTTPException(status_code=500, detail="LLM generated empty content during regeneration.")

    except LLMGenerationError as e: # This comes from the LLM service if it raises it
        raise HTTPException(status_code=500, detail=f"LLM Generation Error during regeneration: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during LLM regeneration for section ID {section_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during section regeneration: {str(e)}")

    # Prepare data for update
    section_update_payload = models.CampaignSectionUpdateInput(content=generated_content)
    if section_input.new_title is not None:
        section_update_payload.title = section_input.new_title
    # Update the type field only if it was explicitly provided in the input
    if section_input.section_type is not None:
        section_update_payload.type = section_input.section_type

    # Update Section using CRUD
    updated_section = crud.update_campaign_section(
        db=db,
        section_id=section_id,
        campaign_id=campaign_id,
        section_update_data=section_update_payload
    )

    if updated_section is None:
        # This case implies section was not found by crud.update_campaign_section, which is unlikely
        # if crud.get_section succeeded earlier and IDs are correct.
        # Could also mean an issue within the update logic itself.
        raise HTTPException(status_code=500, detail="Failed to update section after regeneration. Section may have been deleted.")

    return updated_section

# The Config class should be at the module level if it's meant for Pydantic model configuration,
# or within each Pydantic model that needs it.
# For example, if SectionOrderUpdate needed it:
# class SectionOrderUpdate(external_models.BaseModel):
# section_ids: List[int]
# class Config:
# from_attributes = True
#
# However, usually external_models.BaseModel would already have its Config.
# If this `class Config` was erroneously placed at the end of the file, it should be removed or moved.
# For now, I'll assume it's not needed here or handled by BaseModel.
# class Config:
#     from_attributes = True


# --- Moodboard Image Upload Endpoint ---

class MoodboardImageUploadResponse(BaseModel):
    image_url: str
    campaign: models.Campaign # Use the existing Pydantic model for Campaign

@router.post(
    "/{campaign_id}/moodboard/upload",
    response_model=MoodboardImageUploadResponse,
    tags=["Campaigns", "Mood Board"]
)
async def upload_moodboard_image_for_campaign(
    campaign_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Authentication & Authorization
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload images to this campaign")

    # Image Processing & Storage
    image_service = ImageGenerationService()
    image_bytes = await file.read()

    prompt_text = f"Uploaded moodboard image for campaign {campaign_id}: {file.filename}"
    model_used = "direct_upload"
    size_used = "original" # Placeholder as actual size might vary

    try:
        print(f"[MoodboardUpload] About to save image for campaign_id: {campaign_id}, user_id: {current_user.id}, filename: {file.filename}") # DIAGNOSTIC
        permanent_image_url = await image_service._save_image_and_log_db(
            prompt=prompt_text,
            model_used=model_used,
            size_used=size_used,
            db=db,
            image_bytes=image_bytes,
            user_id=current_user.id,
            campaign_id=campaign_id, # Pass campaign_id here
            original_filename_from_api=file.filename
        )
    except HTTPException as e:
        # If _save_image_and_log_db raises an HTTPException (e.g. Azure config issue), re-raise it
        raise e
    except Exception as e:
        # Catch any other unexpected errors during image saving
        print(f"Error saving uploaded moodboard image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded image: {str(e)}")

    if not permanent_image_url:
        raise HTTPException(status_code=500, detail="Image URL was not generated after saving.")

    # Update Campaign
    current_mood_board_urls = list(db_campaign.mood_board_image_urls) if db_campaign.mood_board_image_urls else []
    current_mood_board_urls.append(permanent_image_url)

    campaign_update_payload = models.CampaignUpdate(mood_board_image_urls=current_mood_board_urls)

    updated_campaign = await crud.update_campaign(
        db=db,
        campaign_id=campaign_id,
        campaign_update=campaign_update_payload
    )

    if not updated_campaign:
        # This should ideally not happen if the campaign existed and update logic is sound
        raise HTTPException(status_code=500, detail="Failed to update campaign with new moodboard image.")

    return MoodboardImageUploadResponse(image_url=permanent_image_url, campaign=updated_campaign)
