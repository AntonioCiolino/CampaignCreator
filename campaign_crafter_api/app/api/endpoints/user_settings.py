from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app import models, crud
from campaign_crafter_api.app.api import deps
from campaign_crafter_api.app.core.security import encrypt_key # decrypt_key removed as it's not used
from campaign_crafter_api.app.models import UserAPIKeyUpdate

router = APIRouter()

@router.put("/me/keys", response_model=models.User)
def update_user_api_keys(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    api_keys_in: UserAPIKeyUpdate,
) -> Any:
    """
    Update current user's OpenAI and Stable Diffusion API keys.
    Pass an empty string or null to clear a key.
    """
    # current_user from deps.get_current_active_user is already a models.User Pydantic model.
    # We need the ORM model to make changes.
    user_orm = crud.user.get(db, id=current_user.id)
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

    return response_user
