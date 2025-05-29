from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session # Though not directly used in this endpoint, good for consistency if other endpoints need DB

from app import models # Pydantic models
from app.services.openai_service import OpenAILLMService
from app.services.gemini_service import GeminiLLMService
from app.core.config import settings # To check if keys are set

router = APIRouter()

@router.get("/models", response_model=models.ModelListResponse, tags=["LLM Management"])
async def list_llm_models():
    all_models: List[models.ModelInfo] = []

    # Try to get OpenAI models
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "YOUR_API_KEY_HERE":
        try:
            openai_service = OpenAILLMService()
            openai_models_data = openai_service.list_available_models() # This should return List[Dict[str, str]]
            for model_data in openai_models_data:
                 # Ensure IDs are prefixed for the factory if not already by the service.
                 # OpenAILLMService's list_available_models already prefixes with "openai/"
                all_models.append(models.ModelInfo(id=model_data.get("id"), name=model_data.get("name")))
        except ValueError as ve: # Catch init errors from OpenAILLMService
            print(f"Warning: Could not retrieve OpenAI models, API key might be invalid or service init failed: {ve}")
        except Exception as e:
            print(f"Warning: An error occurred while retrieving OpenAI models: {e}")
    else:
        print("Warning: OpenAI API key not configured. OpenAI models will not be listed.")

    # Try to get Gemini models
    if settings.GEMINI_API_KEY:
        try:
            gemini_service = GeminiLLMService()
            gemini_models_data = gemini_service.list_available_models() # This should return List[Dict[str, str]]
            for model_data in gemini_models_data:
                # Ensure IDs are prefixed for the factory.
                # GeminiLLMService's list_available_models already prefixes with "gemini/"
                all_models.append(models.ModelInfo(id=model_data.get("id"), name=model_data.get("name")))
        except ValueError as ve: # Catch init errors from GeminiLLMService
            print(f"Warning: Could not retrieve Gemini models, API key might be invalid or service init failed: {ve}")
        except Exception as e:
            print(f"Warning: An error occurred while retrieving Gemini models: {e}")
    else:
        print("Warning: Gemini API key not configured. Gemini models will not be listed.")
    
    # Remove duplicates by ID if any service lists a generic ID that another also lists (unlikely with prefixes)
    # Or if a model is somehow listed by both (e.g. a common base model ID without prefix)
    final_model_list = []
    seen_ids = set()
    for model_info in all_models:
        if model_info.id not in seen_ids:
            final_model_list.append(model_info)
            seen_ids.add(model_info.id)
            
    if not final_model_list:
        # This will now only happen if both API keys are missing or both services fail to list any models.
        # No need to raise HTTPException, an empty list is valid.
        print("Warning: No LLM models available from any configured provider.")
    
    return models.ModelListResponse(models=final_model_list)
