from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session # Not used here, but good practice for API modules

from app import models # Pydantic models
from app.models import FeaturePromptItem, FeaturePromptListResponse # Import new models
from app.services.random_table_service import RandomTableService, TableNotFoundError
from app.services.feature_prompt_service import FeaturePromptService # Import FeaturePromptService
# from app.db import get_db # Example if DB was needed for other utility endpoints

router = APIRouter()

# Instantiate the services.
random_table_service = RandomTableService()
feature_prompt_service = FeaturePromptService() # Instantiate FeaturePromptService

@router.get("/random-tables", response_model=models.TableNameListResponse, tags=["Utilities"])
async def list_random_table_names():
    try:
        table_names = random_table_service.get_available_table_names()
        return models.TableNameListResponse(table_names=table_names) # Corrected to use models
    except Exception as e:
        # Catch-all for unexpected errors during service operation (e.g., if CSV was malformed beyond _load_tables handling)
        print(f"Error listing random table names: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve list of random tables due to an internal error.")

@router.get("/random-tables/{table_name}/item", response_model=models.RandomItemResponse, tags=["Utilities"])
async def get_random_table_item(table_name: str):
    try:
        item = random_table_service.get_random_item_from_table(table_name)
        # The service now returns an item string directly, or raises TableNotFoundError
        return models.RandomItemResponse(table_name=table_name, item=item)
    except TableNotFoundError:
        raise HTTPException(status_code=404, detail=f"Random table '{table_name}' not found.")
    except Exception as e:
        # Catch-all for other unexpected errors
        print(f"Error getting random item from table '{table_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve item from table '{table_name}' due to an internal error.")

@router.get("/features", response_model=FeaturePromptListResponse, tags=["Utilities"])
async def list_feature_prompts():
    try:
        prompts = feature_prompt_service.get_all_prompts()
        # Prompts is already a list of dictionaries, convert them to FeaturePromptItem
        feature_items = [FeaturePromptItem(name=p['name'], template=p['template']) for p in prompts]
        return FeaturePromptListResponse(features=feature_items)
    except Exception as e:
        print(f"Error listing feature prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve list of feature prompts due to an internal error.")

@router.get("/features/{feature_name}", response_model=FeaturePromptItem, tags=["Utilities"])
async def get_feature_prompt(feature_name: str):
    try:
        prompt_template = feature_prompt_service.get_prompt(feature_name)
        if prompt_template is None:
            raise HTTPException(status_code=404, detail=f"Feature prompt '{feature_name}' not found.")
        # The service returns the template string directly. We need to wrap it in FeaturePromptItem.
        # The 'name' is the feature_name itself, and 'template' is the returned string.
        return FeaturePromptItem(name=feature_name, template=prompt_template)
    except HTTPException as http_exc: # Re-raise HTTPException to preserve status code
        raise http_exc
    except Exception as e:
        print(f"Error getting feature prompt '{feature_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feature prompt '{feature_name}' due to an internal error.")
