from typing import Optional, Type, Dict, List
from sqlalchemy.orm import Session
from app.models import ModelInfo, User as UserModel
from app.services.llm_service import AbstractLLMService
from app.services.openai_service import OpenAILLMService
from app import orm_models # For type hinting current_user_orm
from app import crud # To fetch orm_user from current_user Pydantic model
from app.core.security import decrypt_key # To decrypt user's API keys
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
    db: Session,
    current_user_orm: Optional[orm_models.User], # Pass the ORM user model
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
        # Default provider selection logic based on system settings if no specific request.
        # This part might need adjustment if user-specific default is desired.
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            selected_provider = "openai"
        elif settings.LOCAL_LLM_API_BASE_URL and settings.LOCAL_LLM_API_BASE_URL.strip():
            selected_provider = local_provider_key
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ["YOUR_GEMINI_API_KEY"]:
            selected_provider = "gemini"
        elif settings.LLAMA_API_KEY and settings.LLAMA_API_KEY not in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]:
            selected_provider = "llama"
        elif settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
            selected_provider = "deepseek"
        else:
            raise LLMServiceUnavailableError(
                "LLM provider name must be specified or inferable. No default system provider seems to be configured."
            )
        print(f"Warning: No LLM provider specified or directly inferable. Defaulting to system provider '{selected_provider}'.")

    if not selected_provider: 
        raise LLMServiceUnavailableError("Could not determine LLM provider.")
        
    if selected_provider == local_provider_key and local_provider_key not in _llm_service_providers:
        _llm_service_providers[local_provider_key] = LocalLLMService
        
    service_class = _llm_service_providers.get(selected_provider)

    if not service_class:
        raise LLMServiceUnavailableError(f"Unsupported or unknown LLM provider: {selected_provider}")

    user_specific_api_key: Optional[str] = None
    if current_user_orm:
        encrypted_key_to_use: Optional[str] = None
        if selected_provider == "openai":
            encrypted_key_to_use = current_user_orm.encrypted_openai_api_key
        elif selected_provider == "gemini":
            encrypted_key_to_use = current_user_orm.encrypted_gemini_api_key
        # Placeholder for 'other_llm_api_key' logic:
        # elif selected_provider == "some_other_provider_mapped_to_other_llm":
        #     encrypted_key_to_use = current_user_orm.encrypted_other_llm_api_key

        if encrypted_key_to_use:
            decrypted_key = decrypt_key(encrypted_key_to_use)
            if decrypted_key:
                user_specific_api_key = decrypted_key
            else:
                print(f"Warning: Failed to decrypt API key for user {current_user_orm.id} and provider {selected_provider}.")

    try:
        # Instantiate the service with the (potentially None) user_specific_api_key
        service_instance = service_class(api_key=user_specific_api_key)
        # The service's __init__ now handles API key logic (user vs system fallback) and client setup.
        # No need for direct API key/URL availability checks here anymore.
        return service_instance
    except ValueError as e: 
        # ValueError might be raised by service __init__ (e.g., LocalLLMService if URL is missing)
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
