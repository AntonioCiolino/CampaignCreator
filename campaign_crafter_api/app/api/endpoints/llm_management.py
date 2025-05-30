from typing import List, Dict # Dict might not be needed anymore if list_llm_models is simplified
from fastapi import APIRouter, HTTPException
from app import models as pydantic_models # Renamed to avoid confusion with service model dicts
from app.services.llm_factory import get_llm_service, get_available_models_info, LLMServiceUnavailableError # Added get_available_models_info
from app.core.config import settings # For direct key checks if needed, though factory handles it

router = APIRouter()

@router.get("/models", response_model=pydantic_models.ModelListResponse, tags=["LLM Management"])
async def list_llm_models():
    """
    Lists all available LLM models from all configured and available providers.
    The model IDs returned are prefixed with their provider (e.g., "openai/gpt-3.5-turbo")
    and can be used in other API endpoints that accept a 'model_id_with_prefix'.
    """
    try:
        available_models_info: List[pydantic_models.ModelInfo] = await get_available_models_info()

        if not available_models_info:
            print("Warning: No LLM models available from any configured and operational provider for the /models endpoint.")
            
        return pydantic_models.ModelListResponse(models=available_models_info)
    except Exception as e:
        print(f"Critical error in list_llm_models endpoint calling get_available_models_info: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve list of LLM models due to an internal server error.")

@router.post("/generate-text", response_model=pydantic_models.LLMTextGenerationResponse, tags=["LLM Management"])
async def generate_text_endpoint(request: pydantic_models.LLMGenerationRequest):
    """
    Generates text using the specified LLM provider and model.
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    provider_name: Optional[str] = None
    model_specific_id: Optional[str] = None # Model ID for the service, without prefix

    if request.model_id_with_prefix:
        if "/" not in request.model_id_with_prefix:
            # This means either it's a direct provider name, or a model_id for a default provider.
            # Or it's a model_id for a provider that needs to be explicitly named or defaulted.
            # For simplicity, we will assume if no prefix, it's a model ID for the default provider.
            # The factory's default logic will handle this.
            print(f"Warning: model_id_with_prefix '{request.model_id_with_prefix}' has no prefix. Factory will attempt default provider.")
            model_specific_id = request.model_id_with_prefix 
            # provider_name will be determined by factory's default logic
        else:
            try:
                provider_name, model_specific_id = request.model_id_with_prefix.split("/", 1)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid model_id_with_prefix format. Expected 'provider/model_name'.")
    else:
        # No model_id_with_prefix provided, factory will use its default provider logic
        # model_specific_id will remain None, so service will use its internal default model
        pass 
        

    try:
        # Get the service instance. provider_name can be None here if we want factory to infer/default.
        # model_id_with_prefix is passed to help factory infer if provider_name is None.
        llm_service = get_llm_service(provider_name=provider_name, model_id_with_prefix=request.model_id_with_prefix)
        
        # The model_specific_id (without prefix) is passed to the service's generate_text method.
        # If model_specific_id is None here (e.g. only provider was given, or nothing was given),
        # the service's generate_text method will use its own default model.
        generated_text = llm_service.generate_text(
            prompt=request.prompt,
            model=model_specific_id, # This is the ID for the service, e.g., "gpt-3.5-turbo"
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return pydantic_models.LLMTextGenerationResponse(
            text=generated_text,
            model_used=request.model_id_with_prefix or f"{llm_service.PROVIDER_NAME}/{model_specific_id or 'default'}" # Best guess of model used
        )
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM Service Error: {e}")
    except NotImplementedError:
        raise HTTPException(status_code=501, detail=f"The generation function for the selected LLM provider or model is not implemented.")
    except ValueError as e: # Catch other value errors, e.g. from service validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for other unexpected errors from the LLM service
        print(f"Unexpected error during text generation: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while generating text.")

# Ensure Pydantic models are defined for the new endpoint
# In app/models/llm_models.py (or similar):
# class LLMTextGenerationRequest(BaseModel):
#     prompt: str
#     model_id_with_prefix: Optional[str] = None # e.g., "openai/gpt-3.5-turbo"
#     temperature: float = 0.7
#     max_tokens: int = 500

# class LLMTextGenerationResponse(BaseModel):
#     text: str
#     model_used: Optional[str] = None
#
# And ModelInfo, ModelListResponse should already exist.
# class ModelInfo(BaseModel):
#     id: str
#     name: str
#
# class ModelListResponse(BaseModel):
#     models: List[ModelInfo]
