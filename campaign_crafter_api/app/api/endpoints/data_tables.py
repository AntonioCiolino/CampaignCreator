from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, orm_models
from app.db import get_db

router_features = APIRouter()
router_roll_tables = APIRouter()

# --- Feature Endpoints ---
@router_features.post("/", response_model=models.Feature)
def create_feature(
    feature: models.FeatureCreate, db: Session = Depends(get_db)
):
    db_feature_by_name = crud.get_feature_by_name(db, name=feature.name)
    if db_feature_by_name:
        raise HTTPException(
            status_code=400, detail="Feature with this name already exists"
        )
    return crud.create_feature(db=db, feature=feature)

@router_features.get("/{feature_id}", response_model=models.Feature)
def read_feature(feature_id: int, db: Session = Depends(get_db)):
    db_feature = crud.get_feature(db, feature_id=feature_id)
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return db_feature

@router_features.get("/", response_model=List[models.Feature])
def read_features(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    features = crud.get_features(db, skip=skip, limit=limit)
    return features

@router_features.put("/{feature_id}", response_model=models.Feature)
def update_feature(
    feature_id: int,
    feature_update: models.FeatureUpdate,
    db: Session = Depends(get_db),
):
    db_feature = crud.get_feature(db, feature_id=feature_id)
    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    if feature_update.name is not None and feature_update.name != db_feature.name:
        existing_feature_with_name = crud.get_feature_by_name(db, name=feature_update.name)
        if existing_feature_with_name and existing_feature_with_name.id != feature_id:
            raise HTTPException(
                status_code=400, detail="Another feature with this name already exists"
            )
            
    updated_feature = crud.update_feature(
        db=db, feature_id=feature_id, feature_update=feature_update
    )
    # crud.update_feature itself should handle the case where feature_id doesn't exist,
    # but the check above is good for immediate feedback and name check.
    # If updated_feature is None, it means the feature was not found by crud.update_feature,
    # which should ideally be caught by the initial check.
    if updated_feature is None:
         raise HTTPException(status_code=404, detail="Feature not found during update") # Should not happen if initial check is done
    return updated_feature

@router_features.delete("/{feature_id}", response_model=models.Feature)
def delete_feature(feature_id: int, db: Session = Depends(get_db)):
    db_feature = crud.delete_feature(db, feature_id=feature_id)
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return db_feature

# --- Rolltable Endpoints ---
@router_roll_tables.post("/", response_model=models.RollTable)
def create_roll_table(
    roll_table: models.RollTableCreate, db: Session = Depends(get_db)
):
    db_roll_table_by_name = crud.get_roll_table_by_name(db, name=roll_table.name)
    if db_roll_table_by_name:
        raise HTTPException(
            status_code=400, detail="Rolltable with this name already exists"
        )
    # Additional validation for items if necessary (e.g., min_roll <= max_roll)
    # This could also be done in Pydantic models with validators
    for item in roll_table.items:
        if item.min_roll > item.max_roll:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid item '{item.description}': min_roll ({item.min_roll}) cannot be greater than max_roll ({item.max_roll})."
            )
    return crud.create_roll_table(db=db, roll_table=roll_table)

@router_roll_tables.get("/{roll_table_id}", response_model=models.RollTable)
def read_roll_table(roll_table_id: int, db: Session = Depends(get_db)):
    db_roll_table = crud.get_roll_table(db, roll_table_id=roll_table_id)
    if db_roll_table is None:
        raise HTTPException(status_code=404, detail="Rolltable not found")
    return db_roll_table

@router_roll_tables.get("/", response_model=List[models.RollTable])
def read_roll_tables(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    roll_tables = crud.get_roll_tables(db, skip=skip, limit=limit)
    return roll_tables

@router_roll_tables.put("/{roll_table_id}", response_model=models.RollTable)
def update_roll_table(
    roll_table_id: int,
    roll_table_update: models.RollTableUpdate,
    db: Session = Depends(get_db),
):
    db_roll_table = crud.get_roll_table(db, roll_table_id=roll_table_id)
    if not db_roll_table:
        raise HTTPException(status_code=404, detail="Rolltable not found")

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
    if updated_roll_table is None: # Should be caught by the initial check
        raise HTTPException(status_code=404, detail="Rolltable not found during update")
    return updated_roll_table

@router_roll_tables.delete("/{roll_table_id}", response_model=models.RollTable)
def delete_roll_table(roll_table_id: int, db: Session = Depends(get_db)):
    db_roll_table = crud.delete_roll_table(db, roll_table_id=roll_table_id)
    if db_roll_table is None:
        raise HTTPException(status_code=404, detail="Rolltable not found")
    return db_roll_table
