from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

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
        generated_toc = await llm_service.generate_toc( # Added await
            campaign_concept=db_campaign.concept, 
            model=model_specific_id
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error for TOC generation: {str(e)}")
    except LLMGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
        generated_titles = await llm_service.generate_titles( # Added await
            campaign_concept=db_campaign.concept, 
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
    return external_models.CampaignTitlesResponse(titles=generated_titles)

# --- Campaign Section Endpoints ---

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

class Config:
    from_attributes = True
