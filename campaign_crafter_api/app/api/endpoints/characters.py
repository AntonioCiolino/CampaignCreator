from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, orm_models
from app.db import get_db
from app.services.auth_service import get_current_active_user

router = APIRouter()

@router.post("/", response_model=models.Character, status_code=status.HTTP_201_CREATED)
def create_new_character(
    character_in: models.CharacterCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Create a new character for the current user.
    """
    db_character = crud.create_character(db=db, character=character_in, user_id=current_user.id)
    return db_character

@router.get("/", response_model=List[models.Character])
def read_user_characters(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve characters for the current user.
    """
    characters = crud.get_characters_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return characters

@router.get("/{character_id}", response_model=models.Character)
def read_single_character(
    character_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Retrieve a specific character by ID.
    Ensures the character belongs to the current user.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this character")
    return db_character

@router.put("/{character_id}", response_model=models.Character)
def update_existing_character(
    character_id: int,
    character_update: models.CharacterUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Update an existing character.
    Ensures the character belongs to the current user.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this character")

    updated_character = crud.update_character(db=db, character_id=character_id, character_update=character_update)
    if updated_character is None: # Should not happen if previous checks passed
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found during update attempt")
    return updated_character

@router.delete("/{character_id}", response_model=models.Character)
def delete_existing_character(
    character_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Delete a character.
    Ensures the character belongs to the current user.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this character")

    deleted_character_orm = crud.delete_character(db=db, character_id=character_id)
    if deleted_character_orm is None: # Should not happen
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found during deletion attempt")
    return deleted_character_orm

@router.post("/{character_id}/campaigns/{campaign_id}", response_model=models.Character)
def link_character_to_campaign(
    character_id: int,
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Associate a character with a campaign.
    Ensures the character and campaign belong to the current user.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this character")

    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to link to this campaign")

    character_with_campaign = crud.add_character_to_campaign(db=db, character_id=character_id, campaign_id=campaign_id)
    if character_with_campaign is None: # Should indicate an issue if character or campaign wasn't found by CRUD, already checked.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not link character to campaign")
    return character_with_campaign

@router.delete("/{character_id}/campaigns/{campaign_id}", response_model=models.Character)
def unlink_character_from_campaign(
    character_id: int,
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Remove association between a character and a campaign.
    Ensures the character and campaign belong to the current user.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this character")

    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None: # Check if campaign exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    # No need to check campaign ownership for unlinking if character ownership is confirmed,
    # as the link itself implies user had rights to create it.
    # However, for consistency, checking campaign ownership is fine.
    if db_campaign.owner_id != current_user.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify links for this campaign")


    character_after_unlink = crud.remove_character_from_campaign(db=db, character_id=character_id, campaign_id=campaign_id)
    if character_after_unlink is None: # Should indicate an issue if character or campaign wasn't found by CRUD
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not unlink character from campaign")
    return character_after_unlink

# Endpoint to get characters for a specific campaign
# This could also live in campaigns.py, but placing it here for character-centric view.
@router.get("/campaign/{campaign_id}/characters", response_model=List[models.Character])
def read_campaign_characters(
    campaign_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve characters associated with a specific campaign.
    Ensures the campaign belongs to the current user.
    """
    db_campaign = crud.get_campaign(db=db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access characters for this campaign")

    characters = crud.get_characters_by_campaign(db=db, campaign_id=campaign_id, skip=skip, limit=limit)
    return characters

@router.get("/{character_id}/campaigns", response_model=List[models.Campaign])
def read_character_campaigns(
    character_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Retrieve all campaigns associated with a specific character.
    Ensures the character belongs to the current user.
    """
    # First, verify the character exists and belongs to the current user
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        # This check ensures user can only query campaigns for their own characters
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this character's campaigns")

    # Now, fetch the campaigns for this character
    campaigns = crud.get_campaigns_for_character(db=db, character_id=character_id)

    # The campaigns returned by crud.get_campaigns_for_character are ORM models.
    # FastAPI will automatically convert them to List[models.Campaign] Pydantic models.
    # Note: The crud.get_campaigns_for_character itself doesn't filter by campaign ownership,
    # but since we've verified character ownership, this implies the user has a right to know
    # which of their campaigns this character (that they own) is part of.
    # If campaigns could be shared, further filtering might be needed here based on campaign ownership or sharing rules.
    # For now, assuming all campaigns a user's character is linked to are implicitly viewable in this context.
    return campaigns

@router.post("/{character_id}/generate-response", response_model=models.LLMTextGenerationResponse)
async def generate_character_llm_response(
    character_id: int,
    request_body: models.LLMGenerationRequest, # Reusing existing model
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Generates a text response as if spoken or written by the specified character,
    based on the provided prompt and character's notes.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to generate responses for this character")

    if not request_body.prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt cannot be empty.")

    # Determine LLM service and model
    # For character interaction, campaign context might be less relevant.
    # We primarily use the user's general LLM settings or what's specified in the request.
    # The get_llm_service factory can handle finding the appropriate service.
    # No direct campaign object is passed to get_llm_service here, so it would use user/system defaults.

    # Helper to extract provider and model from model_id_with_prefix
    # This logic might be better in a shared utility or within get_llm_service itself if it's complex
    provider_name_from_request: Optional[str] = None
    model_specific_id_from_request: Optional[str] = None
    if request_body.model_id_with_prefix and "/" in request_body.model_id_with_prefix:
        provider_name_from_request, model_specific_id_from_request = request_body.model_id_with_prefix.split("/",1)
    elif request_body.model_id_with_prefix:
        model_specific_id_from_request = request_body.model_id_with_prefix
        # provider_name_from_request will remain None, get_llm_service will try to infer or use default

    try:
        # Fetch ORM user for API key access within get_llm_service
        orm_user = crud.get_user(db, current_user.id)
        if not orm_user: # Should not happen if current_user is valid
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve user data for LLM service.")

        llm_service = crud.get_llm_service( # crud.py re-exports get_llm_service from llm_factory
            db=db,
            current_user_orm=orm_user,
            provider_name=provider_name_from_request,
            model_id_with_prefix=request_body.model_id_with_prefix,
            # campaign=None # Explicitly no campaign context for this generic character interaction
        )

        generated_text = await llm_service.generate_character_response(
            character_name=db_character.name,
            character_notes=db_character.notes_for_llm or "", # Pass empty string if notes are None
            user_prompt=request_body.prompt,
            chat_history=request_body.chat_history,
            current_user=current_user, # Pass Pydantic user model
            db=db,
            model=model_specific_id_from_request, # Pass only the model part if prefix was used
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens
        )
        return models.LLMTextGenerationResponse(text=generated_text)

    except crud.LLMServiceUnavailableError as e: # crud.py re-exports this
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except crud.LLMGenerationError as e: # crud.py re-exports this
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ValueError as e: # E.g. empty prompt if not caught earlier, or other validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log the full error for debugging
        print(f"Unexpected error during character response generation: {type(e).__name__} - {str(e)}")
        # Consider logging traceback as well: import traceback; traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while generating the character response.")

@router.post("/{character_id}/generate-image", response_model=models.Character)
async def generate_character_image_endpoint(
    character_id: int,
    request_body: models.CharacterImageGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    # Dependency inject ImageGenerationService
    img_gen_service: Annotated[crud.ImageGenerationService, Depends(crud.ImageGenerationService)]
):
    """
    Generates an image for a character based on their appearance description
    and optional additional details. Adds the image URL to the character's image_urls list.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to generate images for this character")

    base_prompt = f"Character: {db_character.name}."
    if db_character.appearance_description:
        base_prompt += f" Appearance: {db_character.appearance_description}."
    else:
        base_prompt += " A typical fantasy character." # Fallback if no appearance desc

    if request_body.additional_prompt_details:
        base_prompt += f" Additional details: {request_body.additional_prompt_details}."

    # Default to a common style if not overridden by other details
    if "digital art" not in base_prompt.lower() and "photo" not in base_prompt.lower() and "illustration" not in base_prompt.lower():
        base_prompt += " Style: detailed digital illustration."

    image_url: Optional[str] = None
    model_to_use = request_body.model_name or "dall-e" # Default to dall-e if not specified

    try:
        if model_to_use == "dall-e":
            image_url = await img_gen_service.generate_image_dalle(
                prompt=base_prompt,
                db=db,
                current_user=current_user,
                size=request_body.size, # Will use service/settings default if None
                quality=request_body.quality, # Will use service/settings default if None
                user_id=current_user.id,
                # campaign_id=None # Character images are not tied to a specific campaign context here
            )
        elif model_to_use == "stable-diffusion":
            # Get user's SD engine preference or system default
            user_orm = crud.get_user(db, current_user.id)
            sd_engine_to_use = user_orm.sd_engine_preference if user_orm and user_orm.sd_engine_preference else settings.STABLE_DIFFUSION_DEFAULT_ENGINE

            image_url = await img_gen_service.generate_image_stable_diffusion(
                prompt=base_prompt,
                db=db,
                current_user=current_user,
                size=request_body.size,
                steps=request_body.steps,
                cfg_scale=request_body.cfg_scale,
                user_id=current_user.id,
                sd_engine_id=sd_engine_to_use
                # campaign_id=None
            )
        elif model_to_use == "gemini":
             image_url = await img_gen_service.generate_image_gemini(
                prompt=base_prompt,
                db=db,
                current_user=current_user,
                size=request_body.size,
                model=request_body.gemini_model_name, # Pass specific gemini model if provided
                user_id=current_user.id
                # campaign_id=None
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported image generation model: {model_to_use}")

        if not image_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Image generation succeeded but no URL was returned.")

        # Append the new image URL to the character's image_urls list
        updated_image_urls = list(db_character.image_urls) if db_character.image_urls else []
        if image_url not in updated_image_urls: # Avoid duplicates, though unlikely with UUIDs
            updated_image_urls.append(image_url)

        character_update_payload = models.CharacterUpdate(image_urls=updated_image_urls)
        updated_db_character = crud.update_character(
            db=db,
            character_id=character_id,
            character_update=character_update_payload
        )
        if not updated_db_character:
             # This should ideally not happen if character was fetched successfully before
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update character with new image URL.")

        return updated_db_character

    except HTTPException as e: # Re-raise HTTPExceptions from services or this function
        raise e
    except Exception as e:
        print(f"Unexpected error during character image generation: {type(e).__name__} - {str(e)}")
        # import traceback; traceback.print_exc() # For more detailed server-side logging if needed
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while generating the character image.")

@router.post("/generate-aspect", response_model=models.CharacterAspectGenerationResponse)
async def generate_character_aspect(
    request: models.CharacterAspectGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Generates text for a specific aspect of a character (e.g., description, appearance)
    using an LLM.
    """
    # Fetch the ORM user model as crud.generate_character_aspect_text expects it
    # to potentially access API keys via relationships or direct attributes on the ORM model.
    current_user_orm = crud.get_user(db, user_id=current_user.id)
    if not current_user_orm:
        # This should ideally not happen if current_user (Pydantic model) is valid
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized.")

    try:
        generated_text = await crud.generate_character_aspect_text(
            db=db,
            current_user_orm=current_user_orm,
            request=request
        )
        return models.CharacterAspectGenerationResponse(generated_text=generated_text)
    except crud.LLMServiceUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        # Log the full error for debugging on the server
        # import traceback; traceback.print_exc(); # Consider for detailed logging
        print(f"API Error in /generate-aspect: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate character aspect: {str(e)}")
