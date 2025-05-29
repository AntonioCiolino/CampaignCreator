from typing import Optional
from sqlalchemy.orm import Session

from . import external_models, orm_models # Pydantic models and ORM models

# Placeholder for user CRUD, will be expanded later
# def get_user(db: Session, user_id: int):
#     return db.query(orm_models.User).filter(orm_models.User.id == user_id).first()

# def create_user(db: Session, user: models.UserCreate):
#     hashed_password = user.password + "notreallyhashed" # Replace with actual hashing
#     db_user = orm_models.User(email=user.email, hashed_password=hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# from app.services.openai_service import OpenAILLMService # No longer needed for direct import
from app.services.llm_service import LLMService # For type hinting if needed
from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError # Import the factory
from app import models 

# Campaign CRUD functions
def create_campaign(db: Session, campaign: models.CampaignBase, owner_id: int, model_id_for_concept: Optional[str] = None) -> orm_models.Campaign:
    generated_concept = None
    try:
        # Use the factory to get the appropriate LLM service
        # If model_id_for_concept is None, get_llm_service will use its default (OpenAI if available)
        llm_service: LLMService = get_llm_service(model_id_for_concept)
        generated_concept = llm_service.generate_campaign_concept(user_prompt=campaign.initial_user_prompt)
        # Note: generate_campaign_concept in the service might also take a model_id if we want to override the factory's choice at call time
        # For now, the factory determines the service, and the service method uses its default model or one passed to it.
        # If model_id_for_concept from factory implies a specific model (e.g. "openai/gpt-4"), service should use it.
    except LLMServiceUnavailableError as e:
        print(f"LLM service unavailable for concept generation: {e}")
        # Campaign will be created without a concept.
    except Exception as e:
        print(f"Error generating campaign concept from LLM: {e}")
        # For now, we'll let the campaign be created with a None concept if LLM fails.
        # The endpoint can decide if this is an error or acceptable.
        # Alternatively, re-raise e here to force endpoint to handle.

    db_campaign = orm_models.Campaign(
        title=campaign.title,
        initial_user_prompt=campaign.initial_user_prompt,
        concept=generated_concept, # Use the LLM-generated concept
        owner_id=owner_id
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def get_campaign(db: Session, campaign_id: int) -> Optional[orm_models.Campaign]:
    return db.query(orm_models.Campaign).filter(orm_models.Campaign.id == campaign_id).first()

def update_campaign(db: Session, campaign_id: int, campaign_update: models.CampaignBase) -> Optional[orm_models.Campaign]:
    # Note: campaign_update is CampaignCreate model, which has title and initial_user_prompt
    # The 'concept' field (LLM-generated) is not directly updatable via this function.
    # A separate mechanism (e.g., a 'regenerate_concept' endpoint) would handle concept updates.
    db_campaign = get_campaign(db, campaign_id=campaign_id)
    if db_campaign:
        # Only update fields that are part of CampaignCreate model
        if campaign_update.title is not None: # Ensure title is part of the update model if optional
            db_campaign.title = campaign_update.title
        if campaign_update.initial_user_prompt is not None:
            db_campaign.initial_user_prompt = campaign_update.initial_user_prompt
        
        # If you want to allow clearing concept (or other fields) if not provided:
        # update_data = campaign_update.dict(exclude_unset=True) 
        # for key, value in update_data.items():
        #     if hasattr(db_campaign, key): # Ensure the attribute exists on the ORM model
        #         setattr(db_campaign, key, value)

        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
    return db_campaign

def update_campaign_toc(db: Session, campaign_id: int, toc_content: str) -> Optional[orm_models.Campaign]:
    db_campaign = get_campaign(db, campaign_id=campaign_id)
    if db_campaign:
        db_campaign.toc = toc_content
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
    return db_campaign

# CampaignSection CRUD functions
def get_campaign_sections(db: Session, campaign_id: int, skip: int = 0, limit: int = 1000) -> list[orm_models.CampaignSection]:
    return db.query(orm_models.CampaignSection).filter(orm_models.CampaignSection.campaign_id == campaign_id).order_by(orm_models.CampaignSection.order).offset(skip).limit(limit).all()

def create_campaign_section(db: Session, campaign_id: int, section_title: Optional[str], section_content: str) -> orm_models.CampaignSection:
    existing_sections = get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) # Get all sections to determine order
    max_order = -1
    if existing_sections:
        max_order = max(section.order for section in existing_sections if section.order is not None)
    
    new_order = max_order + 1

    db_section = orm_models.CampaignSection(
        title=section_title,
        content=section_content,
        order=new_order,
        campaign_id=campaign_id
    )
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

def get_section(db: Session, section_id: int, campaign_id: int) -> Optional[orm_models.CampaignSection]:
    return db.query(orm_models.CampaignSection).filter(
        orm_models.CampaignSection.id == section_id,
        orm_models.CampaignSection.campaign_id == campaign_id
    ).first()

def update_campaign_section(db: Session, section_id: int, campaign_id: int, section_update_data: models.CampaignSectionUpdateInput) -> Optional[orm_models.CampaignSection]:
    db_section = get_section(db=db, section_id=section_id, campaign_id=campaign_id)
    if db_section:
        update_data = section_update_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            # If 'order' is updated, and more complex logic is needed later (e.g., reordering others),
            # it would be handled here. For now, direct update.
            setattr(db_section, key, value)
        
        db.add(db_section) # Add to session before commit, though often tracked
        db.commit()
        db.refresh(db_section)
    return db_section

# LLMConfig CRUD functions (example, can be expanded)
# def create_llm_config(db: Session, config: models.LLMConfigCreate, owner_id: int) -> orm_models.LLMConfig:
#     db_config = orm_models.LLMConfig(**config.dict(), owner_id=owner_id)
#     db.add(db_config)
#     db.commit()
#     db.refresh(db_config)
#     return db_config

# def get_llm_configs_by_user(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[orm_models.LLMConfig]:
#     return db.query(orm_models.LLMConfig).filter(orm_models.LLMConfig.owner_id == owner_id).offset(skip).limit(limit).all()

# CampaignSection CRUD (example, can be expanded)
# def create_campaign_section(db: Session, section: models.CampaignSectionCreate, campaign_id: int) -> orm_models.CampaignSection:
#     db_section = orm_models.CampaignSection(**section.dict(), campaign_id=campaign_id)
#     db.add(db_section)
#     db.commit()
#     db.refresh(db_section)
#     return db_section

# def get_campaign_sections(db: Session, campaign_id: int, skip: int = 0, limit: int = 1000) -> list[orm_models.CampaignSection]:
#     return db.query(orm_models.CampaignSection).filter(orm_models.CampaignSection.campaign_id == campaign_id).order_by(orm_models.CampaignSection.order).offset(skip).limit(limit).all()

def get_all_campaigns(db: Session):
    return db.query(orm_models.Campaign).all()
