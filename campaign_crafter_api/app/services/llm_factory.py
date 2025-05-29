from typing import Optional, Type, Dict
from app.services.llm_service import AbstractLLMService
from app.services.openai_service import OpenAILLMService
from app.services.gemini_service import GeminiLLMService
from app.services.llama_service import LlamaLLMService 
from app.services.deepseek_service import DeepSeekLLMService
from app.services.local_llm_service import LocalLLMService # New import
from app.core.config import settings

class LLMServiceUnavailableError(Exception):
    """Custom exception for when an LLM service cannot be initialized or is unavailable."""
    pass

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
        # if not await service_instance.is_available(): # This would require get_llm_service to be async
        #     raise LLMServiceUnavailableError(f"Service '{selected_provider}' reported as unavailable after instantiation.")
        return service_instance
    except ValueError as e: 
        raise LLMServiceUnavailableError(f"Failed to initialize {selected_provider} service: {e}")
    except Exception as e: 
        raise LLMServiceUnavailableError(f"An unexpected error occurred while initializing {selected_provider} service ({type(e).__name__}): {e}")
