from typing import Optional, List
import re # Add import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel # Added BaseModel import

from app import external_models, crud, orm_models, models
from app.db import get_db 
from app.services.llm_service import LLMServiceUnavailableError, LLMGenerationError # Updated import
from app.services.llm_factory import get_llm_service
from app.services.export_service import HomebreweryExportService
from app.external_models.export_models import PrepareHomebreweryPostResponse

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
    campaign_input: models.CampaignCreate, # <--- Changed
    db: Session = Depends(get_db)
):
    owner_id = 1  # Placeholder
    try:
        # Note: campaign_input is passed as the 'campaign' argument to crud.create_campaign
        # This is valid because CampaignCreate is a subclass of CampaignBase.
        db_campaign = await crud.create_campaign(
            db=db, 
            campaign_payload=campaign_input,
            owner_id=owner_id
        )
        if db_campaign.concept is None and campaign_input.initial_user_prompt: # <--- Changed
            print(f"Campaign {db_campaign.id} created, but concept generation might have failed or was skipped (e.g. LLM unavailable/error).")
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
    db: Session = Depends(get_db)
):
    campaigns = crud.get_all_campaigns(db=db)
    # No HTTPException is raised if campaigns is empty
    return campaigns

@router.get("/{campaign_id}", response_model=models.Campaign)
async def read_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign

@router.put("/{campaign_id}", response_model=models.Campaign)
async def update_existing_campaign(
    campaign_id: int,
    campaign_update: models.CampaignUpdate, # Changed from CampaignBase to CampaignUpdate
    db: Session = Depends(get_db)
):
    updated_campaign = crud.update_campaign(db=db, campaign_id=campaign_id, campaign_update=campaign_update)
    if updated_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated_campaign

# --- LLM-Related Endpoints ---

@router.post("/{campaign_id}/toc", response_model=models.Campaign, tags=["Campaigns"])
async def generate_campaign_toc_endpoint(
    campaign_id: int,
    request_body: models.LLMGenerationRequest, 
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. TOC cannot be generated.")

    try:
        provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=request_body.model_id_with_prefix)

        generated_tocs_dict = await llm_service.generate_toc( # Returns a dict now
            campaign_concept=db_campaign.concept,
            db=db,
            model=model_specific_id
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

    display_toc_content = generated_tocs_dict.get("display_toc")
    homebrewery_toc_content = generated_tocs_dict.get("homebrewery_toc")

    # The LLM service (e.g. OpenAIService) now raises an error if content is empty or keys are missing.
    # So, we can assume if we reach here, both display_toc_content and homebrewery_toc_content are valid strings.
    # A paranoid check for key existence could be:
    if display_toc_content is None or homebrewery_toc_content is None: # Check if .get returned None (key missing)
        # This should ideally be caught by the LLM service's contract or its own error handling.
        # If LLMGenerationError from the service guarantees content, this might be redundant.
        # However, it's a safeguard against unexpected return structures.
        error_detail = "TOC generation did not return the expected structure (missing display_toc or homebrewery_toc key, or value is null)."
        if "display_toc" not in generated_tocs_dict or "homebrewery_toc" not in generated_tocs_dict:
             error_detail = "TOC generation did not return the expected structure (missing display_toc or homebrewery_toc key)."

        print(f"Error: {error_detail} - Dict received: {generated_tocs_dict}") # Log for debugging
        raise HTTPException(status_code=500, detail=error_detail)

    updated_campaign_with_toc = crud.update_campaign_toc(
        db=db,
        campaign_id=campaign_id,
        display_toc_content=display_toc_content,
        homebrewery_toc_content=homebrewery_toc_content
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
    count: int = Query(5, ge=1, le=10), 
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. Titles cannot be generated.")
    try:
        provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=request_body.model_id_with_prefix)
        generated_titles = await llm_service.generate_titles( # Added await
            campaign_concept=db_campaign.concept,
            db=db,
            count=count, 
            model=model_specific_id
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
    response_model=List[models.CampaignSection], # Returns a list of the created sections
    tags=["Campaigns", "Campaign Sections"]
)
async def seed_sections_from_toc_endpoint(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    print(f"--- Seeding sections for campaign {campaign_id} ---")
    if not db_campaign.display_toc:
        print(f"Campaign {campaign_id} has no display_toc. Cannot seed sections.")
        raise HTTPException(status_code=400, detail="No display_toc found for this campaign. Cannot seed sections.")
    print(f"Raw display_toc for campaign {campaign_id}:\n{db_campaign.display_toc}")

    try:
        # Step 1: Parse db_campaign.display_toc into a list of section titles
        raw_toc_lines = db_campaign.display_toc.splitlines()
        parsed_titles = []
        for line in raw_toc_lines:
            stripped_line = line.strip()
            # Regex to match lines starting with '-', '*', or '+' followed by space and then capture the title
            match = re.match(r"^(?:-|\*|\+)\s+(.+)", stripped_line)
            if match:
                title = match.group(1).strip()
                if title: # Ensure title is not empty after stripping
                    # Further clean title: remove potential markdown links like [Title](...)
                    title = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", title).strip()
                    parsed_titles.append(title)

        print(f"Parsed titles for campaign {campaign_id}: {parsed_titles}")
        if not parsed_titles:
            print(f"No titles were parsed from display_toc for campaign {campaign_id}. No sections will be created.")

        # Step 2: Delete existing sections for this campaign
        print(f"About to delete existing sections for campaign {campaign_id}.")
        deleted_count = crud.delete_sections_for_campaign(db=db, campaign_id=campaign_id)
        print(f"Deleted {deleted_count} existing sections for campaign {campaign_id} before seeding from TOC.")

        # Step 3: Create new sections based on parsed_titles
        created_sections_orm = []
        for order, title in enumerate(parsed_titles):
            print(f"Creating section for campaign {campaign_id}: Title='{title}', Order={order}")
            created_section = crud.create_section_with_placeholder_content(
                db=db,
                campaign_id=campaign_id,
                title=title,
                order=order,
                placeholder_content=f"Content for '{title}' to be generated."
            )
            created_sections_orm.append(created_section)

        print(f"Returning {len(created_sections_orm)} created sections for campaign {campaign_id}: {[s.title for s in created_sections_orm]}")
        print(f"--- Finished seeding sections for campaign {campaign_id} ---")
        return created_sections_orm

    except Exception as e:
        # Log the exception e
        print(f"Error during seeding sections from TOC for campaign {campaign_id}: {e}")
        # Consider if db.rollback() is needed if operations are not atomic within services/CRUD
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while seeding sections: {str(e)}")


# --- Campaign Section Endpoints ---

# Pydantic model for the request body of section order update
class SectionOrderUpdate(BaseModel): # Changed to use pydantic.BaseModel
    section_ids: List[int]

@router.put("/{campaign_id}/sections/order", status_code=204, tags=["Campaign Sections"])
async def update_section_order_endpoint(
    campaign_id: int,
    order_update: SectionOrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates the order of sections within a campaign.
    The list of section_ids should be in the desired new order.
    """
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

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
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not db_campaign.concept and not section_input.prompt:
        raise HTTPException(status_code=400, detail="Campaign concept is missing and no specific prompt for section. Section content cannot be generated.")

    existing_sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    existing_sections_summary = "; ".join([s.title for s in existing_sections if s.title]) if existing_sections else None

    try:
        provider_name, model_specific_id = _extract_provider_and_model(section_input.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=section_input.model_id_with_prefix)
        generated_content = await llm_service.generate_section_content(
            campaign_concept=db_campaign.concept or "A general creative writing piece.",
            db=db,
            existing_sections_summary=existing_sections_summary,
            section_creation_prompt=section_input.prompt,
            section_title_suggestion=section_input.title,
            model=model_specific_id
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
            section_content=generated_content
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
    db: Session = Depends(get_db)
):
    updated_section = crud.update_campaign_section(
        db=db, 
        section_id=section_id, 
        campaign_id=campaign_id, 
        section_update_data=section_data
    )
    if updated_section is None:
        raise HTTPException(status_code=404, detail="Campaign section not found or does not belong to the specified campaign.")
    return updated_section

@router.get("/{campaign_id}/sections", response_model=models.CampaignSectionListResponse, tags=["Campaign Sections"])
async def list_campaign_sections(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    return {"sections": sections}

@router.delete("/{campaign_id}/sections/{section_id}", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def delete_campaign_section_endpoint(
    campaign_id: int,
    section_id: int,
    db: Session = Depends(get_db)
):
    deleted_section = crud.delete_campaign_section(db=db, section_id=section_id, campaign_id=campaign_id)
    if deleted_section is None:
        raise HTTPException(status_code=404, detail="Campaign section not found or does not belong to this campaign.")
    return deleted_section

# --- Export Endpoints ---

@router.get("/{campaign_id}/export/homebrewery", tags=["Campaigns", "Export"])
async def export_campaign_homebrewery(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign notfound")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) 
    export_service = HomebreweryExportService()
    try:
        formatted_text = export_service.format_campaign_for_homebrewery(campaign=db_campaign, sections=sections)
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
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000)
    all_content_parts = []
    if db_campaign.concept:
        concept_title = db_campaign.title if db_campaign.title else "Campaign Concept"
        all_content_parts.append(f"# {concept_title}\n\n{db_campaign.concept}\n\n")
    if db_campaign.toc:
        all_content_parts.append(f"## Table of Contents\n\n{db_campaign.toc}\n\n")
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
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000)
    export_service = HomebreweryExportService()
    try:
        markdown_content = export_service.format_campaign_for_homebrewery(campaign=db_campaign, sections=sections)
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
