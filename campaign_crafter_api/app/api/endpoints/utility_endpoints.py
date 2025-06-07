from typing import List, Optional, Annotated # Added Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db

from app import models
from app.models import FeaturePromptItem, FeaturePromptListResponse
from app.services.random_table_service import RandomTableService, TableNotFoundError
from app.services.feature_prompt_service import FeaturePromptService

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
        # Catch-all for unexpected errors during service operation (e.g., if CSV was malformed beyond _load_tables handling)
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

@router.get("/features", response_model=FeaturePromptListResponse, tags=["Utilities"])
async def list_feature_prompts(db: Annotated[Session, Depends(get_db)]):
    try:
        db_features = feature_prompt_service.get_all_features(db=db)
        feature_items = [FeaturePromptItem(name=feature.name, template=feature.template) for feature in db_features]
        return FeaturePromptListResponse(features=feature_items)
    except Exception as e:
        print(f"Error listing feature prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve list of feature prompts due to an internal error.")

@router.get("/features/{feature_name}", response_model=FeaturePromptItem, tags=["Utilities"])
async def get_feature_prompt(feature_name: str, db: Annotated[Session, Depends(get_db)]):
    try:
        prompt_template = feature_prompt_service.get_prompt(feature_name, db=db)
        if prompt_template is None:
            raise HTTPException(status_code=404, detail=f"Feature prompt '{feature_name}' not found.")
        return FeaturePromptItem(name=feature_name, template=prompt_template)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error getting feature prompt '{feature_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feature prompt '{feature_name}' due to an internal error.")
