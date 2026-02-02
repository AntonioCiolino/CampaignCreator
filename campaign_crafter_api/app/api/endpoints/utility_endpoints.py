from typing import List, Optional, Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db

from app import models # Keep this for other models if used
# Explicitly import Feature related Pydantic models from app.models
from app.models import Feature as PydanticFeature, FeatureCreate, FeatureUpdate # Using PydanticFeature to avoid conflict with ORM Feature
from app.services.random_table_service import RandomTableService, TableNotFoundError
from app.services.feature_prompt_service import FeaturePromptService
# No, the FeaturePromptItem and FeaturePromptListResponse are fine for the response.
# The `models.Feature` Pydantic model is what we need to return, not FeaturePromptItem.
# Let's adjust the response model of the list_feature_prompts endpoint.

router = APIRouter()

# Instantiate the services.
random_table_service = RandomTableService()
feature_prompt_service = FeaturePromptService()

@router.get("/random-tables", response_model=models.TableNameListResponse, tags=["Utilities"])
async def list_random_table_names(db: Annotated[Session, Depends(get_db)]):
    try:
        table_names = random_table_service.get_available_table_names(db=db)
        return models.TableNameListResponse(table_names=table_names)
    except Exception as e:
        print(f"Error listing random table names: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve list of random tables due to an internal error.")

@router.get("/random-tables/{table_name}/item", response_model=models.RandomItemResponse, tags=["Utilities"])
async def get_random_table_item(table_name: str, db: Annotated[Session, Depends(get_db)]):
    try:
        item = random_table_service.get_random_item_from_table(table_name, db=db)
        return models.RandomItemResponse(table_name=table_name, item=item)
    except TableNotFoundError:
        raise HTTPException(status_code=404, detail=f"Random table '{table_name}' not found.")
    except Exception as e:
        print(f"Error getting random item from table '{table_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve item from table '{table_name}' due to an internal error.")

# The response model should be a list of the Pydantic Feature model
@router.get("/features", response_model=List[PydanticFeature], tags=["Utilities"])
async def list_features(db: Annotated[Session, Depends(get_db)]): # Renamed function for clarity
    try:
        # feature_prompt_service.get_all_features(db) returns List[orm_models.Feature]
        # These ORM objects will be automatically converted to List[PydanticFeature]
        # by FastAPI because the response_model is List[PydanticFeature] and PydanticFeature.Config.from_attributes = True
        db_features_orm = feature_prompt_service.get_all_features(db=db)
        return db_features_orm # FastAPI handles the conversion
    except Exception as e:
        print(f"Error listing features: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve list of features due to an internal error.")

@router.get("/features/by-name/{feature_name}", response_model=PydanticFeature, tags=["Utilities"])
async def get_feature(feature_name: str, db: Annotated[Session, Depends(get_db)]): # Renamed function
    try:
        # crud.get_feature_by_name returns an orm_models.Feature or None
        db_feature_orm = feature_prompt_service.get_prompt(feature_name, db=db) # get_prompt actually returns the template string or None
                                                                              # We need the full feature object.
                                                                              # Let's use crud directly or add a method to service.

        # Correct approach: get the full feature ORM object
        from app import crud as main_crud # Alias to avoid confusion if crud is imported elsewhere in this file
        db_feature_orm_full = main_crud.get_feature_by_name(db, name=feature_name)

        if db_feature_orm_full is None:
            raise HTTPException(status_code=404, detail=f"Feature '{feature_name}' not found.")

        # FastAPI will convert db_feature_orm_full to PydanticFeature
        return db_feature_orm_full
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error getting feature '{feature_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feature '{feature_name}' due to an internal error.")

from app.services.auth_service import get_current_active_user # Correct import path

# Endpoint to create a new feature
@router.post("/features/", response_model=PydanticFeature, status_code=201, tags=["Utilities", "Features Management"])
async def create_new_feature(
    feature_in: FeatureCreate, # This model already includes all new fields
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    # For now, let's assume features created via API are user-specific.
    # System features are typically only from CSV seeding.
    # If we want to allow creating system features via API, further auth checks would be needed.
    user_id_for_feature = current_user.id

    # Check if a feature with this name already exists for this user or as a system feature
    # to prevent duplicates that might cause confusion.
    # This check might need refinement based on desired unique constraints (e.g., name unique per user, or globally unique).
    from app import crud as main_crud # Ensure crud is imported
    existing_feature_user = main_crud.get_feature_by_name(db, name=feature_in.name, user_id=user_id_for_feature)
    existing_feature_system = main_crud.get_feature_by_name(db, name=feature_in.name, user_id=None)

    if existing_feature_user:
        raise HTTPException(status_code=400, detail=f"Feature with name '{feature_in.name}' already exists for this user.")
    if existing_feature_system and user_id_for_feature is not None: # User trying to create a feature with a name of a system feature
        print(f"Warning: User {current_user.username} creating feature '{feature_in.name}' which shadows a system feature.")
        # Allow shadowing for now, but this could be a policy decision.

    try:
        created_feature_orm = main_crud.create_feature(db=db, feature=feature_in, user_id=user_id_for_feature)
        return created_feature_orm # FastAPI handles ORM to Pydantic conversion
    except Exception as e:
        # Log the exception e
        print(f"Error creating feature '{feature_in.name}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while creating the feature: {str(e)}")

@router.put("/features/{feature_id}", response_model=PydanticFeature, tags=["Utilities", "Features Management"])
async def update_existing_feature(
    feature_id: int,
    feature_update_data: FeatureUpdate, # This model includes all new fields as optional
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    from app import crud as main_crud # Ensure crud is imported
    db_feature = main_crud.get_feature(db, feature_id=feature_id)

    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Authorization: Only owner or superuser can update. System features (user_id is None) are not updatable via this API for now.
    if db_feature.user_id is None:
        raise HTTPException(status_code=403, detail="System features cannot be updated via this API.")
    if db_feature.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this feature")

    try:
        updated_feature_orm = main_crud.update_feature(db=db, feature_id=feature_id, feature_update=feature_update_data)
        if updated_feature_orm is None: # Should be caught by get_feature above, but as a safeguard
            raise HTTPException(status_code=404, detail="Feature not found during update attempt.")
        return updated_feature_orm
    except Exception as e:
        # Log the exception e
        print(f"Error updating feature ID {feature_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while updating the feature: {str(e)}")

@router.delete("/features/{feature_id}", response_model=PydanticFeature, tags=["Utilities", "Features Management"])
async def delete_existing_feature(
    feature_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    from app import crud as main_crud # Ensure crud is imported
    db_feature = main_crud.get_feature(db, feature_id=feature_id)

    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Authorization: Only owner or superuser can delete. System features are not deletable.
    if db_feature.user_id is None:
        raise HTTPException(status_code=403, detail="System features cannot be deleted via this API.")
    if db_feature.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this feature")

    try:
        deleted_feature_orm = main_crud.delete_feature(db=db, feature_id=feature_id)
        if deleted_feature_orm is None: # Should be caught by get_feature above
             raise HTTPException(status_code=404, detail="Feature not found during delete attempt.")
        return deleted_feature_orm # Return the deleted object
    except Exception as e:
        # Log the exception e
        print(f"Error deleting feature ID {feature_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while deleting the feature: {str(e)}")
