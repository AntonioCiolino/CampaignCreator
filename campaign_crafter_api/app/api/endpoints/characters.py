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
    skip: int = 0,
    limit: int = 100,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
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
    skip: int = 0,
    limit: int = 100,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
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
