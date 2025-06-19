import google.generativeai as genai # type: ignore
import re # Added import
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app.models import User as UserModel # Added UserModel import
# Removed import from llm_factory: from app.services.llm_factory import LLMServiceUnavailableError
from pathlib import Path # For the __main__ block
import asyncio # For testing async methods in __main__
class GeminiLLMService(AbstractLLMService):
    PROVIDER_NAME = "gemini" # Class variable for provider name
    DEFAULT_MODEL = "gemini-1.5-flash"
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.effective_api_key = self.api_key # Key from constructor (user-provided)
        if not self.effective_api_key:
            self.effective_api_key = settings.GEMINI_API_KEY # Fallback to system key

        self.configured_successfully = False
        if self.effective_api_key and self.effective_api_key != "YOUR_GEMINI_API_KEY":
            try:
                genai.configure(api_key=self.effective_api_key)
                self.configured_successfully = True
            except Exception as e:
                print(f"Error configuring Gemini client during __init__ with effective_api_key: {e}")
                # self.configured_successfully remains False
        else:
            print("Warning: Gemini API key (user or system) not configured or is a placeholder.")
        
        self.feature_prompt_service = FeaturePromptService()

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        if not self.configured_successfully:
            return False
        try:
            # genai should already be configured from __init__
            model_instance = self._get_model_instance(self.DEFAULT_MODEL)
            await model_instance.generate_content_async(
                "test",
                generation_config=genai.types.GenerationConfig(candidate_count=1, max_output_tokens=1)
            )
            return True
        except Exception as e:
            print(f"Gemini service not available. API check failed (using effective_api_key): {e}")
            # This might indicate the key, though configured, is invalid or has quota issues.
            return False
    def _get_model_instance(self, model_id: Optional[str] = None): # No changes here, internal helper
        effective_model_id = model_id or self.DEFAULT_MODEL
        if not effective_model_id or not effective_model_id.strip():
            effective_model_id = self.DEFAULT_MODEL
        try:
            # This part remains synchronous as model instantiation itself is not async.
            return genai.GenerativeModel(effective_model_id)
        except Exception as e: # Broad catch, as various errors can occur here
            raise LLMServiceUnavailableError(f"Failed to initialize Gemini model '{effective_model_id}': {e}")
   
    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str: # Added _current_user, db
        if not await self.is_available(current_user=current_user, db=db): # Pass args
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
    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
                       f"Generate a detailed and engaging RPG campaign concept based on this idea: {user_prompt}. Include potential plot hooks, key NPCs, and unique settings."
        
        # Re-use generate_text for actual generation, passing current_user and db
        return await self.generate_text(prompt=final_prompt, current_user=current_user, db=db, model=model_instance.model_name, temperature=0.7, max_tokens=1000)

    def _parse_toc_string_with_types(self, raw_toc_string: str) -> List[Dict[str, str]]:
        parsed_toc_items = []
        regex = r"^\s*-\s*(.+?)\s*\[Type:\s*([^\]]+?)\s*\]\s*$"
        fallback_regex = r"^\s*-\s*(.+)"
        known_types = ["monster", "character", "npc", "location", "item", "quest", "chapter", "note", "world_detail", "generic", "unknown"]

        for line in raw_toc_string.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(regex, line, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                type_str = match.group(2).strip().lower()
                if type_str not in known_types:
                    print(f"Warning: Unknown type '{type_str}' found for title '{title}'. Defaulting to 'unknown'.")
                    type_str = "unknown"
                parsed_toc_items.append({"title": title, "type": type_str})
            else:
                fallback_match = re.match(fallback_regex, line)
                if fallback_match:
                    title = fallback_match.group(1).strip()
                    title = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", title).strip()
                    if title:
                         parsed_toc_items.append({"title": title, "type": "unknown"})
        return parsed_toc_items

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> List[Dict[str, str]]: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        
        model_instance = self._get_model_instance(model) # Determine model instance once

        # Fetch Display TOC prompt
        display_prompt_template_str = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template_str:
            raise LLMGenerationError("Display TOC prompt template ('TOC Display') not found in database for Gemini.")
        
        try:
            display_final_prompt = display_prompt_template_str.format(campaign_concept=campaign_concept)
        except KeyError:
            print(f"ERROR: Gemini formatting 'TOC Display' prompt failed due to KeyError. Prompt: '{display_prompt_template_str}' Concept: '{campaign_concept}'")
            raise LLMGenerationError("Failed to format 'TOC Display' prompt due to unexpected placeholders for Gemini.")

        raw_toc_string = await self.generate_text(
            prompt=display_final_prompt,
            current_user=current_user, db=db, # Pass args
            model=model_instance.model_name,
            temperature=0.5,
            max_tokens=700
        )
        if not raw_toc_string:
             raise LLMGenerationError(f"Gemini API call for Display TOC (model: {model_instance.model_name}) succeeded but returned no usable content.")

        return self._parse_toc_string_with_types(raw_toc_string)

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> List[str]: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")
        model_instance = self._get_model_instance(model)
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names", db=db)
        final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count) if custom_prompt_template else \
                       f"Based on the following RPG campaign concept: '{campaign_concept}', generate {count} alternative, catchy campaign titles. List each title on a new line. Ensure only the titles are listed, nothing else."
        text_response = await self.generate_text(prompt=final_prompt, current_user=current_user, db=db, model=model_instance.model_name, temperature=0.7, max_tokens=150 + (count * 20)) # Pass args
        titles = [title.strip() for title in text_response.split('\n') if title.strip()]
        return titles[:count]
    async def generate_section_content(
        self,
        campaign_concept: str,
        db: Session,
        current_user: UserModel, # Added current_user
        existing_sections_summary: Optional[str],
        section_creation_prompt: Optional[str],
        section_title_suggestion: Optional[str],
        model: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept is required.")
        model_instance = self._get_model_instance(model)
        effective_section_prompt = section_creation_prompt
        type_based_instruction = ""
        if section_type and section_type.lower() not in ["generic", "unknown", "", None]:
            title_str = section_title_suggestion or "the current section"
            if section_type.lower() == "npc" or section_type.lower() == "character":
                type_based_instruction = f"This section is about an NPC or character named '{title_str}'. Generate a detailed description including appearance, personality, motivations, potential plot hooks, and if appropriate, a basic stat block suitable for a tabletop RPG."
            elif section_type.lower() == "location":
                type_based_instruction = f"This section describes a location: '{title_str}'. Detail its key features, atmosphere, inhabitants (if any), notable points of interest, secrets, and potential encounters."
            elif section_type.lower() == "chapter" or section_type.lower() == "quest":
                type_based_instruction = f"This section outlines a chapter or quest titled '{title_str}'. Describe the main events, objectives, challenges, potential rewards, and any key NPCs or locations involved."
            else: # Other specific types
                type_based_instruction = f"This section is specifically about '{title_str}' which is a '{section_type}'. Generate detailed content appropriate for this type."
        if not effective_section_prompt and type_based_instruction:
            effective_section_prompt = type_based_instruction
        elif effective_section_prompt and type_based_instruction:
            effective_section_prompt = f"{type_based_instruction}\n\nFurther specific instructions for this section: {section_creation_prompt}"
        elif not effective_section_prompt:
            effective_section_prompt = "Continue the story logically, introducing new elements or developing existing ones."
        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content", db=db)
        final_prompt_for_generation: str
        if custom_prompt_template:
            final_prompt_for_generation = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=effective_section_prompt, # Use the refined prompt
                section_title_suggestion=section_title_suggestion or "Next Part"
            )
        else: # Simplified default
            final_prompt_for_generation = f"Campaign Concept: {campaign_concept}\n"
            if existing_sections_summary:
                final_prompt_for_generation += f"Summary of existing sections: {existing_sections_summary}\n"
            final_prompt_for_generation += f"Instruction for new section (titled '{section_title_suggestion or 'Next Part'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"
        
        return await self.generate_text(prompt=final_prompt_for_generation, current_user=current_user, db=db, model=model_instance.model_name, temperature=0.7, max_tokens=4000)

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, any]]:
        if not await self.is_available(current_user=current_user, db=db):
            print("Warning: Gemini API key not configured or service unavailable. Cannot fetch models.")
            # Return a minimal list or an empty list, but ensure structure matches.
            fallback_models = [
                {"id": "gemini-pro", "name": "Gemini Pro (Unavailable/Fallback)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
                {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Unavailable/Fallback)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            ]
            return fallback_models

        available_models: List[Dict[str, any]] = []
        try:
            print("Fetching available models from Gemini API...")
            # genai.list_models() is synchronous.
            # Consider loop.run_in_executor for true async if this blocks significantly.
            api_models = genai.list_models()
            for m in api_models:
                # Filter for models that support 'generateContent' as a proxy for text/chat generation
                if 'generateContent' in m.supported_generation_methods:
                    model_id = m.name.split('/')[-1] if '/' in m.name else m.name

                    # Determine model_type and capabilities
                    model_type = "chat" # Default for Gemini generative models
                    supports_temperature = True # Gemini models generally support temperature
                    capabilities = ["chat"]

                    if "vision" in model_id.lower() or "vision" in m.display_name.lower():
                        capabilities.append("vision")
                        # Vision models are typically chat-based as well for multimodal interactions
                    
                    # Add to list
                    available_models.append({
                        "id": model_id,
                        "name": m.display_name,
                        "model_type": model_type,
                        "supports_temperature": supports_temperature,
                        "capabilities": capabilities
                    })

            if not available_models:
                print("Warning: Gemini API returned no models supporting 'generateContent'. Using hardcoded list as fallback.")
                raise Exception("No suitable models found from API") # Triggers fallback in except block

        except Exception as e:
            print(f"Could not dynamically fetch models from Gemini API: {e}. Using a hardcoded list as fallback.")
            # Ensure fallback list also includes the new fields
            available_models = [
                {"id": "gemini-1.5-pro-latest", "name": "Gemini 1.5 Pro (Latest)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"]},
                {"id": "gemini-1.5-flash-latest", "name": "Gemini 1.5 Flash (Latest)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"]},
                {"id": "gemini-pro", "name": "Gemini Pro (Legacy)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]}, # Older version, might phase out
                {"id": "gemini-pro-vision", "name": "Gemini Pro Vision (Legacy)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"]}, # Older version
            ]
            # Ensure default model is in the list if using fallback
            default_model_id = self.DEFAULT_MODEL # e.g., "gemini-1.5-flash"
            if not any(m['id'] == default_model_id for m in available_models):
                # Find if a variant of default (e.g. latest) is present, otherwise add it
                is_default_variant_present = any(default_model_id in m['id'] for m in available_models)
                if not is_default_variant_present:
                    available_models.insert(0, {
                        "id": default_model_id,
                        "name": default_model_id.replace("-", " ").title() + " (Default)",
                        "model_type": "chat",
                        "supports_temperature": True,
                        "capabilities": ["chat", "vision"] if "vision" in default_model_id else ["chat"]
                    })

        # Sort models to have a consistent order, e.g., by name or a preferred list
        available_models.sort(key=lambda x: (
            "latest" not in x["id"], # Put latest versions first
            "pro" not in x["id"],    # Then pro versions
            "flash" not in x["id"],  # Then flash versions
            x["name"]
        ))
        return available_models

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # The google-generativeai library for Gemini (as of early 2024)
        # does not typically require explicit client closing for basic generate_content_async usage.
        # If it were using something like an httpx.AsyncClient internally that needs closing,
        # this is where it would be done. For now, it's a no-op.
        pass

    async def generate_homebrewery_toc_from_sections(self, sections_summary:str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        if not sections_summary:
            return "{{toc,wide\n# Table Of Contents\n}}\n"

        model_instance = self._get_model_instance(model)

        prompt_template_str = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not prompt_template_str:
            raise LLMGenerationError("Homebrewery TOC prompt template ('TOC Homebrewery') not found in database for Gemini.")

        final_prompt = prompt_template_str.format(sections_summary=sections_summary)

        generated_toc = await self.generate_text(
            prompt=final_prompt,
            current_user=current_user,
            db=db,
            model=model_instance.model_name, # Use the determined model_name
            temperature=0.3, # Consistent with OpenAI
            max_tokens=1000    # Consistent with OpenAI
        )
        if not generated_toc:
            raise LLMGenerationError(f"Gemini API call for Homebrewery TOC from sections (model: {model_instance.model_name}) succeeded but returned no usable content.")

        return generated_toc

    async def generate_image(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = "gemini-pro-vision", size: Optional[str] = None) -> bytes:
        """
        Generates an image based on the given prompt using Gemini.
        Note: The 'size' parameter is conceptual as API capabilities for size need confirmation.
        The 'gemini-pro-vision' model is specified, but a dedicated image generation
        model might be more appropriate if available via the API.
        """
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        if not prompt:
            raise ValueError("Prompt cannot be empty for image generation.")

        # It's crucial that the chosen model supports image generation.
        # 'gemini-pro-vision' is primarily for understanding images.
        # This might need to be a specific image generation model (e.g., an Imagen model endpoint if accessible via Gemini SDK).
        # For now, we proceed with the specified model, assuming it might have some image generation capabilities or this is a placeholder.
        # model_instance = self._get_model_instance(model_id=model or "gemini-pro-vision")

        # Directly raise LLMGenerationError as text-to-image is not supported with this SDK configuration.
        raise LLMGenerationError(
            "Text-to-image generation with Gemini models is not currently supported with the configured SDK. "
            "The 'gemini-1.5-flash' and 'gemini-pro-vision' models are intended for multimodal understanding, "
            "not direct image generation through this service."
        )


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    # Synchronous setup should be outside main_test but inside if __name__ == '__main__'
    env_path_api_root = Path(__file__).resolve().parent.parent.parent / ".env"
    env_path_monorepo_root = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path_api_root.exists():
        load_dotenv(dotenv_path=env_path_api_root)
    elif env_path_monorepo_root.exists():
        load_dotenv(dotenv_path=env_path_monorepo_root)
    else:
        print(f"Warning: .env file not found at {env_path_api_root} or {env_path_monorepo_root}. Service might not initialize correctly.")

    # Use a placeholder current_user and db for service initialization and checks in main_test
    class DummyUser(UserModel):
        id: int = 1
        username: str = "testuser"
        # Add other fields if necessary, matching UserModel structure
        email: Optional[str] = "test@example.com"
        full_name: Optional[str] = "Test User"
        disabled: bool = False
        is_superuser: bool = False
        openai_api_key_provided: bool = False
        sd_api_key_provided: bool = False
        gemini_api_key_provided: bool = False
        other_llm_api_key_provided: bool = False
        # campaigns, llm_configs, roll_tables can be empty lists or None
        campaigns = []
        llm_configs = []
        roll_tables = []


    mock_user = DummyUser()
    mock_db_session: Optional[Session] = None


    async def main_test(): # Async function definition
        # Load environment variables for GEMINI_API_KEY specifically for the test
        # This allows testing both system key and constructor-injected key scenarios if desired
        system_gemini_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY) # settings.GEMINI_API_KEY might be already updated by load_dotenv
        settings.GEMINI_API_KEY = system_gemini_key # Ensure settings object has the key from .env for system fallback test

        # Test with system key first (or if no user key is provided)
        print(f"Attempting to initialize GeminiLLMService with system key: ...{system_gemini_key[-4:] if system_gemini_key and system_gemini_key != 'YOUR_GEMINI_API_KEY' else 'Not Set or Placeholder'}")
        gemini_service_system = GeminiLLMService() # Uses system key from settings if no key passed

        is_system_available = await gemini_service_system.is_available(current_user=mock_user, db=mock_db_session)
        if not is_system_available:
            print("Skipping GeminiLLMService tests as system GEMINI_API_KEY is not set, is a placeholder, or service is unavailable.")
            await gemini_service_system.close()
            return

        print("GeminiLLMService with system key is available.")
        # Optionally, run a quick test with the system key service instance
        # For example, list models:
        # models_list_system = await gemini_service_system.list_available_models(current_user=mock_user, db=mock_db_session)
        # print(f"Models available with system key: {[m['name'] for m in models_list_system[:2]]}") # Print first 2 model names

        # Now, to test with a constructor-injected key (if different or for specific test)
        # For this example, we'll just re-use the system_gemini_key as if it were user-provided
        # In a real test suite, you might have a separate test_user_api_key
        user_provided_key_for_test = system_gemini_key
        print(f"\nAttempting to initialize GeminiLLMService with a constructor-injected key: ...{user_provided_key_for_test[-4:] if user_provided_key_for_test and user_provided_key_for_test != 'YOUR_GEMINI_API_KEY' else 'Not Set or Placeholder'}")
        gemini_service = GeminiLLMService(api_key=user_provided_key_for_test) # Instance for further tests

        try:
            # The is_available check is crucial and now uses the logic from __init__
            if not await gemini_service.is_available(current_user=mock_user, db=mock_db_session):
                 print("GeminiLLMService with constructor-injected key is NOT available. Check key and configuration.")
                 await gemini_service.close()
                 await gemini_service_system.close() # Also close the system instance
                 return

            print("GeminiLLMService with constructor-injected key Initialized and Available for tests.")
            print("\nAvailable Gemini Models (IDs are for service methods):")
            models_list = await gemini_service.list_available_models(current_user=mock_user, db=mock_db_session) # Use a different variable name
            for m in models_list:
                print(f"- {m['name']} (id: {m['id']})")
            for m in models_list:
                print(f"- {m['name']} (id: {m['id']})")
            if models_list:
                test_model_id_for_service = gemini_service.DEFAULT_MODEL
                # Try to pick a different model if available for more robust testing
                alt_models = [m['id'] for m in models_list if m['id'] != gemini_service.DEFAULT_MODEL and "vision" not in m['id'].lower()] # Prefer non-vision for text tests
                if not alt_models: # If only vision models or only default, stick to default
                     alt_models = [m['id'] for m in models_list if m['id'] != gemini_service.DEFAULT_MODEL] # take any other model
                
                if alt_models:
                    test_model_id_for_service = alt_models[0]
                else: # Only one model in list, use it
                    test_model_id_for_service = models_list[0]['id']

                print(f"\nUsing model ID: '{test_model_id_for_service}' for generation tests...")

                print("\n--- Testing Generic Text Generation ---")
                try:
                    generic_text = await gemini_service.generate_text(
                        prompt=f"Tell me a short story about a robot learning to paint. Use model {test_model_id_for_service}.", 
                        current_user=mock_user, db=mock_db_session, # Pass mock_user and mock_db_session
                        model=test_model_id_for_service, 
                        temperature=0.8, 
                        max_tokens=200
                    )
                    print("Generic Text Output (first 250 chars):", generic_text[:250] + "..." if generic_text else "No generic text generated.")
                except Exception as e:
                    print(f"Error during generic text generation test: {e}")

                print(f"\n--- Testing Campaign Concept Generation (using default model: {gemini_service.DEFAULT_MODEL}) ---")
                try:
                    concept = await gemini_service.generate_campaign_concept("A city powered by captured dreams.", current_user=mock_user, db=mock_db_session) # Pass mock_user and mock_db_session
                    print("Concept Output (first 150 chars):", concept[:150] + "..." if concept else "No concept generated.")
                    if concept:
                        print(f"\n--- Testing TOC Generation (using model: {test_model_id_for_service}) ---")
                        toc_result = await gemini_service.generate_toc(concept, current_user=mock_user, db=mock_db_session, model=test_model_id_for_service) # Pass mock_user and mock_db_session
                        if toc_result:
                            print("Display TOC Output (first 150 chars):", toc_result.get("display_toc", "")[:150] + "...")
                            print("Homebrewery TOC Output (first 150 chars):", toc_result.get("homebrewery_toc", "")[:150] + "...")
                        else:
                            print("No TOC generated.")

                        print(f"\n--- Testing Titles Generation (using default model: {gemini_service.DEFAULT_MODEL}) ---")
                        titles = await gemini_service.generate_titles(concept, current_user=mock_user, db=mock_db_session, count=3) # Pass mock_user and mock_db_session
                        print("Titles Output:", titles)

                        print(f"\n--- Testing Section Content Generation (using model: {test_model_id_for_service}) ---")
                        section_content = await gemini_service.generate_section_content(
                            campaign_concept=concept,
                            current_user=mock_user, db=mock_db_session, # Pass mock_user and mock_db_session
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

        except ValueError as ve: # Catch specific errors if needed
            print(f"ValueError during GeminiLLMService testing: {ve}")
        except LLMServiceUnavailableError as llmsue: # Catch specific errors if needed
            print(f"LLMServiceUnavailableError during GeminiLLMService testing: {llmsue}")
        except Exception as e: # General catch-all
            print(f"An unexpected error occurred during GeminiLLMService testing: {e}")
        finally:
            if 'gemini_service' in locals() and gemini_service: await gemini_service.close()
            if 'gemini_service_system' in locals() and gemini_service_system: await gemini_service_system.close()

    asyncio.run(main_test())
