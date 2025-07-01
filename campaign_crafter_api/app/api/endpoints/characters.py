from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, orm_models
from app.db import get_db
from app.api.endpoints.auth import get_current_active_user

router = APIRouter()

@router.post("/campaigns/{campaign_id}/characters", response_model=models.Character, status_code=201)
def create_character_for_campaign(
    campaign_id: int,
    character: models.CharacterCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_campaign = crud.get_campaign(db, campaign_id=campaign_id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add characters to this campaign")

    # Ensure character.campaign_id is set correctly, overriding any value from the request body
    character_data = character.model_dump()
    character_data["campaign_id"] = campaign_id

    # Pydantic models expect HttpUrl types to be strings when creating from dict,
    # so convert them if they are already HttpUrl objects.
    if "icon_url" in character_data and character_data["icon_url"] is not None:
        character_data["icon_url"] = str(character_data["icon_url"])

    if "images" in character_data and character_data["images"] is not None:
        for img_data in character_data["images"]:
            if "url" in img_data and img_data["url"] is not None:
                img_data["url"] = str(img_data["url"])

    # Re-create the CharacterCreate model with the corrected data
    # This ensures validation happens correctly with string URLs
    validated_character_create = models.CharacterCreate(**character_data)

    return crud.create_character(db=db, character=validated_character_create)

@router.get("/campaigns/{campaign_id}/characters", response_model=List[models.Character])
def read_characters_for_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    db_campaign = crud.get_campaign(db, campaign_id=campaign_id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if db_campaign.owner_id != current_user.id:
        # Allow public read or implement more granular permissions if needed
        # For now, only owner can see characters
        raise HTTPException(status_code=403, detail="Not authorized to view characters for this campaign")
    characters = crud.get_characters_by_campaign(db, campaign_id=campaign_id, skip=skip, limit=limit)
    return characters

@router.get("/characters/{character_id}", response_model=models.Character)
def read_character(
    character_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    db_campaign = crud.get_campaign(db, campaign_id=db_character.campaign_id)
    if not db_campaign or db_campaign.owner_id != current_user.id:
        # Allow public read or implement more granular permissions if needed
        # For now, only owner can see character
        raise HTTPException(status_code=403, detail="Not authorized to view this character")
    return db_character

@router.put("/characters/{character_id}", response_model=models.Character)
def update_character(
    character_id: int,
    character: models.CharacterUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    db_campaign = crud.get_campaign(db, campaign_id=db_character.campaign_id)
    if not db_campaign or db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this character")

    # Convert HttpUrl to string for icon_url if present
    character_data = character.model_dump(exclude_unset=True)
    if "icon_url" in character_data and character_data["icon_url"] is not None:
        character_data["icon_url"] = str(character_data["icon_url"])

    # Convert HttpUrl to string for image urls if present
    if "images" in character_data and character_data["images"] is not None:
        for img_data in character_data["images"]:
            if "url" in img_data and img_data["url"] is not None:
                img_data["url"] = str(img_data["url"])

    # Create a new CharacterUpdate instance with potentially modified data
    validated_character_update = models.CharacterUpdate(**character_data)

    return crud.update_character(db=db, character_id=character_id, character_update=validated_character_update)

@router.delete("/characters/{character_id}", status_code=204)
def delete_character(
    character_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    db_campaign = crud.get_campaign(db, campaign_id=db_character.campaign_id)
    if not db_campaign or db_campaign.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this character")

    crud.delete_character(db=db, character_id=character_id)
    return None # FastAPI will return 204 No Content
