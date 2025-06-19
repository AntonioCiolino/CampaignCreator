import logging # Added logging
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

logger = logging.getLogger(__name__) # Added logger

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
    current_user_orm: Optional[orm_models.User],
    provider_name: Optional[str] = None,
    model_id_with_prefix: Optional[str] = None,
    campaign: Optional[orm_models.Campaign] = None  # New parameter
) -> AbstractLLMService:
    """
    Factory function to get an instance of an AbstractLLMService.
    """
    # Inside get_llm_service function
    selected_provider: Optional[str] = None
    source_of_selection_message: str = "unknown"

    # Priority 1: Explicit provider_name from arguments (implies it was extracted from request's model_id_with_prefix by caller)
    if provider_name:
        selected_provider = provider_name.lower()
        source_of_selection_message = f"explicitly specified provider_name='{selected_provider}' (from request's model_id_with_prefix='{model_id_with_prefix}')"

    # Priority 2: model_id_with_prefix from arguments (if it contains a provider and provider_name was not derived by caller)
    elif model_id_with_prefix and "/" in model_id_with_prefix:
        inferred_provider, _ = model_id_with_prefix.split("/", 1)
        selected_provider = inferred_provider.lower()
        source_of_selection_message = f"request's model_id_with_prefix='{model_id_with_prefix}'"

    # Priority 3: Campaign's selected_llm_id
    elif campaign and campaign.selected_llm_id and "/" in campaign.selected_llm_id:
        inferred_provider, _ = campaign.selected_llm_id.split("/", 1)
        selected_provider = inferred_provider.lower()
        source_of_selection_message = f"campaign (ID: {campaign.id}) setting: '{campaign.selected_llm_id}'"

    # Priority 4: User's preferred_llm_id (if exists on orm_models.User)
    elif current_user_orm and hasattr(current_user_orm, 'preferred_llm_id'):
        user_pref_llm_id = getattr(current_user_orm, 'preferred_llm_id', None)
        if user_pref_llm_id and "/" in user_pref_llm_id:
            inferred_provider, _ = user_pref_llm_id.split("/", 1)
            selected_provider = inferred_provider.lower()
            source_of_selection_message = f"user (ID: {current_user_orm.id}) preference: '{user_pref_llm_id}'"

    # Priority 5: System fallback
    else:
        local_provider_key = settings.LOCAL_LLM_PROVIDER_NAME.lower() if settings.LOCAL_LLM_PROVIDER_NAME else "local_llm"
        # Determine selected_provider based on system settings
        temp_selected_provider: Optional[str] = None # Temporary variable for this block
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            temp_selected_provider = "openai"
        elif settings.LOCAL_LLM_API_BASE_URL and settings.LOCAL_LLM_API_BASE_URL.strip():
            temp_selected_provider = local_provider_key
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ["YOUR_GEMINI_API_KEY"]:
            temp_selected_provider = "gemini"
        elif settings.LLAMA_API_KEY and settings.LLAMA_API_KEY not in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]:
            temp_selected_provider = "llama"
        elif settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
            temp_selected_provider = "deepseek"

        if not temp_selected_provider: # Check if any system default was found
            logger.error("LLM provider could not be determined from any source, including system defaults.")
            raise LLMServiceUnavailableError(
                "LLM provider could not be determined. Please configure a provider or specify one in the request, campaign, or user settings."
            )

        selected_provider = temp_selected_provider # Assign to the main variable
        source_of_selection_message = f"system configuration fallback (chose '{selected_provider}')"
        logger.warning(f"LLM provider selection defaulted to system config: Chose '{selected_provider}' because no provider was specified in request, campaign, or user settings.")

    if not selected_provider: 
        logger.critical("Fatal: selected_provider is None after selection logic. This should not happen if fallback has defaults.")
        raise LLMServiceUnavailableError("Fatal: Could not determine LLM provider.")

    logger.info(f"LLM Service: Attempting to use provider '{selected_provider}' (selected based on: {source_of_selection_message}).")

    local_provider_key_for_check = settings.LOCAL_LLM_PROVIDER_NAME.lower() if settings.LOCAL_LLM_PROVIDER_NAME else "local_llm"
    if selected_provider == local_provider_key_for_check and local_provider_key_for_check not in _llm_service_providers:
        _llm_service_providers[local_provider_key_for_check] = LocalLLMService

    service_class = _llm_service_providers.get(selected_provider)

    if not service_class:
        logger.error(f"Unsupported or unknown LLM provider after selection: {selected_provider}")
        raise LLMServiceUnavailableError(f"Unsupported or unknown LLM provider: {selected_provider}")

    user_specific_api_key: Optional[str] = None # Moved definition here
    if current_user_orm:
        encrypted_key_to_use: Optional[str] = None
        if selected_provider == "openai":
            if hasattr(current_user_orm, 'encrypted_openai_api_key'):
                encrypted_key_to_use = current_user_orm.encrypted_openai_api_key
        elif selected_provider == "gemini":
            if hasattr(current_user_orm, 'encrypted_gemini_api_key'):
                encrypted_key_to_use = current_user_orm.encrypted_gemini_api_key
        elif selected_provider == "llama":
            if hasattr(current_user_orm, 'encrypted_llama_api_key'):
                encrypted_key_to_use = current_user_orm.encrypted_llama_api_key
        elif selected_provider == "deepseek":
            if hasattr(current_user_orm, 'encrypted_deepseek_api_key'):
                encrypted_key_to_use = current_user_orm.encrypted_deepseek_api_key

        if encrypted_key_to_use:
            try:
                decrypted_key = decrypt_key(encrypted_key_to_use)
                if decrypted_key:
                    user_specific_api_key = decrypted_key
                else:
                    logger.warning(f"Failed to decrypt API key for user {current_user_orm.id} and provider {selected_provider} (key was empty after decryption).")
            except Exception as e_decrypt:
                    logger.error(f"Error decrypting API key for user {current_user_orm.id}, provider {selected_provider}: {e_decrypt}")

    try:
        service_instance = service_class(api_key=user_specific_api_key)
        return service_instance
    except ValueError as e: 
        logger.error(f"ValueError during {selected_provider} service initialization: {e}")
        raise LLMServiceUnavailableError(f"Failed to initialize {selected_provider} service: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during {selected_provider} service initialization ({type(e).__name__}): {e}")
        raise LLMServiceUnavailableError(f"An unexpected error occurred while initializing {selected_provider} service ({type(e).__name__}): {e}")

async def get_available_models_info(db: Session, current_user: UserModel) -> List[ModelInfo]: # Changed signature
    all_models_info: List[ModelInfo] = []
    # LLMServiceUnavailableError is used below, imported from llm_service
    # Iterate over a copy of keys in case the dictionary is modified elsewhere
    provider_names = list(_llm_service_providers.keys())

    if not current_user: # Should not happen if endpoint protects correctly
        raise LLMServiceUnavailableError("User context is required to list available models.")

    current_user_orm = crud.get_user(db, user_id=current_user.id)
    if not current_user_orm:
        # This means the user from the token exists in Pydantic form but not in DB via crud.get_user
        # This is a critical state inconsistency.
        raise LLMServiceUnavailableError(f"Could not retrieve ORM user for user ID {current_user.id}. Cannot determine API key context.")

    for provider_name in provider_names:
        service: Optional[AbstractLLMService] = None
        try:
            print(f"Attempting to get service and models for: {provider_name}")
            # get_llm_service itself checks for basic configuration (API keys/URL)
            # and raises LLMServiceUnavailableError if not configured.
            service = get_llm_service(db=db, current_user_orm=current_user_orm, provider_name=provider_name)

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
