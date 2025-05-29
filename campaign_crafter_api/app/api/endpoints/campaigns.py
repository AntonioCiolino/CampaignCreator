from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, crud, orm_models 
from app.db import get_db 
from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError
from app.services.export_service import HomebreweryExportService
from fastapi.responses import PlainTextResponse

router = APIRouter()

def _extract_provider_and_model(model_id_with_prefix: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Helper to extract provider and model_specific_id."""
    if model_id_with_prefix and "/" in model_id_with_prefix:
        try:
            provider, model_id = model_id_with_prefix.split("/", 1)
            return provider.lower(), model_id
        except ValueError:
            # This case should ideally be caught by Pydantic validation if format is strict
            raise HTTPException(status_code=400, detail=f"Invalid model_id_with_prefix format: '{model_id_with_prefix}'. Expected 'provider/model_name'.")
    elif model_id_with_prefix: 
        # If no prefix, it's ambiguous. Could be a model ID for a default provider,
        # or a provider name itself if no model is specified for that provider.
        # The factory's get_llm_service will try to infer.
        # We return None for provider, and the model_id_with_prefix as the model_specific_id.
        # The factory will then try this model_id with its default provider.
        # Or, if this string IS a provider name, factory will use it and service will use its default model.
        return None, model_id_with_prefix 
    return None, None # No model_id_with_prefix provided

@router.post("/", response_model=models.Campaign)
async def create_new_campaign(
    campaign: models.CampaignCreate, 
    db: Session = Depends(get_db)
):
    owner_id = 1 # Placeholder
    try:
        # crud.create_campaign now needs to handle the model_id_with_prefix logic for concept generation
        db_campaign = crud.create_campaign(
            db=db, 
            campaign=campaign, 
            owner_id=owner_id, 
            model_id_with_prefix_for_concept=campaign.model_id_with_prefix_for_concept # Pass from request
        )
        
        if db_campaign.concept is None and campaign.user_prompt: # If user prompted but concept is still none
             print(f"Campaign {db_campaign.id} created, but concept generation might have failed or was skipped (e.g. LLM unavailable/error).")
             # Consider if an error/warning should be returned to client.
             # For now, just logging and returning the campaign as created.
    except LLMServiceUnavailableError as e:
        # This implies the factory failed to get a service, likely due to config issues for the selected/default provider
        raise HTTPException(status_code=503, detail=f"LLM Service Error for concept generation: {e}")
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during campaign creation: {e}")
        # This could be an error from the LLM service itself (e.g. API error) or other unexpected issue
        raise HTTPException(status_code=500, detail=f"Failed to create campaign due to an external service or unexpected error: {str(e)}")
    return db_campaign


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
        
        generated_toc = llm_service.generate_toc(
            campaign_concept=db_campaign.concept, 
            model=model_specific_id # Pass only the specific model ID or None
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for TOC generation: {e}")
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="TOC generation is not implemented for the selected LLM provider.")
    except Exception as e:
        print(f"Error during TOC generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Table of Contents: {str(e)}")

    if not generated_toc:
        raise HTTPException(status_code=500, detail="TOC generation resulted in empty content.")

    updated_campaign_with_toc = crud.update_campaign_toc(db=db, campaign_id=campaign_id, toc_content=generated_toc)
    if updated_campaign_with_toc is None:
        raise HTTPException(status_code=404, detail="Campaign not found when attempting to update TOC.")
        
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
        
        generated_titles = llm_service.generate_titles(
            campaign_concept=db_campaign.concept, 
            count=count, 
            model=model_specific_id # Pass only the specific model ID or None
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for title generation: {e}")
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

@router.post("/{campaign_id}/sections", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def create_new_campaign_section_endpoint(
    campaign_id: int,
    section_input: models.CampaignSectionCreateInput, # This model should contain model_id_with_prefix
    db: Session = Depends(get_db)
):
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not db_campaign.concept and not section_input.prompt: # Allow section if prompt is given, even without main concept
        raise HTTPException(status_code=400, detail="Campaign concept is missing and no specific prompt for section. Section content cannot be generated.")

    existing_sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    existing_sections_summary = "; ".join([s.title for s in existing_sections if s.title]) if existing_sections else None

    try:
        provider_name, model_specific_id = _extract_provider_and_model(section_input.model_id_with_prefix)
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=section_input.model_id_with_prefix)
        
        generated_content = llm_service.generate_section_content(
            campaign_concept=db_campaign.concept or "A general creative writing piece.", # Provide fallback if main concept missing but prompt exists
            existing_sections_summary=existing_sections_summary,
            section_creation_prompt=section_input.prompt,
            section_title_suggestion=section_input.title,
            model=model_specific_id # Pass only the specific model ID or None
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for section content generation: {e}")
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

# Other endpoints (PUT section, GET sections, export, full_content, GET campaign, PUT campaign)
# generally do not directly interact with LLM services for generation, so they remain largely unchanged
# by this specific refactoring, unless their Pydantic models or underlying CRUD operations change.

@router.put("/{campaign_id}/sections/{section_id}", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def update_campaign_section_endpoint(
    campaign_id: int,
    section_id: int,
    section_data: models.CampaignSectionUpdateInput, # Assuming this doesn't involve LLM regen
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
    return models.CampaignSectionListResponse(sections=sections)

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
    response = models.CampaignFullContentResponse(
        campaign_id=db_campaign.id,
        title=db_campaign.title,
        full_content=full_content_str
    )
    return response

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
    campaign_update: models.CampaignCreate, 
    db: Session = Depends(get_db)
):
    # This endpoint might need to be enhanced if changing the title/prompt should re-trigger concept generation
    # For now, it's a simple update of fields.
    # If concept regeneration is desired, it would need model_id_with_prefix and logic similar to create_new_campaign
    updated_campaign = crud.update_campaign(db=db, campaign_id=campaign_id, campaign_update=campaign_update)
    if updated_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated_campaign

# Import the new Pydantic model for the response
from app.models.export_models import PrepareHomebreweryPostResponse

@router.get("/{campaign_id}/prepare_for_homebrewery", response_model=PrepareHomebreweryPostResponse, tags=["Campaigns", "Export"])
async def prepare_campaign_for_homebrewery_posting(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """
    Prepares the campaign content for manual posting to Homebrewery.
    It returns the full Markdown content and a link to Homebrewery's "new brew" page.
    """
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) # Assuming limit is high enough
    
    export_service = HomebreweryExportService()
    try:
        markdown_content = export_service.format_campaign_for_homebrewery(campaign=db_campaign, sections=sections)
    except Exception as e:
        print(f"Error during Homebrewery content generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Homebrewery Markdown: {str(e)}")

    homebrewery_new_url = "https://homebrewery.naturalcrit.com/new"
    
    filename_title_part = db_campaign.title.replace(' ', '_') if db_campaign.title else 'campaign_export'
    filename_suggestion = f"{filename_title_part}_{db_campaign.id}_homebrewery.md" # Consistent with existing export

    return PrepareHomebreweryPostResponse(
        markdown_content=markdown_content,
        homebrewery_new_url=homebrewery_new_url,
        filename_suggestion=filename_suggestion
    )
