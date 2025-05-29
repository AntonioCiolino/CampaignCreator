from typing import List, Dict
from fastapi import APIRouter, HTTPException
from app import models as pydantic_models # Renamed to avoid confusion with service model dicts
from app.services.llm_factory import get_llm_service, _llm_service_providers, LLMServiceUnavailableError
from app.core.config import settings # For direct key checks if needed, though factory handles it

router = APIRouter()

@router.get("/models", response_model=pydantic_models.ModelListResponse, tags=["LLM Management"])
async def list_llm_models():
    """
    Lists all available LLM models from all configured and available providers.
    The model IDs returned are prefixed with their provider (e.g., "openai/gpt-3.5-turbo")
    and can be used in other API endpoints that accept a 'model_id_with_prefix'.
    """
    all_provider_models: List[pydantic_models.ModelInfo] = []
    
    # Iterate through all registered providers in the factory
    for provider_name in _llm_service_providers.keys():
        try:
            print(f"Attempting to list models for provider: {provider_name}")
            # Get the service instance for the current provider
            # No specific model_id_with_prefix is needed here, just the provider_name
            service_instance = get_llm_service(provider_name=provider_name)
            
            # Get models from the service. These are provider-specific IDs.
            # Example: {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
            provider_specific_models: List[Dict[str, str]] = service_instance.list_available_models()
            
            for model_data in provider_specific_models:
                # Construct the full model_id_with_prefix for client use
                # The service's list_available_models() should return IDs specific to that provider.
                # The factory expects "provider_name/model_specific_id".
                # Some services (like old OpenAI/Gemini) might already return prefixed IDs.
                # The new AbstractLLMService contract is that list_available_models returns provider-specific IDs.
                
                model_specific_id = model_data.get("id")
                model_name = model_data.get("name")

                if not model_specific_id or not model_name:
                    print(f"Warning: Skipping model with missing id or name from provider {provider_name}: {model_data}")
                    continue

                # Ensure the ID is correctly prefixed for use with the factory in other endpoints
                if "/" not in model_specific_id: # If not already prefixed by the service
                    full_id_for_factory = f"{provider_name}/{model_specific_id}"
                else: # If service already prefixed it (e.g. older versions of services did this)
                    # We should ensure it matches the current provider to avoid mis-prefixed IDs.
                    prefix, actual_id = model_specific_id.split("/",1)
                    if prefix.lower() == provider_name.lower():
                         full_id_for_factory = model_specific_id
                    else:
                         # This case indicates a misbehaving service or old format.
                         # For robustness, we'll re-prefix with the current provider.
                         print(f"Warning: Model ID '{model_specific_id}' from provider '{provider_name}' has an unexpected prefix '{prefix}'. Re-prefixing.")
                         full_id_for_factory = f"{provider_name}/{actual_id}"


                all_provider_models.append(
                    pydantic_models.ModelInfo(id=full_id_for_factory, name=model_name)
                )
            print(f"Successfully listed {len(provider_specific_models)} models for provider: {provider_name}")

        except LLMServiceUnavailableError as e:
            print(f"Warning: Service for provider '{provider_name}' is unavailable: {e}. Models from this provider will not be listed.")
        except NotImplementedError:
            print(f"Warning: Provider '{provider_name}' has list_available_models not implemented. Models from this provider will not be listed.")
        except Exception as e:
            # Catch any other unexpected errors during service interaction
            print(f"Warning: An unexpected error occurred while retrieving models from provider '{provider_name}': {type(e).__name__} - {e}. Models from this provider will not be listed.")
    
    # Remove duplicates by full ID (e.g. "openai/gpt-3.5-turbo")
    final_model_list: List[pydantic_models.ModelInfo] = []
    seen_full_ids = set()
    for model_info in all_provider_models:
        if model_info.id not in seen_full_ids:
            final_model_list.append(model_info)
            seen_full_ids.add(model_info.id)
            
    if not final_model_list:
        print("Warning: No LLM models available from any configured and operational provider.")
        # It's valid to return an empty list if no providers are configured or working.
        # Consider if an HTTPException should be raised if absolutely no models can be found
        # and the application expects at least one. For now, empty list is fine.
    
    return pydantic_models.ModelListResponse(models=final_model_list)

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
