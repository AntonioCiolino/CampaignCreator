from typing import Optional, Type, Dict
from app.services.llm_service import AbstractLLMService
from app.services.openai_service import OpenAILLMService
from app.services.gemini_service import GeminiLLMService
from app.services.llama_service import LlamaLLMService # Uncommented
from app.services.deepseek_service import DeepSeekLLMService # Uncommented
from app.core.config import settings

class LLMServiceUnavailableError(Exception):
    """Custom exception for when an LLM service cannot be initialized or is unavailable."""
    pass

_llm_service_providers: Dict[str, Type[AbstractLLMService]] = {
    "openai": OpenAILLMService,
    "gemini": GeminiLLMService,
    "llama": LlamaLLMService, # Added
    "deepseek": DeepSeekLLMService, # Added
}

def get_llm_service(
    provider_name: Optional[str] = None, 
    model_id_with_prefix: Optional[str] = None
) -> AbstractLLMService:
    """
    Factory function to get an instance of an AbstractLLMService.

    Args:
        provider_name (Optional[str]): The name of the LLM provider (e.g., "openai", "gemini", "llama", "deepseek").
                                       Case-insensitive.
        model_id_with_prefix (Optional[str]): The full model identifier, e.g., "openai/gpt-3.5-turbo".
                                             If provider_name is None, this is used to infer the provider.
                                             The part after the '/' is the model_id for the service itself.

    Returns:
        AbstractLLMService: An instance of the requested LLM service.

    Raises:
        LLMServiceUnavailableError: If the provider is not supported, or if the service
                                    cannot be initialized (e.g., missing or placeholder API key).
    """
    selected_provider: Optional[str] = None

    if provider_name:
        selected_provider = provider_name.lower()
    elif model_id_with_prefix and "/" in model_id_with_prefix:
        selected_provider, _ = model_id_with_prefix.split("/", 1)
        selected_provider = selected_provider.lower()
        print(f"Inferred provider '{selected_provider}' from model_id_with_prefix '{model_id_with_prefix}'.")
    else:
        # Try to default if no provider information given
        # Prioritize by common usage or configuration preference
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            selected_provider = "openai"
            print(f"Warning: No LLM provider specified or inferable. Defaulting to '{selected_provider}' due to available API key.")
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ["YOUR_GEMINI_API_KEY"]:
            selected_provider = "gemini"
            print(f"Warning: No LLM provider specified or inferable, and OpenAI key missing/placeholder. Defaulting to '{selected_provider}' due to available API key.")
        elif settings.LLAMA_API_KEY and settings.LLAMA_API_KEY not in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]: # Check Llama
            selected_provider = "llama"
            print(f"Warning: No LLM provider specified or inferable, and OpenAI/Gemini keys missing/placeholder. Defaulting to '{selected_provider}' due to available API key.")
        elif settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]: # Check DeepSeek
            selected_provider = "deepseek"
            print(f"Warning: No LLM provider specified or inferable, and OpenAI/Gemini/Llama keys missing/placeholder. Defaulting to '{selected_provider}' due to available API key.")
        else:
            raise LLMServiceUnavailableError(
                "LLM provider name must be specified or inferable. "
                "No default provider (OpenAI, Gemini, Llama, DeepSeek) seems to be configured with a valid API key."
            )

    if not selected_provider: 
        raise LLMServiceUnavailableError("Could not determine LLM provider.")
        
    service_class = _llm_service_providers.get(selected_provider)

    if not service_class:
        raise LLMServiceUnavailableError(f"Unsupported or unknown LLM provider: {selected_provider}")

    # Check for API key availability and validity for the selected provider BEFORE instantiation attempt
    if selected_provider == "openai":
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            raise LLMServiceUnavailableError("OpenAI API key is not configured or is a placeholder. Cannot use OpenAI models.")
    elif selected_provider == "gemini":
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY": # Check for placeholder
            raise LLMServiceUnavailableError("Gemini API key is not configured or is a placeholder. Cannot use Gemini models.")
    elif selected_provider == "llama":
        # Llama might need a key and potentially a URL, service's is_available() will handle specifics.
        # Factory ensures the key is at least present and not a placeholder.
        if not settings.LLAMA_API_KEY or settings.LLAMA_API_KEY in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]:
            raise LLMServiceUnavailableError("Llama API key is not configured or is a placeholder.")
        # Optionally, check for LLAMA_API_URL if it's strictly required by all Llama setups the factory might support.
        # if not settings.LLAMA_API_URL or settings.LLAMA_API_URL == "YOUR_LLAMA_API_URL":
        #     raise LLMServiceUnavailableError("Llama API URL is not configured or is a placeholder.")
    elif selected_provider == "deepseek":
        if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
            raise LLMServiceUnavailableError("DeepSeek API key is not configured or is a placeholder.")

    try:
        service_instance = service_class() 
        if not service_instance.is_available(): # Double check with service's own logic
            raise LLMServiceUnavailableError(
                f"Service '{selected_provider}' reported as unavailable after instantiation. "
                "This might be due to missing secondary configurations (e.g., API URL) or other internal checks failing."
            )
        return service_instance
    except ValueError as e: 
        raise LLMServiceUnavailableError(f"Failed to initialize {selected_provider} service: {e}")
    except Exception as e: 
        raise LLMServiceUnavailableError(f"An unexpected error occurred while initializing {selected_provider} service ({type(e).__name__}): {e}")

# Example usage:
# service = get_llm_service(provider_name="openai")
# models = service.list_available_models()
# if models:
#   text = service.generate_text("Hello world", model=models[0]['id'])

# service_by_model_id = get_llm_service(model_id_with_prefix="gemini/gemini-pro")
# text = service_by_model_id.generate_text("This is a test for Gemini")
