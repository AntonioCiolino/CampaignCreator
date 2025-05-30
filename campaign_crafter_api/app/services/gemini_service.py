import google.generativeai as genai # type: ignore
from typing import List, Dict, Optional
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError # Import specific error
from app.services.feature_prompt_service import FeaturePromptService
# Removed import from llm_factory: from app.services.llm_factory import LLMServiceUnavailableError
from pathlib import Path # For the __main__ block
import asyncio # For testing async methods in __main__

class GeminiLLMService(AbstractLLMService):
    PROVIDER_NAME = "gemini" # Class variable for provider name
    DEFAULT_MODEL = "gemini-pro" 

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        # Removed self.is_available() call from __init__
        if not (self.api_key and self.api_key != "YOUR_GEMINI_API_KEY"):
            print("Warning: Gemini API key not configured or is a placeholder.")
            # Service will report as unavailable.
        
        try:
            # Configure should ideally happen once, but SDK might handle re-configuration.
            # If API key is missing, this might not raise an error immediately,
            # but subsequent calls will fail. is_available() will catch this.
            if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
                 genai.configure(api_key=self.api_key)
        except Exception as e:
            # This might catch issues if genai.configure fails immediately
            print(f"Error configuring Gemini client during __init__: {e}")
            # This doesn't prevent service instantiation but is_available should fail.

        self.feature_prompt_service = FeaturePromptService()

    async def is_available(self) -> bool:
        if not (self.api_key and self.api_key != "YOUR_GEMINI_API_KEY"):
            return False
        try:
            # Attempt to configure here again if not done, or if it needs to be per-instance
            # However, genai.configure is typically global.
            # A lightweight API call is better for checking availability.
            genai.configure(api_key=self.api_key) # Ensure configured for this check if not globally
            model_instance = self._get_model_instance(self.DEFAULT_MODEL) # Use a known default
            # Perform a very small, non-empty prompt generation
            await model_instance.generate_content_async(
                "test",
                generation_config=genai.types.GenerationConfig(candidate_count=1, max_output_tokens=1)
            )
            return True
        except Exception as e:
            print(f"Gemini service not available. API check failed: {e}")
            return False

    def _get_model_instance(self, model_id: Optional[str] = None):
        effective_model_id = model_id or self.DEFAULT_MODEL
        if not effective_model_id or not effective_model_id.strip():
            effective_model_id = self.DEFAULT_MODEL
        try:
            # This part remains synchronous as model instantiation itself is not async.
            return genai.GenerativeModel(effective_model_id)
        except Exception as e: # Broad catch, as various errors can occur here
            raise LLMServiceUnavailableError(f"Failed to initialize Gemini model '{effective_model_id}': {e}")


    async def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        if not await self.is_available():
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        model_instance = self._get_model_instance(model)

        generation_config_params = {}
        if temperature is not None:
            generation_config_params["temperature"] = max(0.0, min(temperature, 1.0))
        if max_tokens is not None:
            generation_config_params["max_output_tokens"] = max_tokens
        
        generation_config = genai.types.GenerationConfig(**generation_config_params) if generation_config_params else None

        try:
            response = await model_instance.generate_content_async(prompt, generation_config=generation_config) if generation_config else await model_instance.generate_content_async(prompt)
                
            if response.parts:
                return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text') and response.text: # Check for simple text response
                return response.text
            else: # Handle cases where response might be empty or malformed
                error_details = "Unknown reason for empty content."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    error_details = f"Prompt feedback: {response.prompt_feedback}"
                elif not response.candidates: # No candidates means no valid response.
                    error_details = "No candidates returned in response."
                raise LLMServiceUnavailableError(f"Gemini API call succeeded but returned no usable content. Model: {model_instance.model_name}. Details: {error_details}")
        except Exception as e: # Catch broader exceptions from the SDK or logic
            # Check if it's a Google specific API error if possible, otherwise generic
            # from google.api_core import exceptions as google_exceptions
            # if isinstance(e, google_exceptions.GoogleAPIError):
            print(f"Gemini API error (model: {model_instance.model_name}): {type(e).__name__} - {e}")
            raise LLMServiceUnavailableError(f"Failed to generate text with Gemini model {model_instance.model_name} due to API error: {str(e)}") from e
            # else:
            #     print(f"Unexpected error (model: {model_instance.model_name}): {type(e).__name__} - {e}")
            #     raise Exception(f"An unexpected error occurred: {str(e)}") from e


    async def generate_campaign_concept(self, user_prompt: str, model: Optional[str] = None) -> str:
        if not await self.is_available():
            raise LLMServiceUnavailableError("Gemini service is not available.")
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign")
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
                       f"Generate a detailed and engaging RPG campaign concept based on this idea: {user_prompt}. Include potential plot hooks, key NPCs, and unique settings."
        
        # Re-use generate_text for actual generation
        return await self.generate_text(prompt=final_prompt, model=model_instance.model_name, temperature=0.7, max_tokens=1000)


    async def generate_toc(self, campaign_concept: str, model: Optional[str] = None) -> str:
        if not await self.is_available():
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Table of Contents")
        final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept) if custom_prompt_template else \
                       f"Based on the following RPG campaign concept: '{campaign_concept}', generate a hierarchical Table of Contents suitable for an RPG campaign book. Include main chapters and potential sub-sections with brief descriptions for each."
        
        return await self.generate_text(prompt=final_prompt, model=model_instance.model_name, temperature=0.5, max_tokens=700)

    async def generate_titles(self, campaign_concept: str, count: int = 5, model: Optional[str] = None) -> List[str]:
        if not await self.is_available():
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")

        model_instance = self._get_model_instance(model)
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names")
        final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count) if custom_prompt_template else \
                       f"Based on the following RPG campaign concept: '{campaign_concept}', generate {count} alternative, catchy campaign titles. List each title on a new line. Ensure only the titles are listed, nothing else."

        text_response = await self.generate_text(prompt=final_prompt, model=model_instance.model_name, temperature=0.7, max_tokens=150 + (count * 20))
        titles = [title.strip() for title in text_response.split('\n') if title.strip()]
        return titles[:count]

    async def generate_section_content(self, campaign_concept: str, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: Optional[str] = None) -> str:
        if not await self.is_available():
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept: # Basic check
            raise ValueError("Campaign concept is required.")

        model_instance = self._get_model_instance(model)
        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content")

        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=section_creation_prompt or "Continue the story logically, introducing new elements or developing existing ones.",
                section_title_suggestion=section_title_suggestion or "Next Part"
            )
        else: # Simplified default
            final_prompt = f"Campaign Concept: {campaign_concept}\n"
            if existing_sections_summary:
                final_prompt += f"Summary of existing sections: {existing_sections_summary}\n"
            final_prompt += f"Instruction for new section (titled '{section_title_suggestion or 'Next Part'}'): {section_creation_prompt or 'Develop the next part of the campaign story.'}"
        
        return await self.generate_text(prompt=final_prompt, model=model_instance.model_name, temperature=0.7, max_tokens=1500)

    async def list_available_models(self) -> List[Dict[str, str]]:
        if not await self.is_available(): # Use async is_available
            print("Warning: Gemini API key not configured or service unavailable. Cannot fetch models.")
            return [
                {"id": "gemini-pro", "name": "Gemini Pro (Unavailable/Fallback)"},
                {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro (Unavailable/Fallback)"},
            ]

        available_models: List[Dict[str, str]] = []
        try:
            print("Fetching available models from Gemini API...")
            # genai.list_models() is synchronous.
            # For a truly non-blocking call in an async context, this would ideally be:
            # loop = asyncio.get_running_loop()
            # api_models = await loop.run_in_executor(None, genai.list_models)
            # For now, calling it directly as it's usually fast.
            api_models = genai.list_models()

            for m in api_models:
                if 'generateContent' in m.supported_generation_methods:
                    model_id = m.name.split('/')[-1] if '/' in m.name else m.name
                    available_models.append({"id": model_id, "name": m.display_name})
            
            if not available_models:
                 print("Warning: Gemini API returned no models supporting 'generateContent'. Using hardcoded list.")
                 raise Exception("No models found from API") # Fall through to hardcoded list
        except Exception as e:
            print(f"Could not dynamically fetch models from Gemini API: {e}. Using a hardcoded list as fallback.")
            available_models = [
                {"id": "gemini-pro", "name": "Gemini Pro"},
                {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro"},
                # {"id": "gemini-pro-vision", "name": "Gemini Pro Vision"}, # Keep it simple for now
            ]
        
        default_model_id = self.DEFAULT_MODEL
        if not any(m['id'] == default_model_id for m in available_models):
            available_models.insert(0, {"id": default_model_id, "name": default_model_id.replace("-", " ").title() + " (Default)"})
            
        return available_models

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # The google-generativeai library for Gemini (as of early 2024)
        # does not typically require explicit client closing for basic generate_content_async usage.
        # If it were using something like an httpx.AsyncClient internally that needs closing,
        # this is where it would be done. For now, it's a no-op.
        pass


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    # Load .env from the project root or monorepo root
    env_path_api_root = Path(__file__).resolve().parent.parent.parent / ".env"
    env_path_monorepo_root = Path(__file__).resolve().parent.parent.parent.parent / ".env"

    if env_path_api_root.exists():
        load_dotenv(dotenv_path=env_path_api_root)
    elif env_path_monorepo_root.exists():
        load_dotenv(dotenv_path=env_path_monorepo_root)
    else:
        print(f"Warning: .env file not found at {env_path_api_root} or {env_path_monorepo_root}. Service might not initialize correctly.")

    settings.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    settings.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY) 

    if not GeminiLLMService().is_available(): # Check availability using the instance method
        print("Skipping GeminiLLMService tests as GEMINI_API_KEY is not set or is a placeholder.")
    else:
        print(f"Attempting to initialize GeminiLLMService with key: ...{settings.GEMINI_API_KEY[-4:] if settings.GEMINI_API_KEY else 'None'}")
        try:
            gemini_service = GeminiLLMService()
            print("GeminiLLMService Initialized.")

            print("\nAvailable Gemini Models (IDs are for service methods):")
            models = gemini_service.list_available_models()
            for m in models:
                print(f"- {m['name']} (id: {m['id']})")

            if models:
                # Pick a model for testing - prefer non-default if available and different
                test_model_id_for_service = gemini_service.DEFAULT_MODEL
                if len(models) > 1:
                    # Try to pick a different model from default for one test, if available
                    alt_models = [m['id'] for m in models if m['id'] != gemini_service.DEFAULT_MODEL]
                    if alt_models:
                        test_model_id_for_service = alt_models[0]
                
                print(f"\nUsing model ID: '{test_model_id_for_service}' for generation tests...")

                print("\n--- Testing Generic Text Generation ---")
                try:
                    generic_text = gemini_service.generate_text(
                        prompt=f"Tell me a short story about a robot learning to paint. Use model {test_model_id_for_service}.", 
                        model=test_model_id_for_service, 
                        temperature=0.8, 
                        max_tokens=200
                    )
                    print("Generic Text Output (first 250 chars):", generic_text[:250] + "..." if generic_text else "No generic text generated.")
                except Exception as e:
                    print(f"Error during generic text generation test: {e}")

                print(f"\n--- Testing Campaign Concept Generation (using default model: {gemini_service.DEFAULT_MODEL}) ---")
                try:
                    concept = gemini_service.generate_campaign_concept("A city powered by captured dreams.") # Uses default model
                    print("Concept Output (first 150 chars):", concept[:150] + "..." if concept else "No concept generated.")

                    if concept:
                        print(f"\n--- Testing TOC Generation (using model: {test_model_id_for_service}) ---")
                        toc = gemini_service.generate_toc(concept, model=test_model_id_for_service)
                        print("TOC Output (first 150 chars):", toc[:150] + "..." if toc else "No TOC generated.")

                        print(f"\n--- Testing Titles Generation (using default model: {gemini_service.DEFAULT_MODEL}) ---")
                        titles = gemini_service.generate_titles(concept, count=3) # Uses default model
                        print("Titles Output:", titles)

                        print(f"\n--- Testing Section Content Generation (using model: {test_model_id_for_service}) ---")
                        section_content = gemini_service.generate_section_content(
                            campaign_concept=concept,
                            existing_sections_summary="Chapter 1: The Dream Weavers. Chapter 2: The Nightmare Market.",
                            section_creation_prompt="A character discovers a way to enter the dreamscape physically.",
                            section_title_suggestion="Chapter 3: Lucid Reality",
                            model=test_model_id_for_service
                        )
                        print("Section Content Output (first 150 chars):", section_content[:150] + "..." if section_content else "No section content generated.")
                except Exception as e:
                     print(f"Error during campaign feature tests: {e}")
            else:
                print("No Gemini models listed by the service, skipping generation tests.")

        except ValueError as ve:
            print(f"Error initializing or using GeminiLLMService: {ve}")
        except Exception as e:
            print(f"An unexpected error occurred during GeminiLLMService testing: {e}")
