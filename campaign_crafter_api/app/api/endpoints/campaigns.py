from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, crud, orm_models # Pydantic models, CRUD functions, ORM models
from app.db import get_db # Dependency for DB session

router = APIRouter()

@router.post("/", response_model=models.Campaign)
async def create_new_campaign(
    campaign: models.CampaignCreate, 
    db: Session = Depends(get_db)
):
    # For now, assumes a placeholder owner_id = 1
    # This will be replaced with actual user authentication later.
    owner_id = 1 
    try:
        # For initial concept generation, model_id is not directly part of CampaignCreate.
        # We can pass None to crud.create_campaign, and it will use the factory's default.
        # Or, extend CampaignCreate to include an optional model_id for concept generation.
        # For now, using None, which means factory default (OpenAI if key exists).
        db_campaign = crud.create_campaign(db=db, campaign=campaign, owner_id=owner_id, model_id_for_concept=None)
        
        # Check if LLM failed (concept is None) AND if the reason was service unavailability
        # This check is a bit indirect. A more robust way would be for crud.create_campaign
        # to return a status or specific error if LLM failed due to unavailability.
        if db_campaign.concept is None: 
            # This could be due to LLM error OR service unavailability handled in CRUD.
            # If it was LLMServiceUnavailableError, crud.create_campaign would have printed a message.
            print("Campaign created. Concept might be missing if LLM service was unavailable or an error occurred during generation.")
            # Depending on product requirements, one might raise an error here instead.
            # For example: raise HTTPException(status_code=503, detail="Campaign created, but LLM concept generation failed.")
    except ValueError as ve: # Catch specific errors like API key not configured
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Catch-all for other exceptions, including OpenAI API errors if not handled more specifically in service/crud
        print(f"Error during campaign creation: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to create campaign due to an external service error: {str(e)}")
    return db_campaign

from fastapi import Query # Import Query

@router.post("/{campaign_id}/toc", response_model=models.Campaign, tags=["Campaigns"])
async def generate_campaign_toc_endpoint(
    campaign_id: int,
    request_body: models.LLMGenerationRequest, # Use the new request body model
    db: Session = Depends(get_db)
):
    # 1. Fetch the campaign
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Check if campaign concept exists
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. TOC cannot be generated.")

    # 3. Instantiate LLM Service and generate TOC
    try:
        # from app.services.openai_service import OpenAILLMService # No longer direct import
        from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError # Import factory

        llm_service = get_llm_service(request_body.model) # request_body.model can be "provider/model_name" or None
        
        generated_toc = llm_service.generate_toc(
            campaign_concept=db_campaign.concept, 
            model=request_body.model # Pass the full model_id, service will parse/use its default
        )
        
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as ve: 
        # This might catch errors from model_id parsing in service if not handled by factory, or other ValueErrors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during TOC generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Table of Contents: {str(e)}")

    if not generated_toc:
        raise HTTPException(status_code=500, detail="TOC generation resulted in empty content.")

    # 4. Update campaign with the new TOC
    updated_campaign_with_toc = crud.update_campaign_toc(db=db, campaign_id=campaign_id, toc_content=generated_toc)
    if updated_campaign_with_toc is None:
        # This should ideally not happen if the campaign was found initially
        raise HTTPException(status_code=404, detail="Campaign not found when attempting to update TOC.")
        
    return updated_campaign_with_toc

@router.post("/{campaign_id}/titles", response_model=models.CampaignTitlesResponse, tags=["Campaigns"])
async def generate_campaign_titles_endpoint(
    campaign_id: int,
    request_body: models.LLMGenerationRequest, # Use the new request body model
    count: Optional[int] = Query(5, ge=1, le=10), # Count remains a query parameter
    db: Session = Depends(get_db)
):
    # 1. Fetch the campaign
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Check if campaign concept exists
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. Titles cannot be generated.")
    
    if count is None or count <=0 : # Ensure count is positive, default to 5 if not provided or invalid
        count = 5


    # 3. Instantiate LLM Service and generate titles
    try:
        # from app.services.openai_service import OpenAILLMService # No longer direct import
        from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError # Import factory

        llm_service = get_llm_service(request_body.model)
        
        generated_titles = llm_service.generate_titles(
            campaign_concept=db_campaign.concept, 
            count=count, 
            model=request_body.model # Pass the full model_id
        )
        
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during title generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate titles: {str(e)}")

    if not generated_titles:
        # This might happen if LLM returns empty or fails to parse, though service should raise exception
        raise HTTPException(status_code=500, detail="Title generation resulted in empty content.")
        
    return models.CampaignTitlesResponse(titles=generated_titles)

@router.post("/{campaign_id}/sections", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def create_new_campaign_section_endpoint(
    campaign_id: int,
    section_input: models.CampaignSectionCreateInput,
    db: Session = Depends(get_db)
):
    # 1. Fetch the campaign
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Check if campaign concept exists
    if not db_campaign.concept:
        raise HTTPException(status_code=400, detail="Campaign concept is missing. Section content cannot be generated without it.")

    # 3. Fetch existing sections for the campaign
    existing_sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    
    # 4. Prepare existing_sections_summary
    existing_sections_summary = "; ".join([s.title for s in existing_sections if s.title]) if existing_sections else None

    # 5. Instantiate LLM Service using factory
    try:
        # from app.services.openai_service import OpenAILLMService # No longer direct import
        from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError # Import factory
        llm_service = get_llm_service(section_input.model) # section_input.model can be "provider/model_name" or None
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as ve: 
        raise HTTPException(status_code=503, detail=f"LLM Service initialization failed: {str(ve)}")


    # 6. Call llm_service.generate_section_content()
    generated_content: Optional[str] = None
    try:
        generated_content = llm_service.generate_section_content(
            campaign_concept=db_campaign.concept,
            existing_sections_summary=existing_sections_summary,
            section_creation_prompt=section_input.prompt,
            section_title_suggestion=section_input.title,
            model=section_input.model # Pass the full model_id, service will parse/use its default
        )
    except LLMServiceUnavailableError as e: # Should be caught by factory, but as a safeguard
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e: 
        print(f"Error during section content generation for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate section content: {str(e)}")

    if not generated_content:
        raise HTTPException(status_code=500, detail="LLM generated empty content for the section.")

    # 7. Call crud.create_campaign_section()
    # The user's suggested title (section_input.title) is used.
    # LLM could potentially refine or generate a title if the service was designed to return it separately.
    new_section_title = section_input.title if section_input.title else "Untitled Section" # Default if user provides no title

    try:
        db_section = crud.create_campaign_section(
            db=db,
            campaign_id=campaign_id,
            section_title=new_section_title, 
            section_content=generated_content
        )
    except Exception as e: # Catch potential DB errors during section creation
        print(f"Error saving new section for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save the new campaign section.")
        
    # 8. Return the newly created campaign section
    return db_section

@router.put("/{campaign_id}/sections/{section_id}", response_model=models.CampaignSection, tags=["Campaign Sections"])
async def update_campaign_section_endpoint(
    campaign_id: int,
    section_id: int,
    section_data: models.CampaignSectionUpdateInput,
    db: Session = Depends(get_db)
):
    # In a real app, you would also check if the user is the owner of the campaign
    # and has permission to update this section.

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
    # Check if campaign exists (optional, but good practice)
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id)
    # The crud.get_campaign_sections already returns a list of orm_models.CampaignSection
    # Pydantic will handle the conversion for the response_model.
    return models.CampaignSectionListResponse(sections=sections)

from fastapi.responses import PlainTextResponse # Import PlainTextResponse
from app.services.export_service import HomebreweryExportService # Import the new service

@router.get("/{campaign_id}/export/homebrewery", tags=["Campaigns", "Export"])
async def export_campaign_homebrewery(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    # 1. Fetch the campaign
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Fetch all sections for the campaign
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) # Assumes limit is high enough

    # 3. Instantiate HomebreweryExportService
    export_service = HomebreweryExportService()

    # 4. Call format_campaign_for_homebrewery
    try:
        formatted_text = export_service.format_campaign_for_homebrewery(campaign=db_campaign, sections=sections)
    except Exception as e:
        # Catch any unexpected errors during formatting
        print(f"Error during Homebrewery export formatting for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to format campaign for Homebrewery export: {str(e)}")

    # 5. Return PlainTextResponse
    filename_title_part = db_campaign.title.replace(' ', '_') if db_campaign.title else 'campaign_export'
    filename = f"{filename_title_part}_{db_campaign.id}_homebrewery.md"
    
    return PlainTextResponse(
        content=formatted_text, 
        media_type="text/markdown", # Changed from text/plain to text/markdown
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""} # Added quotes around filename
    )

@router.get("/{campaign_id}/full_content", response_model=models.CampaignFullContentResponse, tags=["Campaigns"])
async def get_campaign_full_content_endpoint(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    # 1. Fetch the campaign
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Fetch all sections for the campaign (ordered by 'order' from CRUD)
    sections = crud.get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) # Assuming limit is high enough

    # 3. Concatenate content
    all_content_parts = []

    # Optionally include the main campaign concept at the start
    if db_campaign.concept:
        concept_title = db_campaign.title if db_campaign.title else "Campaign Concept"
        all_content_parts.append(f"# {concept_title}\n\n{db_campaign.concept}\n\n")
    
    # Optionally, include the Table of Contents if it exists
    if db_campaign.toc:
        all_content_parts.append(f"## Table of Contents\n\n{db_campaign.toc}\n\n")

    # Add content from sections
    for section in sections:
        if section.title:
            all_content_parts.append(f"## {section.title}\n\n{section.content}\n\n")
        else:
            all_content_parts.append(f"{section.content}\n\n") # Section without title, add extra newline for separation

    full_content_str = "".join(all_content_parts).strip() # Remove trailing newlines

    # 4. Construct the response
    response = models.CampaignFullContentResponse(
        campaign_id=db_campaign.id,
        title=db_campaign.title,
        full_content=full_content_str
    )
    
    # 5. Return the response
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
    campaign_update: models.CampaignCreate, # Reusing CampaignCreate for simplicity
    db: Session = Depends(get_db)
):
    # In a real app, you would also check if the user is the owner of the campaign
    updated_campaign = crud.update_campaign(db=db, campaign_id=campaign_id, campaign_update=campaign_update)
    if updated_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated_campaign
