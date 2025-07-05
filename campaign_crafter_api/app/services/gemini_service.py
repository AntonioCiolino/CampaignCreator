import google.generativeai as genai # type: ignore
import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app import models, orm_models
from app.models import User as UserModel
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
    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
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

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> List[Dict[str, str]]:
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

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> List[str]:
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
        db_campaign: orm_models.Campaign, # Changed from campaign_concept, added db_campaign type
        db: Session,
        current_user: UserModel,
        existing_sections_summary: Optional[str],
        section_creation_prompt: Optional[str],
        section_title_suggestion: Optional[str],
        model: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")

        campaign_concept = db_campaign.concept # Get concept from db_campaign
        if not campaign_concept:
            # Fallback if concept is somehow empty, though db_campaign should have it
            campaign_concept = "A new creative piece."
            # Or raise ValueError("Campaign concept is required and missing from db_campaign.")

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

        # --- Character Information Injection ---
        character_info_parts = []
        if db_campaign.characters:
            for char in db_campaign.characters:
                char_details = f"Character Name: {char.name}"
                if char.description:
                    char_details += f"\n  Description: {char.description}"
                if char.notes_for_llm:
                    char_details += f"\n  LLM Notes: {char.notes_for_llm}"
                character_info_parts.append(char_details)

        campaign_characters_formatted = "This campaign has no explicitly defined characters yet."
        if character_info_parts:
            campaign_characters_formatted = "The following characters are part of this campaign:\n" + "\n\n".join(character_info_parts)
        # --- End Character Information Injection ---

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content", db=db)
        final_prompt_for_generation: str

        if custom_prompt_template:
            try:
                final_prompt_for_generation = custom_prompt_template.format(
                    campaign_concept=campaign_concept,
                    existing_sections_summary=existing_sections_summary or "N/A",
                    section_creation_prompt=effective_section_prompt,
                    section_title_suggestion=section_title_suggestion or "Next Part",
                    campaign_characters=campaign_characters_formatted # Add new parameter
                )
            except KeyError as e:
                print(f"Warning: Prompt template 'Section Content' is missing a key: {e}. Falling back to default prompt structure. Please update the template to include 'campaign_characters'.")
                # Fallback structure if template is old and doesn't have campaign_characters
                final_prompt_for_generation = (
                    f"Campaign Concept: {campaign_concept}\n"
                    f"Relevant Characters in this Campaign:\n{campaign_characters_formatted}\n\n"
                    f"Summary of existing sections: {existing_sections_summary or 'N/A'}\n"
                    f"Instruction for new section (titled '{section_title_suggestion or 'Next Part'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"
                )
        else: # Simplified default if no template found at all
            final_prompt_for_generation = (
                f"Campaign Concept: {campaign_concept}\n"
                f"Relevant Characters in this Campaign:\n{campaign_characters_formatted}\n\n"
            )
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
        model_instance = self._get_model_instance(model_id=model or "gemini-pro-vision")

        try:
            # The structure of the API call for text-to-image generation needs to be confirmed.
            # This is a conceptual implementation based on typical Gemini API patterns.
            # We assume generate_content_async can produce images and the response format.
            # Specific generation_config might be needed for image output, e.g., mime_type.
            # genai.types.GenerationConfig(..., output_mime_type="image/png")

            # Placeholder for actual API call parameters.
            # The Gemini API for image generation might expect a different content structure or specific parameters.
            # For example, some APIs might require a specific prompt format or configuration.
            print(f"Attempting to generate image with model: {model_instance.model_name} using prompt: '{prompt[:50]}...'")

            response = await model_instance.generate_content_async(
                prompt
                # generation_config=genai.types.GenerationConfig(
                #     # Example: request PNG image if API supports mime_type specification
                #     # This is speculative and depends on actual API features.
                #     # response_mime_type="image/png"
                # )
            )

            # Process the response to extract image bytes.
            # This assumes the image data is in response.parts[0].inline_data.data.
            # The actual structure might differ for image generation models.
            if response.parts and response.parts[0].inline_data and response.parts[0].inline_data.data:
                image_bytes = response.parts[0].inline_data.data
                # mime_type = response.parts[0].inline_data.mime_type # Could be useful
                return image_bytes
            else:
                # Log details if the response is not as expected.
                error_message = "Gemini API call for image generation succeeded but returned no image data."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    error_message += f" Prompt feedback: {response.prompt_feedback}"
                if not response.candidates:
                     error_message += " No candidates were generated."
                # You might want to log the full response here for debugging if it's small enough
                # print(f"Unexpected response structure from Gemini image generation: {response}")
                raise LLMGenerationError(error_message)

        except LLMGenerationError: # Re-raise if it's already our specific error
            raise
        except LLMServiceUnavailableError: # Re-raise
            raise
        except Exception as e:
            # Handle potential errors from the API call (e.g., network issues, API errors)
            # This could include errors if the model doesn't support image generation or the prompt is invalid.
            # from google.api_core import exceptions as google_exceptions
            # if isinstance(e, google_exceptions.InvalidArgument):
            #     raise LLMGenerationError(f"Invalid prompt or parameters for Gemini image generation (model: {model_instance.model_name}): {e}")
            print(f"Error during Gemini image generation (model: {model_instance.model_name}): {type(e).__name__} - {e}")
            raise LLMGenerationError(f"Failed to generate image with Gemini model {model_instance.model_name}: {e}") from e

    async def generate_character_response(
        self,
        character_name: str,
        character_notes: str,
        user_prompt: str,
        current_user: UserModel,
        db: Session,
        chat_history: Optional[List[models.ChatMessage]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 300
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not user_prompt:
            raise ValueError("User prompt cannot be empty for character response.")

        model_instance = self._get_model_instance(model)

        truncated_notes = (character_notes[:1000] + '...') if character_notes and len(character_notes) > 1000 else character_notes

        # Gemini typically uses a direct instruction format rather than a separate system prompt for some models/use-cases.
        # We will construct a detailed prompt that includes the character's persona.
        # The prompt structure might need adjustment based on Gemini's best practices for role-playing.
        # Example:
        # "You are acting as the character '{character_name}'.
        #  Your persona: '{character_notes}'.
        #  Now, respond to the following as '{character_name}':
        #  User's message: '{user_prompt}'
        #  Your response:"

        # For Gemini, it's often better to structure the prompt directly.
        # The 'system' role is not as distinctly used as in OpenAI for chat models via `generate_content_async`'s direct string input.
        # Instead, instructions are part of the main prompt or through specific multi-turn chat setup.

        effective_temperature = temperature if temperature is not None else 0.75
        effective_max_tokens = max_tokens or 300

        generation_config_params = {}
        if effective_temperature is not None:
            generation_config_params["temperature"] = max(0.0, min(effective_temperature, 1.0)) # Gemini temp is 0.0-1.0
        if effective_max_tokens is not None:
            generation_config_params["max_output_tokens"] = effective_max_tokens

        final_generation_config = genai.types.GenerationConfig(**generation_config_params) if generation_config_params else None

        if chat_history:
            # Construct messages for multi-turn chat
            # Gemini's chat history typically starts with a user message setting context, then model, then user, etc.
            # The "system prompt" or character notes needs to be integrated into this flow.
            # One way is to make the character notes part of the first user message to the model.
            # Or, if the model supports a "system" like instruction at the beginning of `contents`.
            # For `genai.GenerativeModel.start_chat(history=...)`, history is `Content` objects.
            # `genai.GenerativeModel.generate_content_async(contents=...)` is more direct here.

            contents = []
            # Initial context setting for the character
            # This can be a "user" turn that the "model" (character) implicitly understands as its persona.
            initial_context = (
                f"You are embodying the character named '{character_name}'. "
                f"Your personality, background, and way of speaking are defined by the following notes: "
                f"'{truncated_notes if truncated_notes else 'A typically neutral character.'}' "
                f"Respond naturally as this character would. Do not break character. Do not mention that you are an AI. "
                f"The conversation starts now."
            )
            # For Gemini, this initial instruction might be better as the first 'user' part of a two-part initial history,
            # or as a general instruction before the user's actual first turn if the API supports a "system" role
            # more directly in the `contents` list (which it does via a specific format if using ChatSession).
            # Simpler for direct `generate_content_async`: prepend to history or make it the first user turn.

            # Let's try to prepend the system-like message as the first user turn.
            # If the model supports it, a system prompt can be passed differently.
            # For now, we integrate it into the user/model turns.

            # Option 1: Prepend character notes as a system instruction (if model understands this role in `contents`)
            # contents.append({"role": "system", "parts": [{"text": initial_context}]}) # This role is not standard for contents list, it's user/model

            # Option 2: More common for Gemini: start with user setting the context
            # The first "user" message can be the character instructions.
            # The model's first response would then be "Okay, I understand my role." (implicitly or explicitly if prompted for).
            # Then the actual chat history begins. This is a bit complex for direct generation.

            # Option 3: (Chosen) Build a history where the persona is an instruction, then replay chat.
            # The `system_message` is implicitly handled by the `full_prompt` structure when not using chat_history.
            # When using chat_history, we must ensure the persona is established.
            # We'll build the `contents` list for `generate_content_async`.
            # The `initial_context` acts as a hidden preamble/instruction.

            contents.append({"role": "user", "parts": [{"text": initial_context}]})
            # Gemini expects the next message to be from the model if we provide the above as 'user'
            contents.append({"role": "model", "parts": [{"text": f"Understood. I am {character_name}. I will respond according to these instructions."}]})


            for message in chat_history:
                role = "user" if message.speaker.lower() == "user" else "model"
                contents.append({"role": role, "parts": [{"text": message.text}]})

            # Add the current user prompt
            contents.append({"role": "user", "parts": [{"text": user_prompt}]})

            try:
                response = await model_instance.generate_content_async(contents, generation_config=final_generation_config)
                if response.parts:
                    return "".join(part.text for part in response.parts if hasattr(part, 'text'))
                elif hasattr(response, 'text') and response.text:
                    return response.text
                else:
                    raise LLMGenerationError(f"Gemini API call (character response with history) succeeded but returned no usable content. Model: {model_instance.model_name}")
            except Exception as e:
                print(f"Gemini API error (character response with history, model: {model_instance.model_name}): {type(e).__name__} - {e}")
                raise LLMGenerationError(f"Failed to generate character response with Gemini (history) model {model_instance.model_name}: {str(e)}") from e

        else:
            # Original logic if no chat_history
            full_prompt = (
                f"**Instructions for AI:**\n"
                f"You are to embody and respond as the character named **{character_name}**.\n"
                f"**Character Persona & Background:**\n{truncated_notes if truncated_notes else 'This character has a generally neutral and adaptable persona.'}\n\n"
                f"**Your Task:**\n"
                f"Respond to the following user message *in the voice and personality of {character_name}*. "
                f"Do not break character. Do not mention that you are an AI or a language model.\n\n"
                f"**User's Message to {character_name}:**\n{user_prompt}\n\n"
                f"**{character_name}'s Response:**"
            )
            return await self.generate_text(
                prompt=full_prompt,
                current_user=current_user,
                db=db,
                model=model_instance.model_name,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens
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
