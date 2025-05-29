from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session # Not used here, but good practice for API modules

from app import models # Pydantic models
from app.services.random_table_service import RandomTableService, TableNotFoundError
# from app.db import get_db # Example if DB was needed for other utility endpoints

router = APIRouter()

# Instantiate the service. For a real application, you might use FastAPI's dependency injection
# for services, especially if they have dependencies like DB sessions or configurations.
# For this service, which just loads a file on init, direct instantiation is simple.
random_table_service = RandomTableService()

@router.get("/random-tables", response_model=models.TableNameListResponse, tags=["Utilities"])
async def list_random_table_names():
    try:
        table_names = random_table_service.get_available_table_names()
        return external_models.TableNameListResponse(table_names=table_names)
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
