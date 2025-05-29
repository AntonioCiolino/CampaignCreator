from typing import Optional
from app.services.llm_service import LLMService
from app.services.openai_service import OpenAILLMService
from app.services.gemini_service import GeminiLLMService
from app.core.config import settings # To check if API keys are set

class LLMServiceUnavailableError(Exception):
    """Custom exception for when an LLM service cannot be initialized or is unavailable."""
    pass

def get_llm_service(model_id: Optional[str]) -> LLMService:
    """
    Factory function to get an instance of an LLMService based on the model_id prefix.
    model_id should be in the format "provider/model_name", e.g., "openai/gpt-3.5-turbo" or "gemini/gemini-pro".
    If no model_id is provided, or no prefix, defaults to OpenAI.
    """
    provider = "openai" # Default provider
    
    if model_id and "/" in model_id:
        provider, _ = model_id.split("/", 1) # Extract provider from "provider/model_name"
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "YOUR_API_KEY_HERE":
            raise LLMServiceUnavailableError("OpenAI API key is not configured. Cannot use OpenAI models.")
        try:
            return OpenAILLMService()
        except ValueError as e: # Catch init errors from the service (e.g. API key invalid format)
             raise LLMServiceUnavailableError(f"Failed to initialize OpenAI service: {e}")

    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise LLMServiceUnavailableError("Gemini API key is not configured. Cannot use Gemini models.")
        try:
            return GeminiLLMService()
        except ValueError as e: # Catch init errors from the service
            raise LLMServiceUnavailableError(f"Failed to initialize Gemini service: {e}")
            
    else:
        # Fallback or raise error if provider is unknown and no default is desired
        # For now, defaulting to OpenAI if prefix is unrecognized but OpenAI key exists
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "YOUR_API_KEY_HERE":
            print(f"Warning: Unknown LLM provider prefix in model_id '{model_id}'. Defaulting to OpenAI.")
            try:
                return OpenAILLMService()
            except ValueError as e:
                raise LLMServiceUnavailableError(f"Failed to initialize default OpenAI service: {e}")
        else:
            raise LLMServiceUnavailableError(f"Unsupported LLM provider or no API key for default (OpenAI) in model_id: {model_id}")

# Example of how this might be used if a global default model is desired:
# DEFAULT_MODEL_ID = "openai/gpt-3.5-turbo-instruct" # Could be configured elsewhere

# def get_default_llm_service() -> LLMService:
#     return get_llm_service(DEFAULT_MODEL_ID)
