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
        db_campaign = await crud.create_campaign(
            db=db, 
            campaign_payload=campaign_input,
            current_user_obj=current_user # Pass the full current_user object
        )
        if db_campaign.concept is None and campaign_input.initial_user_prompt:
            print(f"Campaign {db_campaign.id} created for user {owner_id}, but concept generation might have failed or was skipped.")
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

# --- LLM-Related Endpoints ---

@router.post("/{campaign_id}/toc", response_model=models.Campaign, tags=["Campaigns"])
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
        provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=request_body.model_id_with_prefix)

        # LLM service now returns a List[Dict[str, str]]
        display_toc_list = await llm_service.generate_toc(
            campaign_concept=db_campaign.concept,
            db=db,
            model=model_specific_id,
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
        provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=request_body.model_id_with_prefix)
        generated_titles = await llm_service.generate_titles( # Added await
            campaign_concept=db_campaign.concept,
            db=db,
            count=count, 
            model=model_specific_id,
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
            provider_name, _ = _extract_provider_and_model(db_campaign.selected_llm_id)
            llm_service_instance = get_llm_service(provider_name=provider_name, model_id_with_prefix=db_campaign.selected_llm_id)
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
                        campaign_concept=db_campaign.concept,
                        db=db,
                        current_user=current_user, # Add this line
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
        provider_name, model_specific_id = _extract_provider_and_model(section_input.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=section_input.model_id_with_prefix)
        generated_content = await llm_service.generate_section_content(
            campaign_concept=db_campaign.concept or "A general creative writing piece.",
            db=db,
            existing_sections_summary=existing_sections_summary,
            section_creation_prompt=section_input.prompt,
            section_title_suggestion=section_input.title,
            section_type=type_from_input,
            model=model_specific_id,
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


    # Determine section type and prompt
    final_prompt = section_input.new_prompt
    # Prioritize input type, then existing DB type, then generic
    determined_section_type_for_llm = section_input.section_type or db_section.type or "generic"

    if not final_prompt:
        # If type was not in input and still generic (i.e., db_section.type was also generic or None), try to infer from title
        if not section_input.section_type and determined_section_type_for_llm.lower() in ["unknown", "generic", "other", ""]:
            title_lower = current_title.lower()
            if determined_section_type_for_llm.lower() in ["unknown", "generic", "other", ""]:
                if "npc" in title_lower or "character" in title_lower:
                    determined_section_type_for_llm = "NPC"
                elif "location" in title_lower or "place" in title_lower:
                    determined_section_type_for_llm = "Location"
                elif "chapter" in title_lower or "quest" in title_lower or "adventure" in title_lower:
                    determined_section_type_for_llm = "Chapter/Quest"

        # Construct prompt based on determined type and title
        if determined_section_type_for_llm == "NPC":
            final_prompt = f"Generate a detailed description for an NPC named '{current_title}'. Include their appearance, personality, motivations, and potential plot hooks related to them."
        elif determined_section_type_for_llm == "Location":
            final_prompt = f"Describe the location '{current_title}'. Include its key features, atmosphere, inhabitants (if any), and any notable points of interest or secrets."
        elif determined_section_type_for_llm == "Chapter/Quest":
            final_prompt = f"Outline the main events and encounters for the adventure chapter titled '{current_title}'. Provide a brief overview of the objectives, challenges, and potential rewards."
        else: # Generic or other specific types
            final_prompt = f"Generate content for a section titled '{current_title}' of type '{determined_section_type_for_llm}' as part of a larger campaign document."

    # Initialize LLM Service
    llm_model_to_use = section_input.model_id_with_prefix if section_input.model_id_with_prefix else db_campaign.selected_llm_id
    if not llm_model_to_use:
        # Fallback if no model is specified in input or campaign defaults
        raise HTTPException(status_code=400, detail="LLM model ID not specified in request or campaign settings. Cannot regenerate section.")

    try:
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="Current user ORM object not found.")

        provider_name, model_specific_id = _extract_provider_and_model(llm_model_to_use)
        llm_service = get_llm_service(db=db, current_user_orm=current_user_orm, provider_name=provider_name, model_id_with_prefix=llm_model_to_use)
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service unavailable: {str(e)}")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid LLM model ID format ('{llm_model_to_use}'): {ve}")

    # Fetch existing sections summary for context
    all_campaign_sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=None)
    other_sections_summary = "; ".join(
        [s.title for s in all_campaign_sections if s.id != section_id and s.title]
    ) if all_campaign_sections else None

    # Call LLM Service
    try:
        print(f"Regenerating section '{current_title}' (ID: {section_id}) using LLM: {llm_model_to_use}")
        generated_content = await llm_service.generate_section_content(
            campaign_concept=db_campaign.concept,
            db=db,
            existing_sections_summary=other_sections_summary,
            section_creation_prompt=final_prompt,
            section_title_suggestion=current_title,
            section_type=determined_section_type_for_llm,
            model=model_specific_id,
            current_user=current_user # Add this
        )
        if not generated_content:
            raise HTTPException(status_code=500, detail="LLM generated empty content during regeneration.")

    except LLMGenerationError as e:
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
        permanent_image_url = await image_service._save_image_and_log_db(
            prompt=prompt_text,
            model_used=model_used,
            size_used=size_used,
            db=db,
            image_bytes=image_bytes,
            user_id=current_user.id,
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
