from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models # Removed orm_models as not directly used
from app.db import get_db
from app.services.auth_service import get_current_active_user # Import for auth

router_features = APIRouter()
router_roll_tables = APIRouter()

# --- Feature Endpoints ---
@router_features.post("/", response_model=models.Feature)
def create_feature(
    feature: models.FeatureCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    # Check if a feature with this name already exists for this user
    # Users can have features with the same name as system features (user_id=None)
    db_feature_by_name = crud.get_feature_by_name(db, name=feature.name, user_id=current_user.id)
    if db_feature_by_name:
        raise HTTPException(
            status_code=400, detail="You already have a feature with this name."
        )
    return crud.create_feature(db=db, feature=feature, user_id=current_user.id)

@router_features.get("/{feature_id}", response_model=models.Feature)
def read_feature(
    feature_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_feature = crud.get_feature(db, feature_id=feature_id)
    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    is_owner = db_feature.user_id == current_user.id
    is_system_feature = db_feature.user_id is None
    can_access = is_owner or is_system_feature or current_user.is_superuser

    if not can_access:
        raise HTTPException(status_code=403, detail="Not authorized to access this feature")
    return db_feature

@router_features.get("/", response_model=List[models.Feature])
def read_features(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100
):
    # This will get the user's features + system features
    features = crud.get_features(db, skip=skip, limit=limit, user_id=current_user.id)
    return features

@router_features.put("/{feature_id}", response_model=models.Feature)
def update_feature(
    feature_id: int,
    feature_update: models.FeatureUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_feature = crud.get_feature(db, feature_id=feature_id)
    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    is_owner = db_feature.user_id == current_user.id
    is_system_feature = db_feature.user_id is None

    if not current_user.is_superuser:
        if is_system_feature:
            raise HTTPException(status_code=403, detail="Not authorized to update system feature")
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not authorized to update this feature")
    # Superuser can update any feature.

    if feature_update.name is not None and feature_update.name != db_feature.name:
        # Determine the context for the name uniqueness check.
        name_check_user_id = None # Default to system context
        if db_feature.user_id is not None: # If it's a user-owned feature
            name_check_user_id = db_feature.user_id
        # If a superuser is editing a system feature, name_check_user_id remains None.
        # If a superuser is editing User A's feature, name_check_user_id is User A's ID.
        # If User A is editing their own feature, name_check_user_id is User A's ID.

        existing_feature_with_name = crud.get_feature_by_name(db, name=feature_update.name, user_id=name_check_user_id)

        if existing_feature_with_name and existing_feature_with_name.id != feature_id:
            detail = "Another feature with this name already exists for this user."
            if name_check_user_id is None:
                detail = "Another system feature with this name already exists."
            raise HTTPException(
                status_code=400, detail=detail
            )
            
    updated_feature = crud.update_feature(
        db=db, feature_id=feature_id, feature_update=feature_update
    )
    # crud.update_feature itself returns Optional[orm_models.Feature], so check is good
    if updated_feature is None:
         # This should ideally not be reached if db_feature was found initially,
         # but as a safeguard if update_feature had its own fetch that failed.
         raise HTTPException(status_code=404, detail="Feature not found during update process")
    return updated_feature

@router_features.delete("/{feature_id}", response_model=models.Feature)
def delete_feature(
    feature_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_feature_to_delete = crud.get_feature(db, feature_id=feature_id)
    if db_feature_to_delete is None:
        raise HTTPException(status_code=404, detail="Feature not found to delete")

    is_owner = db_feature_to_delete.user_id == current_user.id
    is_system_feature = db_feature_to_delete.user_id is None

    if not current_user.is_superuser:
        if is_system_feature:
            raise HTTPException(status_code=403, detail="Not authorized to delete system feature")
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not authorized to delete this feature")
    # Superuser can delete any feature.

    deleted_feature = crud.delete_feature(db, feature_id=feature_id)
    # crud.delete_feature returns the deleted object or None if not found
    if deleted_feature is None:
        # This case should be covered by the initial check, but good for robustness
        raise HTTPException(status_code=404, detail="Feature not found during deletion process")
    return deleted_feature

# --- Rolltable Endpoints ---
@router_roll_tables.post("/", response_model=models.RollTable)
def create_roll_table(
    roll_table: models.RollTableCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_roll_table_by_name = crud.get_roll_table_by_name(db, name=roll_table.name)
    if db_roll_table_by_name:
        raise HTTPException(
            status_code=400, detail="Rolltable with this name already exists"
        )
    for item in roll_table.items:
        if item.min_roll > item.max_roll:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid item '{item.description}': min_roll ({item.min_roll}) cannot be greater than max_roll ({item.max_roll})."
            )
    return crud.create_roll_table(db=db, roll_table=roll_table, user_id=current_user.id)

@router_roll_tables.get("/{roll_table_id}", response_model=models.RollTable)
def read_roll_table(roll_table_id: int, db: Annotated[Session, Depends(get_db)]):
    db_roll_table = crud.get_roll_table(db, roll_table_id=roll_table_id)
    if db_roll_table is None:
        raise HTTPException(status_code=404, detail="Rolltable not found")
    return db_roll_table

@router_roll_tables.get("/", response_model=List[models.RollTable])
def read_roll_tables(
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None
):
    roll_tables = crud.get_roll_tables(db, skip=skip, limit=limit, user_id=user_id)
    return roll_tables

@router_roll_tables.put("/{roll_table_id}", response_model=models.RollTable)
def update_roll_table(
    roll_table_id: int,
    roll_table_update: models.RollTableUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_roll_table = crud.get_roll_table(db, roll_table_id=roll_table_id)
    if not db_roll_table:
        raise HTTPException(status_code=404, detail="Rolltable not found")

    if not current_user.is_superuser and db_roll_table.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this roll table")

    if roll_table_update.name is not None and roll_table_update.name != db_roll_table.name:
        existing_roll_table_with_name = crud.get_roll_table_by_name(db, name=roll_table_update.name)
        if existing_roll_table_with_name and existing_roll_table_with_name.id != roll_table_id:
            raise HTTPException(
                status_code=400, detail="Another rolltable with this name already exists"
            )
    
    if roll_table_update.items is not None:
        for item in roll_table_update.items:
            if item.min_roll > item.max_roll:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid item '{item.description}': min_roll ({item.min_roll}) cannot be greater than max_roll ({item.max_roll})."
                )

    updated_roll_table = crud.update_roll_table(
        db=db, roll_table_id=roll_table_id, roll_table_update=roll_table_update
    )
    if updated_roll_table is None:
        raise HTTPException(status_code=404, detail="Rolltable not found during update")
    return updated_roll_table

@router_roll_tables.delete("/{roll_table_id}", response_model=models.RollTable)
def delete_roll_table(
    roll_table_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_roll_table_to_delete = crud.get_roll_table(db, roll_table_id=roll_table_id)
    if db_roll_table_to_delete is None:
        raise HTTPException(status_code=404, detail="Rolltable not found to delete")

    if not current_user.is_superuser and db_roll_table_to_delete.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this roll table")

    deleted_roll_table = crud.delete_roll_table(db, roll_table_id=roll_table_id)
    if deleted_roll_table is None: # Should not happen
        raise HTTPException(status_code=404, detail="Rolltable not found during deletion")
    return deleted_roll_table

@router_roll_tables.post("/copy-system-tables", response_model=List[models.RollTable])
def copy_system_tables_to_user_account(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Copies all system roll tables to the authenticated user's account.
    If a table with the same name already exists for the user, it will be skipped.
    """
    system_tables = crud.get_roll_tables(db=db, user_id=None) # Get only system tables

    copied_tables = []
    for system_table in system_tables:
        # Check if a table with the same name already exists for this user
        existing_user_table = crud.get_roll_table_by_name(
            db=db, name=system_table.name, user_id=current_user.id
        )
        if not existing_user_table:
            # If it doesn't exist, copy it
            copied_table = crud.copy_system_roll_table_to_user(
                db=db, system_table=system_table, user_id=current_user.id
            )
            copied_tables.append(copied_table)

    return copied_tables
