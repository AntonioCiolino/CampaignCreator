from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app import models, crud
# Removed deps import, will add direct imports for get_db and get_current_active_user
from app.core.security import encrypt_key
from app.models import UserAPIKeyUpdate
from app.db import get_db
from app.services.auth_service import get_current_active_user

router = APIRouter()

@router.put("/me/keys", response_model=models.User)
def update_user_api_keys(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    api_keys_in: UserAPIKeyUpdate,
) -> Any:
    """
    Update current user's OpenAI and Stable Diffusion API keys.
    Pass an empty string or null to clear a key.
    """
    # current_user from deps.get_current_active_user is already a models.User Pydantic model.
    # We need the ORM model to make changes.
    user_orm = crud.get_user(db, user_id=current_user.id)
    if not user_orm:
        # This case should ideally not happen if get_current_active_user works correctly
        # and the user hasn't been deleted mid-session.
        raise HTTPException(status_code=404, detail="User not found in database")

    updated = False
    if api_keys_in.openai_api_key is not None:
        if api_keys_in.openai_api_key == "":
            user_orm.encrypted_openai_api_key = None
        else:
            user_orm.encrypted_openai_api_key = encrypt_key(api_keys_in.openai_api_key)
        updated = True

    if api_keys_in.sd_api_key is not None:
        if api_keys_in.sd_api_key == "":
            user_orm.encrypted_sd_api_key = None
        else:
            user_orm.encrypted_sd_api_key = encrypt_key(api_keys_in.sd_api_key)
        updated = True

    if updated:
        db.add(user_orm)
        db.commit()
        db.refresh(user_orm)

    # Populate the 'provided' fields for the response model
    # Re-fetch or use the updated user_orm to construct the response model
    # to ensure all fields are fresh, especially if there are other ORM event listeners or defaults.
    # However, current_user is a Pydantic model. We need to return a Pydantic model.
    # The user_orm is the source of truth from the DB.

    # Create the response Pydantic model from the ORM model
    response_user = models.User.from_orm(user_orm) # or models.User.model_validate(user_orm)

    # The following lines correctly update the Pydantic model instance
    # that will be returned in the response.
    response_user.openai_api_key_provided = bool(user_orm.encrypted_openai_api_key)
    response_user.sd_api_key_provided = bool(user_orm.encrypted_sd_api_key)
    # Ensure other boolean flags are also set based on the ORM model
    response_user.gemini_api_key_provided = bool(user_orm.encrypted_gemini_api_key)
    response_user.other_llm_api_key_provided = bool(user_orm.encrypted_other_llm_api_key)


    return response_user

# Need to import UploadFile and File for the new endpoint
from fastapi import File, UploadFile
from app.services.image_generation_service import ImageGenerationService # Assuming this service can handle generic image saving

@router.post("/me/avatar", response_model=models.User)
async def upload_avatar(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    file: UploadFile = File(...),
):
    """
    Upload or update the current user's avatar.
    """
    user_orm = crud.get_user(db, user_id=current_user.id)
    if not user_orm:
        raise HTTPException(status_code=404, detail="User not found in database")

    image_service = ImageGenerationService() # This service might need adjustment if it's too specific to "generated" images

    try:
        # We can reuse _save_image_and_log_db if it's suitable for profile pictures,
        # or create a more generic save method in a utility service.
        # For now, let's assume _save_image_and_log_db can be used.
        # The prompt/model_used/size_used might not be relevant for avatars.
        image_bytes = await file.read()
        avatar_filename = f"avatar_user_{current_user.id}_{file.filename}"

        # Using a simplified prompt/metadata for avatar uploads
        avatar_url = await image_service._save_image_and_log_db(
            prompt=f"User avatar for {current_user.username}",
            model_used="user_upload", # Indicates it's an uploaded avatar
            size_used="avatar", # Generic size category
            db=db,
            image_bytes=image_bytes,
            user_id=current_user.id, # Link image to user if GeneratedImage table requires it
            original_filename_from_api=avatar_filename # Use a constructed filename
        )

        if not avatar_url:
            raise HTTPException(status_code=500, detail="Failed to save avatar image and get URL.")

        # Update user's avatar_url
        # crud.update_user expects a Pydantic UserUpdate model
        user_update_payload = models.UserUpdate(avatar_url=avatar_url)
        updated_user_orm = crud.update_user(db=db, db_user=user_orm, user_in=user_update_payload)

        # Construct Pydantic User model for response
        response_user = models.User.from_orm(updated_user_orm)
        # Manually set boolean flags based on ORM model state for the response
        response_user.openai_api_key_provided = bool(updated_user_orm.encrypted_openai_api_key)
        response_user.sd_api_key_provided = bool(updated_user_orm.encrypted_sd_api_key)
        response_user.gemini_api_key_provided = bool(updated_user_orm.encrypted_gemini_api_key)
        response_user.other_llm_api_key_provided = bool(updated_user_orm.encrypted_other_llm_api_key)
        # avatar_url will be set by from_orm

        return response_user

    except HTTPException as http_exc: # Re-raise known HTTP exceptions from image service
        raise http_exc
    except Exception as e:
        print(f"Error uploading avatar for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
