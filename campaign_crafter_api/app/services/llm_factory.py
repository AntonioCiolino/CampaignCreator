from typing import Optional, Type, Dict, List
from sqlalchemy.orm import Session # Added Session
from app.models import ModelInfo, User as UserModel # Added UserModel
from app.services.llm_service import AbstractLLMService
from app.services.openai_service import OpenAILLMService
from app.services.gemini_service import GeminiLLMService
from app.services.llama_service import LlamaLLMService 
from app.services.deepseek_service import DeepSeekLLMService
from app.services.local_llm_service import LocalLLMService # New import
from app.core.config import settings
from app.services.llm_service import LLMServiceUnavailableError # Added import

# Updated mapping of provider names to service classes
_llm_service_providers: Dict[str, Type[AbstractLLMService]] = {
    "openai": OpenAILLMService,
    "gemini": GeminiLLMService,
    "llama": LlamaLLMService, 
    "deepseek": DeepSeekLLMService,
    # The key for LocalLLMService will be dynamically set from settings
    # settings.LOCAL_LLM_PROVIDER_NAME: LocalLLMService, # This needs to be added after settings are loaded
}
# Dynamically add LocalLLMService based on settings to handle customizable provider name
if settings.LOCAL_LLM_PROVIDER_NAME:
    _llm_service_providers[settings.LOCAL_LLM_PROVIDER_NAME.lower()] = LocalLLMService


def get_llm_service(
    provider_name: Optional[str] = None, 
    model_id_with_prefix: Optional[str] = None
) -> AbstractLLMService:
    """
    Factory function to get an instance of an AbstractLLMService.
    """
    selected_provider: Optional[str] = None
    local_provider_key = settings.LOCAL_LLM_PROVIDER_NAME.lower() if settings.LOCAL_LLM_PROVIDER_NAME else "local_llm"


    if provider_name:
        selected_provider = provider_name.lower()
    elif model_id_with_prefix and "/" in model_id_with_prefix:
        selected_provider, _ = model_id_with_prefix.split("/", 1)
        selected_provider = selected_provider.lower()
        print(f"Inferred provider '{selected_provider}' from model_id_with_prefix '{model_id_with_prefix}'.")
    else:
        # Default provider selection logic
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            selected_provider = "openai"
        elif settings.LOCAL_LLM_API_BASE_URL and settings.LOCAL_LLM_API_BASE_URL.strip(): # Check local LLM next
            selected_provider = local_provider_key
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ["YOUR_GEMINI_API_KEY"]:
            selected_provider = "gemini"
        elif settings.LLAMA_API_KEY and settings.LLAMA_API_KEY not in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]:
            selected_provider = "llama"
        elif settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
            selected_provider = "deepseek"
        else:
            raise LLMServiceUnavailableError(
                "LLM provider name must be specified or inferable. No default provider seems to be configured with a valid API key/URL."
            )
        print(f"Warning: No LLM provider specified or directly inferable. Defaulting to '{selected_provider}'.")


    if not selected_provider: 
        raise LLMServiceUnavailableError("Could not determine LLM provider.")
        
    # Ensure the dynamic local_provider_key is in the map if it was selected
    if selected_provider == local_provider_key and local_provider_key not in _llm_service_providers:
        _llm_service_providers[local_provider_key] = LocalLLMService
        
    service_class = _llm_service_providers.get(selected_provider)

    if not service_class:
        raise LLMServiceUnavailableError(f"Unsupported or unknown LLM provider: {selected_provider}")

    # API key/URL availability checks
    if selected_provider == "openai":
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            raise LLMServiceUnavailableError("OpenAI API key is not configured or is a placeholder.")
    elif selected_provider == "gemini":
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            raise LLMServiceUnavailableError("Gemini API key is not configured or is a placeholder.")
    elif selected_provider == "llama":
        if not settings.LLAMA_API_KEY or settings.LLAMA_API_KEY in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]:
            raise LLMServiceUnavailableError("Llama API key is not configured or is a placeholder.")
    elif selected_provider == "deepseek":
        if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
            raise LLMServiceUnavailableError("DeepSeek API key is not configured or is a placeholder.")
    elif selected_provider == local_provider_key: # Use the dynamic key from settings
        if not settings.LOCAL_LLM_API_BASE_URL or not settings.LOCAL_LLM_API_BASE_URL.strip():
            raise LLMServiceUnavailableError(f"{settings.LOCAL_LLM_PROVIDER_NAME.title()} API Base URL is not configured.")
    
    try:
        service_instance = service_class() 
        # The service's __init__ or an async is_available() should handle internal checks.
        # For services that need async initialization for is_available (like LocalLLMService),
        # this factory cannot easily await it. The service should try to be operational
        # on instantiation if possible, or the check in the endpoint/dependency is more critical.
        # For now, we rely on the service's own __init__ checks for immediate configuration errors.
        # The `service_instance.is_available()` check here would be problematic if it's async.
        # We will remove the direct call to `is_available()` from here and let service constructor
        # or an async dependency wrapper handle availability.
        # if not await service_instance.is_available(current_user=current_user, db=db): # This would require get_llm_service to be async and take user/db
        #     raise LLMServiceUnavailableError(f"Service '{selected_provider}' reported as unavailable after instantiation.")
        return service_instance
    except ValueError as e: 
        raise LLMServiceUnavailableError(f"Failed to initialize {selected_provider} service: {e}")
    except Exception as e: 
        raise LLMServiceUnavailableError(f"An unexpected error occurred while initializing {selected_provider} service ({type(e).__name__}): {e}")

async def get_available_models_info(db: Session, current_user: UserModel) -> List[ModelInfo]: # Changed signature
    all_models_info: List[ModelInfo] = []
    # LLMServiceUnavailableError is used below, imported from llm_service
    # Iterate over a copy of keys in case the dictionary is modified elsewhere
    provider_names = list(_llm_service_providers.keys())

    for provider_name in provider_names:
        service: Optional[AbstractLLMService] = None
        try:
            print(f"Attempting to get service and models for: {provider_name}")
            # get_llm_service itself checks for basic configuration (API keys/URL)
            # and raises LLMServiceUnavailableError if not configured.
            service = get_llm_service(provider_name)

            # Pass current_user and db to is_available
            if not await service.is_available(current_user=current_user, db=db):
                print(f"Service '{provider_name}' is not available for user {current_user.id}.")
                continue

            # Pass current_user and db to list_available_models
            service_models = await service.list_available_models(current_user=current_user, db=db)
            if not service_models:
                print(f"No models listed by service '{provider_name}' for user {current_user.id}.")
                continue

            for model_dict in service_models:
                # Ensure model_dict has 'id' and 'name' as list_available_models should provide
                original_model_id = model_dict.get("id")
                model_name = model_dict.get("name", original_model_id) # Fallback name to id

                if not original_model_id:
                    print(f"Warning: Model from '{provider_name}' missing 'id': {model_dict}")
                    continue

                prefixed_id = f"{provider_name}/{original_model_id}"
                # Use PROVIDER_NAME for a more descriptive name if desired, or just model_name
                # For consistency with how models might be displayed, let's use the name from the service.
                # The prefixed_id already contains the provider context.
                all_models_info.append(
                    ModelInfo(
                        id=prefixed_id,
                        name=model_name if model_name else prefixed_id,
                        model_type=model_dict.get("model_type", "unknown"), # Get the new field
                        supports_temperature=model_dict.get("supports_temperature", True), # Get the new field
                        capabilities=model_dict.get("capabilities", []) # Ensure this is also handled
                    )
                )
            print(f"Successfully processed models for {provider_name}")

        except LLMServiceUnavailableError as e:
            print(f"Service '{provider_name}' is unavailable or misconfigured: {e}")
        except Exception as e:
            print(f"Failed to get models from provider '{provider_name}': {type(e).__name__} - {e}")
        finally:
            if service and hasattr(service, 'close') and callable(service.close):
                try:
                    await service.close() # Ensure async close is awaited
                except Exception as e:
                    print(f"Error closing service client for '{provider_name}': {e}")

    return all_models_info
