from typing import List, Optional, Annotated, Dict # Added Dict for type hint
from datetime import datetime # Added for timestamping messages

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified # Added for JSON field modification tracking

from app import crud, models, orm_models
from app.core.config import settings # Import settings
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
    # print(f"[API PUT /characters/{character_id}] Received update request. Payload: {character_update.model_dump_json(indent=2)}") # LOG REMOVED
    # if character_update.image_urls is not None: # LOG REMOVED
    #     print(f"[API PUT /characters/{character_id}] image_urls in request: {character_update.image_urls}") # LOG REMOVED
    # else: # LOG REMOVED
    #     print(f"[API PUT /characters/{character_id}] image_urls field is None in request.") # LOG REMOVED

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

# The original/older generate-response without persistence is removed.
# The version with persistence and DB history context is defined later in the file.

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
                model=request_body.gemini_model_name,
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


# --- Character Chat Endpoints ---

# The POST /{character_id}/chat endpoint (create_character_chat_message) has been removed.
# Message creation and persistence are now handled by the POST /{character_id}/generate-response endpoint.

# --- Character Chat Endpoints ---

# The create_character_chat_message endpoint has been removed as its functionality
# (saving messages and returning history) is effectively covered by generate_character_chat_response
# and a dedicated GET endpoint for history would be more appropriate if needed.

@router.post("/{character_id}/generate-response", response_model=models.LLMTextGenerationResponse)
async def generate_character_chat_response( # Renamed function
    character_id: int,
    request_body: models.LLMGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Generates a text response from the character.
    The entire conversation history for this user-character pair is stored
    as a JSON list in a single row in the 'chat_messages' table.
    This endpoint appends the new user message and AI response to this list.
    """
    from datetime import datetime # Import here for usage

    # Constants for summarization trigger are now imported from settings
    # SUMMARIZATION_INTERVAL = settings.CHAT_SUMMARIZATION_INTERVAL
    # MIN_MESSAGES_FOR_SUMMARIZATION_TRIGGER = settings.CHAT_MIN_MESSAGES_FOR_SUMMARY_TRIGGER
    # These specific constants are used in the trigger logic below.

    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to generate responses for this character")

    if not request_body.prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt cannot be empty.")

    # 1. Get or create the conversation record for this user and character
    conversation_orm_object = crud.get_or_create_user_character_conversation(
        db=db, character_id=character_id, user_id=current_user.id
    )

    # conversation_history is a Python list of dicts. Initialize if None (though ORM default should handle it).
    current_conversation_list: List[Dict] = conversation_orm_object.conversation_history if conversation_orm_object.conversation_history is not None else []

    # 2. Append the current user's message to this list
    user_message_entry = {
        "speaker": "user",
        "text": request_body.prompt,
        "timestamp": datetime.utcnow().isoformat()
    }
    current_conversation_list.append(user_message_entry)

    # 3. Prepare context for the LLM (e.g., last N messages)
    # Map to models.ConversationMessageContext (speaker, text) for LLM service
    # Send up to last 10 entries (including current user's new message) for context
    history_for_llm_context_dicts = current_conversation_list[-10:]

    chat_history_for_llm_service = [
        models.ConversationMessageContext(speaker=msg["speaker"], text=msg["text"])
        for msg in history_for_llm_context_dicts
    ]

    provider_name_from_request: Optional[str] = None
    model_specific_id_from_request: Optional[str] = None
    if request_body.model_id_with_prefix and "/" in request_body.model_id_with_prefix:
        provider_name_from_request, model_specific_id_from_request = request_body.model_id_with_prefix.split("/",1)
    elif request_body.model_id_with_prefix:
        model_specific_id_from_request = request_body.model_id_with_prefix

    try:
        orm_user = crud.get_user(db, current_user.id)
        if not orm_user:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve user data for LLM service.")

        llm_service = crud.get_llm_service(
            db=db,
            current_user_orm=orm_user,
            provider_name=provider_name_from_request,
            model_id_with_prefix=request_body.model_id_with_prefix,
        )

        # 4. Call the LLM service
        # user_prompt is the current raw prompt, chat_history is the context *including* this latest user prompt
        # Prepare augmented character notes including memory summary for the LLM service call
        base_character_notes = db_character.notes_for_llm or ""
        # The conversation_orm_object was fetched/created earlier and contains the latest memory_summary
        memory_summary_text = conversation_orm_object.memory_summary or ""

        effective_character_notes_for_llm = base_character_notes
        if memory_summary_text:
            effective_character_notes_for_llm = (
                f"**Summary of Your Past Interactions with this User:**\n{memory_summary_text}\n\n"
                f"**Your Core Persona & Notes:**\n{base_character_notes}"
            )

        generated_text = await llm_service.generate_character_response(
            character_name=db_character.name,
            character_notes=effective_character_notes_for_llm, # Pass augmented notes
            user_prompt=request_body.prompt, # Current user's immediate message
            chat_history=chat_history_for_llm_service[:-1] if chat_history_for_llm_service else [], # Pass history *before* current prompt
            current_user=current_user,
            db=db,
            model=model_specific_id_from_request,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens
        )

        # 5. Append AI's response to the list
        ai_message_entry = {
            "speaker": "assistant", # Using "assistant" for AI role
            "text": generated_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        current_conversation_list.append(ai_message_entry)

        # Explicitly mark the conversation_history field as modified before saving
        flag_modified(conversation_orm_object, "conversation_history")

        # 6. Save the updated conversation list back to the database
        crud.update_user_character_conversation(
            db=db,
            conversation_record=conversation_orm_object,
            new_history_list=current_conversation_list
            # Note: update_user_character_conversation itself also assigns new_history_list
            # to conversation_record.conversation_history. The flag_modified ensures this is picked up by SQLAlchemy.
        )
        # print(f"Conversation (JSON) updated for char_id={character_id}, user_id={current_user.id}") # Debug print removed

        # After saving the current turn, check if summarization should be triggered
        if len(current_conversation_list) >= settings.CHAT_MIN_MESSAGES_FOR_SUMMARY_TRIGGER and \
           len(current_conversation_list) % settings.CHAT_SUMMARIZATION_INTERVAL == 0:
            try:
                # print(f"Attempting to summarize conversation for char_id={character_id}, user_id={current_user.id}") # Debug print removed
                await crud.update_conversation_summary(
                    db=db,
                    conversation_orm=conversation_orm_object, # Pass the updated ORM object
                    llm_service=llm_service, # Reuse the initialized LLM service
                    current_user_model=current_user, # Pass Pydantic User
                    character_name=db_character.name,
                    character_notes=(db_character.notes_for_llm or "") # Pass original notes for summary context
                )
                # print(f"Summarization task completed for char_id={character_id}, user_id={current_user.id}") # Debug print removed
            except Exception as summary_ex:
                # Log summarization error but don't let it fail the main response to the user
                # This print is an error log, so it can stay.
                print(f"ERROR:API:generate_character_chat_response: Summarization failed for char_id={character_id}, user_id={current_user.id}: {summary_ex}")

        # 7. Return the AI's current textual response
        return models.LLMTextGenerationResponse(text=generated_text)

    except crud.LLMServiceUnavailableError as e:
        # If LLM fails, we should decide if we still save the user's message.
        # Current logic: user message was appended to list, but list not yet saved by update_user_character_conversation.
        # To save user message even if LLM fails, call update_user_character_conversation before LLM call.
        # For now, if LLM fails, the appended user message (and any AI message) won't be committed.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except crud.LLMGenerationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Unexpected error during character response generation: {type(e).__name__} - {str(e)}")
        # import traceback; traceback.print_exc();
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while generating the character response.")

# This replaces all previous versions of the generate-response endpoint.

@router.get("/{character_id}/chat", response_model=List[models.ConversationMessageEntry])
def get_character_chat_history(
    character_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Retrieves the full conversation history for a given character and the current user.
    """
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if db_character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this chat history")

    conversation_orm_object = crud.get_or_create_user_character_conversation(
        db=db, character_id=character_id, user_id=current_user.id
    )

    history_as_pydantic = []
    for i, msg in enumerate(conversation_orm_object.conversation_history):
        try:
            if isinstance(msg.get("timestamp"), datetime):
                msg["timestamp"] = msg["timestamp"].isoformat()
            history_as_pydantic.append(models.ConversationMessageEntry(**msg))
        except Exception as e:
            print(f"Failed to load chat history. Data corrupted at index {i}. Error: {e}. Message data: {msg}")
            continue
    return history_as_pydantic
