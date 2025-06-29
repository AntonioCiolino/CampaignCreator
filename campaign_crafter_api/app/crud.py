from typing import Optional, List, Dict # Added List and Dict
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app import models, orm_models # Standardized
from app.core.security import encrypt_key # Added for API key encryption
from app.services.image_generation_service import ImageGenerationService
# import asyncio # No longer needed here
from urllib.parse import urlparse

# --- Password Hashing Utilities ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- User CRUD Functions ---
def create_user(db: Session, user: models.UserCreate) -> orm_models.User: # pwd_context is global
    hashed_password = get_password_hash(user.password)
    db_user = orm_models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_superuser=user.is_superuser
        # 'disabled' defaults to False in the ORM, which is correct for a new user.
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[orm_models.User]:
    return db.query(orm_models.User).filter(orm_models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[orm_models.User]:
    return db.query(orm_models.User).filter(orm_models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[orm_models.User]:
    return db.query(orm_models.User).filter(orm_models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[orm_models.User]:
    return db.query(orm_models.User).offset(skip).limit(limit).all()

def update_user(db: Session, db_user: orm_models.User, user_in: models.UserUpdate) -> orm_models.User: # pwd_context is global
    update_data = user_in.model_dump(exclude_unset=True) # Use model_dump for Pydantic v2

    if "password" in update_data and update_data["password"] is not None:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password

    # Explicitly handle other fields from UserUpdate model
    if user_in.username is not None: # Though username is usually not updatable or handled carefully
        db_user.username = user_in.username
    if user_in.email is not None:
        db_user.email = user_in.email
    if user_in.full_name is not None:
        db_user.full_name = user_in.full_name
    if user_in.is_superuser is not None:
        db_user.is_superuser = user_in.is_superuser
    if user_in.disabled is not None:
        db_user.disabled = user_in.disabled

    # Handle sd_engine_preference
    # Check if 'sd_engine_preference' was explicitly passed in the request data
    if "sd_engine_preference" in update_data: # Checks if key was in payload
        db_user.sd_engine_preference = user_in.sd_engine_preference # Applies the value (could be None to clear)

    # Handle avatar_url
    if "avatar_url" in update_data: # Checks if key was in payload
        db_user.avatar_url = user_in.avatar_url # Applies the value (could be None to clear)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[orm_models.User]:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None

    db.delete(db_user)
    db.commit()
    return db_user

def update_user_api_keys(db: Session, db_user: orm_models.User, api_keys_in: models.UserAPIKeyUpdate) -> orm_models.User:
    if api_keys_in.openai_api_key is not None:
        if api_keys_in.openai_api_key == "":
            db_user.encrypted_openai_api_key = None
        else:
            db_user.encrypted_openai_api_key = encrypt_key(api_keys_in.openai_api_key)

    if api_keys_in.sd_api_key is not None:
        if api_keys_in.sd_api_key == "":
            db_user.encrypted_sd_api_key = None
        else:
            db_user.encrypted_sd_api_key = encrypt_key(api_keys_in.sd_api_key)

    if api_keys_in.gemini_api_key is not None:
        if api_keys_in.gemini_api_key == "":
            db_user.encrypted_gemini_api_key = None
        else:
            db_user.encrypted_gemini_api_key = encrypt_key(api_keys_in.gemini_api_key)

    if api_keys_in.other_llm_api_key is not None:
        if api_keys_in.other_llm_api_key == "":
            db_user.encrypted_other_llm_api_key = None
        else:
            db_user.encrypted_other_llm_api_key = encrypt_key(api_keys_in.other_llm_api_key)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Feature CRUD Functions ---
def get_feature(db: Session, feature_id: int) -> Optional[orm_models.Feature]:
    return db.query(orm_models.Feature).filter(orm_models.Feature.id == feature_id).first()

def get_feature_by_name(db: Session, name: str, user_id: Optional[int] = None) -> Optional[orm_models.Feature]:
    if user_id is not None:
        db_feature = db.query(orm_models.Feature).filter(
            orm_models.Feature.name == name,
            orm_models.Feature.user_id == user_id
        ).first()
        if db_feature:
            return db_feature
    # If not found for the user or no user_id provided, try to find a system feature
    return db.query(orm_models.Feature).filter(
        orm_models.Feature.name == name,
        orm_models.Feature.user_id == None
    ).first()

def get_features(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[orm_models.Feature]:
    query = db.query(orm_models.Feature)
    if user_id is not None:
        query = query.filter(
            (orm_models.Feature.user_id == user_id) | (orm_models.Feature.user_id == None)
        )
    else: # Only system features if no specific user_id
        query = query.filter(orm_models.Feature.user_id == None)
    return query.offset(skip).limit(limit).all()

def create_feature(db: Session, feature: models.FeatureCreate, user_id: Optional[int] = None) -> orm_models.Feature:
    feature_data = feature.model_dump()
    feature_data.pop('user_id', None) # Ensure user_id from payload is removed, function arg takes precedence
    # The user_id explicitly passed to this function (from current_user or None for system features) takes precedence.
    db_feature = orm_models.Feature(**feature_data, user_id=user_id)
    db.add(db_feature)
    db.commit()
    db.refresh(db_feature)
    return db_feature

def update_feature(db: Session, feature_id: int, feature_update: models.FeatureUpdate) -> Optional[orm_models.Feature]:
    db_feature = get_feature(db, feature_id=feature_id)
    if not db_feature:
        return None

    update_data = feature_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_feature, key, value)

    db.add(db_feature)
    db.commit()
    db.refresh(db_feature)
    return db_feature

def delete_feature(db: Session, feature_id: int) -> Optional[orm_models.Feature]:
    db_feature = get_feature(db, feature_id=feature_id)
    if not db_feature:
        return None

    db.delete(db_feature)
    db.commit()
    return db_feature

# --- RollTable and RollTableItem CRUD Functions ---
def get_roll_table(db: Session, roll_table_id: int) -> Optional[orm_models.RollTable]:
    return db.query(orm_models.RollTable).filter(orm_models.RollTable.id == roll_table_id).first()

def get_roll_table_by_name(db: Session, name: str, user_id: Optional[int] = None) -> Optional[orm_models.RollTable]:
    # Try to find a table owned by the user first
    if user_id is not None:
        db_roll_table = db.query(orm_models.RollTable).filter(
            orm_models.RollTable.name == name,
            orm_models.RollTable.user_id == user_id
        ).first()
        if db_roll_table:
            return db_roll_table

    # If not found or no user_id provided, try to find a system table (user_id is None)
    return db.query(orm_models.RollTable).filter(
        orm_models.RollTable.name == name,
        orm_models.RollTable.user_id == None
    ).first()

def get_roll_tables(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[orm_models.RollTable]:
    query = db.query(orm_models.RollTable)
    if user_id is not None:
        query = query.filter(
            (orm_models.RollTable.user_id == user_id) | (orm_models.RollTable.user_id == None)
        )
    else:
        query = query.filter(orm_models.RollTable.user_id == None)
    return query.offset(skip).limit(limit).all()

def create_roll_table(db: Session, roll_table: models.RollTableCreate, user_id: Optional[int] = None) -> orm_models.RollTable:
    db_roll_table = orm_models.RollTable(
        name=roll_table.name,
        description=roll_table.description,
        user_id=user_id
    )
    # Add them to the table's collection. SQLAlchemy will handle associating them.
    db_roll_table.items = [orm_models.RollTableItem(**item.model_dump()) for item in roll_table.items]

    db.add(db_roll_table)
    db.commit()
    db.refresh(db_roll_table)
    return db_roll_table

def update_roll_table(db: Session, roll_table_id: int, roll_table_update: models.RollTableUpdate) -> Optional[orm_models.RollTable]:
    db_roll_table = get_roll_table(db, roll_table_id=roll_table_id)
    if not db_roll_table:
        return None

    if roll_table_update.name is not None:
        db_roll_table.name = roll_table_update.name
    if roll_table_update.description is not None:
        db_roll_table.description = roll_table_update.description

    if roll_table_update.items is not None:
        # Delete existing items
        db.query(orm_models.RollTableItem).filter(orm_models.RollTableItem.roll_table_id == roll_table_id).delete()
        
        # Create new items
        new_items = []
        for item_data in roll_table_update.items:
            new_item = orm_models.RollTableItem(**item_data.model_dump(), roll_table_id=roll_table_id)
            new_items.append(new_item)
        db_roll_table.items = new_items # Assign new list of items

    db.add(db_roll_table) # db.add() is used to stage changes, good practice.
    db.commit()
    db.refresh(db_roll_table)
    return db_roll_table

def delete_roll_table(db: Session, roll_table_id: int) -> Optional[orm_models.RollTable]:
    db_roll_table = get_roll_table(db, roll_table_id=roll_table_id)
    if not db_roll_table:
        return None

    db.delete(db_roll_table)
    db.commit()
    # The object is expired after commit, so we can return it as is if needed,
    # or None if we want to indicate it's no longer in DB.
    # For consistency with other delete functions, returning the object.
    return db_roll_table

def copy_system_roll_table_to_user(db: Session, system_table: orm_models.RollTable, user_id: int) -> orm_models.RollTable:
    """
    Copies a system roll table (where user_id is None) to a specific user.
    The new table will have the same name, description, and items as the system table,
    but will be associated with the given user_id.
    """
    # Create a new RollTable object for the user
    user_roll_table = orm_models.RollTable(
        name=system_table.name,
        description=system_table.description,
        user_id=user_id
    )

    # Copy items from the system table to the new user table
    user_roll_table.items = [
        orm_models.RollTableItem(
            min_roll=item.min_roll,
            max_roll=item.max_roll,
            description=item.description
            # roll_table_id will be set automatically when the user_roll_table is added to session and committed,
            # or by relationship back-population if items are directly appended to user_roll_table.items collection
            # and the relationship is configured correctly.
            # Explicitly setting roll_table=user_roll_table in constructor is safer if cascade isn't perfect.
            # However, since we build the list and assign to .items, SQLAlchemy should handle it.
        ) for item in system_table.items
    ]

    db.add(user_roll_table)
    db.commit()
    db.refresh(user_roll_table)
    return user_roll_table


# from app.services.openai_service import OpenAILLMService
from app.services.llm_service import LLMService # Standardized
from app.services.llm_factory import get_llm_service, LLMServiceUnavailableError # Standardized
# from app import models # This is already imported via "from app import models, orm_models"

# --- Campaign CRUD functions ---
async def create_campaign(db: Session, campaign_payload: models.CampaignCreate, current_user_obj: models.User) -> orm_models.Campaign: # Changed owner_id to current_user_obj
    generated_concept = None

    # Conditionally generate concept
    if not campaign_payload.skip_concept_generation and campaign_payload.initial_user_prompt:
        current_user_orm_for_keys = get_user(db, user_id=current_user_obj.id)
        try:
            provider_name_for_concept = None
            model_specific_id_for_concept_crud = None
            if campaign_payload.model_id_with_prefix_for_concept:
                if "/" in campaign_payload.model_id_with_prefix_for_concept:
                    provider_name_for_concept, model_specific_id_for_concept_crud = campaign_payload.model_id_with_prefix_for_concept.split("/",1)
                else: # No prefix, assume it's the model ID itself
                    model_specific_id_for_concept_crud = campaign_payload.model_id_with_prefix_for_concept

            llm_service = get_llm_service(
                db=db,
                current_user_orm=current_user_orm_for_keys,
                provider_name=provider_name_for_concept,
                model_id_with_prefix=campaign_payload.model_id_with_prefix_for_concept,
                campaign=None  # Campaign doesn't exist yet
            )
            generated_concept = await llm_service.generate_campaign_concept( # Assuming this method is generate_campaign_concept
                user_prompt=campaign_payload.initial_user_prompt, # Use initial_user_prompt from payload
                db=db,
                current_user=current_user_obj,
                model=model_specific_id_for_concept_crud,
                # temperature can be passed if llm_service.generate_campaign_concept supports it
                # temperature=campaign_payload.temperature
            )
        except LLMServiceUnavailableError as e:
            print(f"LLM service unavailable for concept generation: {e}")
        except Exception as e:
            print(f"Error generating campaign concept from LLM: {e}")
    elif campaign_payload.skip_concept_generation:
        print(f"Campaign creation: Skipping concept generation for campaign titled '{campaign_payload.title}'.")
    else: # No prompt provided, and not explicitly skipping
        print(f"Campaign creation: No initial prompt provided for campaign titled '{campaign_payload.title}'. Concept will be null.")


    db_campaign = orm_models.Campaign(
        title=campaign_payload.title,
        initial_user_prompt=campaign_payload.initial_user_prompt,
        concept=generated_concept, # Use the (awaited) LLM-generated concept
        owner_id=current_user_obj.id, # Use id from the passed user object
        badge_image_url=campaign_payload.badge_image_url,
        thematic_image_url=campaign_payload.thematic_image_url,
        thematic_image_prompt=campaign_payload.thematic_image_prompt,
        selected_llm_id=campaign_payload.selected_llm_id,
        temperature=campaign_payload.temperature,

        # Add new theme properties
        theme_primary_color=campaign_payload.theme_primary_color,
        theme_secondary_color=campaign_payload.theme_secondary_color,
        theme_background_color=campaign_payload.theme_background_color,
        theme_text_color=campaign_payload.theme_text_color,
        theme_font_family=campaign_payload.theme_font_family,
        theme_background_image_url=campaign_payload.theme_background_image_url,
        theme_background_image_opacity=campaign_payload.theme_background_image_opacity,

        # New field for Mood Board
        mood_board_image_urls=campaign_payload.mood_board_image_urls
        # toc and homebrewery_export are not set here by default
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def get_campaign(db: Session, campaign_id: int) -> Optional[orm_models.Campaign]:
    db_campaign = db.query(orm_models.Campaign).filter(orm_models.Campaign.id == campaign_id).first()
    if db_campaign:
        # Convert string TOCs to list-of-dicts for backward compatibility
        if isinstance(db_campaign.display_toc, str):
            db_campaign.display_toc = [{"title": db_campaign.display_toc, "type": "unknown"}] if db_campaign.display_toc else []
        if isinstance(db_campaign.homebrewery_toc, str):
            db_campaign.homebrewery_toc = [{"title": db_campaign.homebrewery_toc, "type": "unknown"}] if db_campaign.homebrewery_toc else []
    return db_campaign

async def update_campaign(db: Session, campaign_id: int, campaign_update: models.CampaignUpdate) -> Optional[orm_models.Campaign]:
    db_campaign = get_campaign(db, campaign_id=campaign_id) # get_campaign will now handle potential TOC conversion if data was old
    if db_campaign:
        old_image_urls = []
        if hasattr(db_campaign, 'mood_board_image_urls') and db_campaign.mood_board_image_urls is not None:
            old_image_urls = list(db_campaign.mood_board_image_urls)

        update_data = campaign_update.model_dump(exclude_unset=True)
        
        mood_board_updated = 'mood_board_image_urls' in update_data

        for key, value in update_data.items():
            if hasattr(db_campaign, key):
                setattr(db_campaign, key, value)
            # else:
                # Optionally log or handle fields in payload that are not in ORM model
                # print(f"Warning: Field '{key}' not in Campaign ORM model.")

        if mood_board_updated:
            new_image_urls = set(db_campaign.mood_board_image_urls if db_campaign.mood_board_image_urls else [])
            deleted_urls = [url for url in old_image_urls if url not in new_image_urls]

            if deleted_urls:
                image_service = ImageGenerationService()
                for url_to_delete in deleted_urls:
                    try:
                        parsed_url = urlparse(url_to_delete)
                        # Assuming blob name is the last part of the path
                        # e.g., https://<account>.blob.core.windows.net/<container>/<blob_name>
                        blob_name = parsed_url.path.split('/')[-1]
                        if blob_name:
                            print(f"Attempting to delete blob: {blob_name} from URL: {url_to_delete}")
                            await image_service.delete_image_from_blob_storage(blob_name)
                        else:
                            print(f"Warning: Could not extract blob name from URL: {url_to_delete}")
                    except Exception as e:
                        # Catch errors during parsing or deletion call setup
                        print(f"Error processing URL for deletion {url_to_delete}: {e}")
                        # Depending on policy, you might want to collect these errors rather than just print

        db.add(db_campaign) # Add to session, SQLAlchemy tracks changes
        db.commit()
        db.refresh(db_campaign)
    return db_campaign

def update_campaign_toc(db: Session, campaign_id: int, display_toc_content: List[Dict[str, str]], homebrewery_toc_content: Optional[Dict[str, str]]) -> Optional[orm_models.Campaign]:
    db_campaign = get_campaign(db, campaign_id=campaign_id) # get_campaign will handle potential string TOC conversion before update
    if db_campaign:
        db_campaign.display_toc = display_toc_content # Always update this
        if homebrewery_toc_content is not None: # Only update if provided
            db_campaign.homebrewery_toc = homebrewery_toc_content
        # db.add(db_campaign) # Not strictly necessary as SQLAlchemy tracks changes on attached objects
        db.commit()
        db.refresh(db_campaign)
    return db_campaign

# CampaignSection CRUD functions

def delete_sections_for_campaign(db: Session, campaign_id: int) -> int:
    """Deletes all sections associated with a given campaign_id. Returns the number of sections deleted."""
    num_deleted = db.query(orm_models.CampaignSection).filter(orm_models.CampaignSection.campaign_id == campaign_id).delete(synchronize_session=False)
    db.commit() # Commit after deletion
    return num_deleted

def create_section_with_placeholder_content(db: Session, campaign_id: int, title: str, order: int, placeholder_content: str = "Content to be generated.", type: Optional[str] = "generic") -> orm_models.CampaignSection:
    """Creates a new campaign section with a title, order, placeholder content, and type."""
    db_section = orm_models.CampaignSection(
        title=title,
        content=placeholder_content,
        order=order,
        type=type, # Added type
        campaign_id=campaign_id
    )
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

def get_campaign_sections(db: Session, campaign_id: int, skip: int = 0, limit: int = 1000) -> list[orm_models.CampaignSection]:
    return db.query(orm_models.CampaignSection).filter(orm_models.CampaignSection.campaign_id == campaign_id).order_by(orm_models.CampaignSection.order).offset(skip).limit(limit).all()

def create_campaign_section(db: Session, campaign_id: int, section_title: Optional[str], section_content: str, section_type: Optional[str] = "generic") -> orm_models.CampaignSection:
    existing_sections = get_campaign_sections(db=db, campaign_id=campaign_id, limit=1000) # Get all sections to determine order
    max_order = -1
    if existing_sections:
        max_order = max(section.order for section in existing_sections if section.order is not None)
    
    new_order = max_order + 1

    db_section = orm_models.CampaignSection(
        title=section_title,
        content=section_content,
        order=new_order,
        type=section_type, # Added type
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
        update_data = section_update_data.model_dump(exclude_unset=True) # Changed .dict() to .model_dump()
        for key, value in update_data.items():
            # If 'order' is updated, and more complex logic is needed later (e.g., reordering others),
            # it would be handled here. For now, direct update.
            setattr(db_section, key, value)
        
        db.add(db_section) # Add to session before commit, though often tracked
        db.commit()
        db.refresh(db_section)
    return db_section

def delete_campaign_section(db: Session, section_id: int, campaign_id: int) -> Optional[orm_models.CampaignSection]:
    db_section = get_section(db, section_id=section_id, campaign_id=campaign_id)
    if not db_section:
        return None

    db.delete(db_section)
    db.commit()
    # After commit, the db_section object is expired. If you need to return the object
    # with its state before deletion, you might need to handle it differently,
    # or simply return None or a success indicator. For consistency with other delete ops,
    # returning the object, though its state in session might be "deleted".
    return db_section

async def update_section_order(db: Session, campaign_id: int, ordered_section_ids: List[int]):
    """
    Updates the order of sections for a given campaign.
    :param db: The database session.
    :param campaign_id: The ID of the campaign whose sections are to be reordered.
    :param ordered_section_ids: A list of section IDs in their new desired order.
    """
    # Fetch sections that belong to the campaign and are in the provided list
    sections_to_update = db.query(orm_models.CampaignSection).filter(
        orm_models.CampaignSection.campaign_id == campaign_id,
        orm_models.CampaignSection.id.in_(ordered_section_ids)
    ).all()

    # Create a dictionary for quick lookups of sections by ID
    section_map = {section.id: section for section in sections_to_update}

    for index, section_id in enumerate(ordered_section_ids):
        if section_id in section_map:
            section = section_map[section_id]
            if section.order != index: # Only update if the order has actually changed
                section.order = index
                db.add(section) # Add to session to mark for update
        else:
            # This case should ideally be prevented by checks in the API endpoint
            # If a section_id is provided that doesn't belong to the campaign or doesn't exist,
            # it will be ignored here, or you could raise an error.
            print(f"Warning: Section ID {section_id} not found in campaign {campaign_id} during order update.")

    db.commit()
    # No specific return value needed, or perhaps return the updated sections if desired.
    # For a 204 response, nothing needs to be returned by the CRUD usually.

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

# --- GeneratedImage CRUD Functions ---
def delete_generated_image_by_blob_name(db: Session, blob_name: str, user_id: int) -> Optional[orm_models.GeneratedImage]:
    """
    Deletes a GeneratedImage record from the database based on its filename (blob_name)
    and user_id for authorization.
    Returns the deleted ORM object or None if not found or not authorized.
    """
    db_image = db.query(orm_models.GeneratedImage).filter(
        orm_models.GeneratedImage.filename == blob_name,
        orm_models.GeneratedImage.user_id == user_id
    ).first()

    if not db_image:
        # Could also check if it exists at all and then if user_id matches to give a more specific error,
        # but for deletion, "not found or not authorized" is often sufficient.
        return None

    db.delete(db_image)
    db.commit()
    return db_image
