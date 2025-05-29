import google.generativeai as genai # type: ignore
from typing import List, Dict, Optional
from app.core.config import settings
from app.services.llm_service import AbstractLLMService # Updated import
from app.services.feature_prompt_service import FeaturePromptService
from pathlib import Path # For the __main__ block

class GeminiLLMService(AbstractLLMService): # Updated inheritance
    DEFAULT_MODEL = "gemini-pro" 

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.is_available(): # Use the new method
            raise ValueError("Gemini API key not configured or is a placeholder. Please set GEMINI_API_KEY in your .env file.")
        
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to configure Gemini client, possibly due to API key issue: {e}")

        self.feature_prompt_service = FeaturePromptService()

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "YOUR_GEMINI_API_KEY")

    def _get_model_instance(self, model_id: Optional[str] = None):
        # Helper to get a model instance.
        # model_id here is the direct model ID, e.g., "gemini-pro".
        # The factory handles provider prefixes.
        effective_model_id = model_id or self.DEFAULT_MODEL
        
        if not effective_model_id or not effective_model_id.strip():
            effective_model_id = self.DEFAULT_MODEL # Fallback to a default if empty/whitespace

        try:
            return genai.GenerativeModel(effective_model_id)
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini model '{effective_model_id}': {e}")

    def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        model_instance = self._get_model_instance(model)

        generation_config_params = {}
        if temperature is not None:
            generation_config_params["temperature"] = max(0.0, min(temperature, 1.0)) # Gemini typical range
        if max_tokens is not None:
            generation_config_params["max_output_tokens"] = max_tokens
        
        generation_config = genai.types.GenerationConfig(**generation_config_params) if generation_config_params else None

        try:
            response = model_instance.generate_content(prompt, generation_config=generation_config) if generation_config else model_instance.generate_content(prompt)
                
            if response.parts:
                return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text') and response.text:
                return response.text
            else:
                error_details = "Unknown reason for empty content."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    error_details = f"Prompt feedback: {response.prompt_feedback}"
                elif not response.candidates:
                    error_details = "No candidates returned in response."
                raise Exception(f"Gemini API call for generic text succeeded but returned no usable content. Model: {model_instance.model_name}. Details: {error_details}")
        except Exception as e:
            raise Exception(f"Failed to generate text with Gemini model {model_instance.model_name} due to API error ({type(e).__name__}): {str(e)}") from e

    def generate_campaign_concept(self, user_prompt: str, model: Optional[str] = None) -> str:
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(user_prompt=user_prompt)
        else:
            print(f"Warning: 'Campaign' prompt not found. Using default prompt for Gemini model {model_instance.model_name}.")
            final_prompt = f"Generate a detailed and engaging RPG campaign concept based on this idea: {user_prompt}. Include potential plot hooks, key NPCs, and unique settings."
        
        try:
            response = model_instance.generate_content(final_prompt)
            if response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text') and response.text:
                 return response.text
            else: 
                 raise Exception(f"Gemini API call (model: {model_instance.model_name}) succeeded but returned no usable content.")
        except Exception as e:
            print(f"Gemini API error (model: {model_instance.model_name}) during campaign concept generation: {e}")
            raise Exception(f"Failed to generate campaign concept with {model_instance.model_name} due to API error: {str(e)}") from e

    def generate_toc(self, campaign_concept: str, model: Optional[str] = None) -> str:
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Table of Contents")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept)
        else:
            print(f"Warning: 'Table of Contents' prompt not found. Using default prompt for Gemini model {model_instance.model_name}.")
            final_prompt = f"""Based on the following RPG campaign concept, generate a hierarchical Table of Contents... (prompt text)""" # Truncated
        
        try:
            response = model_instance.generate_content(final_prompt)
            if response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text') and response.text:
                 return response.text
            else:
                 raise Exception(f"Gemini API call for TOC (model: {model_instance.model_name}) succeeded but returned no usable content.")
        except Exception as e:
            print(f"Gemini API error (model: {model_instance.model_name}) during TOC generation: {e}")
            raise Exception(f"Failed to generate TOC with {model_instance.model_name} due to API error: {str(e)}") from e

    def generate_titles(self, campaign_concept: str, count: int = 5, model: Optional[str] = None) -> List[str]:
        model_instance = self._get_model_instance(model)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count)
        else:
            print(f"Warning: 'Campaign Names' prompt not found. Using default prompt for Gemini model {model_instance.model_name}.")
            final_prompt = f"""Based on the following RPG campaign concept, generate {count} alternative campaign titles... (prompt text)""" # Truncated

        try:
            response = model_instance.generate_content(final_prompt)
            text_response = ""
            if response.parts:
                 text_response = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text') and response.text:
                 text_response = response.text
            else:
                 raise Exception(f"Gemini API call for titles (model: {model_instance.model_name}) succeeded but returned no usable content.")

            titles = [title.strip() for title in text_response.split('\n') if title.strip()]
            return titles[:count]
        except Exception as e:
            print(f"Gemini API error (model: {model_instance.model_name}) during title generation: {e}")
            raise Exception(f"Failed to generate titles with {model_instance.model_name} due to API error: {str(e)}") from e

    def generate_section_content(self, campaign_concept: str, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: Optional[str] = None) -> str:
        model_instance = self._get_model_instance(model)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=section_creation_prompt or "Continue the story logically.",
                section_title_suggestion=section_title_suggestion or "Untitled Section"
            )
        else:
            print(f"Warning: 'Section Content' prompt not found. Using default prompt for Gemini model {model_instance.model_name}.")
            prompt_parts = ["You are writing a new section for a tabletop role-playing game campaign." , f"The overall campaign concept is:\n{campaign_concept}\n"] # Truncated
            # ... (rest of default prompt construction)
            final_prompt = "\n".join(prompt_parts)
        
        try:
            response = model_instance.generate_content(final_prompt)
            if response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text') and response.text:
                 return response.text
            else:
                 raise Exception(f"Gemini API call for section content (model: {model_instance.model_name}) succeeded but returned no usable content.")
        except Exception as e:
            print(f"Gemini API error (model: {model_instance.model_name}) during section content generation: {e}")
            raise Exception(f"Failed to generate section content with {model_instance.model_name} due to API error: {str(e)}") from e

    def list_available_models(self) -> List[Dict[str, str]]:
        """
        Lists available Gemini models.
        The 'id' in the returned dict is the model ID usable in generation methods (e.g., "gemini-pro").
        It attempts to list models from the API and falls back to a hardcoded list.
        """
        if not self.is_available():
            print("Warning: Gemini API key not configured. Cannot dynamically fetch models.")
            # Fallback to a minimal hardcoded list if API key isn't set for genai.list_models()
            return [
                {"id": "gemini-pro", "name": "Gemini Pro (Fallback)"},
                {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro (Fallback)"},
            ]

        available_models = []
        try:
            print("Fetching available models from Gemini API...")
            for m in genai.list_models():
                # We are interested in models that support 'generateContent' for text generation
                if 'generateContent' in m.supported_generation_methods:
                    # The model name from API is typically like "models/gemini-pro". We need "gemini-pro".
                    model_id = m.name.split('/')[-1] if '/' in m.name else m.name
                    available_models.append({"id": model_id, "name": m.display_name})
            
            if not available_models: # If API returned empty list for some reason
                 print("Warning: Gemini API returned no models supporting 'generateContent'. Using hardcoded list.")
                 raise Exception("No models found from API") # Fall through to except block for hardcoded list
        except Exception as e:
            print(f"Could not dynamically fetch models from Gemini API: {e}. Using a hardcoded list.")
            # Fallback to a hardcoded list if API call fails or returns no suitable models
            available_models = [
                {"id": "gemini-pro", "name": "Gemini Pro"},
                {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro"},
                {"id": "gemini-pro-vision", "name": "Gemini Pro Vision (Multimodal)"}, # Example, might not be suitable for all text tasks
                # Models like 'text-bison-001' (PaLM) might be listed by older API versions or different endpoints
                # For `genai.GenerativeModel`, we need models compatible with it.
            ]
        
        # Ensure default model is in the list, if not add it.
        default_model_id = self.DEFAULT_MODEL
        if not any(m['id'] == default_model_id for m in available_models):
            available_models.insert(0, {"id": default_model_id, "name": default_model_id.replace("-", " ").title() + " (Default)"})
            
        return available_models


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
