from google import genai as new_genai # type: ignore
from google.generativeai import types as google_types # type: ignore # Assuming old types might still be needed for a bit, or map to new_genai.types
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

# Attempt to import new SDK errors, fall back or define if not available directly
try:
    from google.generativeai.types import BlockedPromptError as NewBlockedPromptError
    from google.generativeai.types import GenerativeAIError as NewGenerativeAIError
    # For specific API errors like AuthenticationError, PermissionDenied, etc.
    # these are usually under google.api_core.exceptions or similar,
    # but the new genai SDK might wrap them in new_genai.errors
    from google.api_core import exceptions as google_api_exceptions # For common API errors
    from google.auth import exceptions as google_auth_exceptions # For DefaultCredentialsError
except ImportError:
    # Define placeholder errors if new SDK doesn't have them named this way,
    # or rely on a general new_genai.errors.APIError
    class NewBlockedPromptError(Exception): pass
    class NewGenerativeAIError(Exception): pass
    # google_api_exceptions might still be valid for underlying transport errors
    from google.api_core import exceptions as google_api_exceptions


class GeminiLLMService(AbstractLLMService):
    DEFAULT_MODEL = "gemini-1.5-flash-latest" # Updated DEFAULT_MODEL

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.effective_api_key = self.api_key
        if not self.effective_api_key:
            self.effective_api_key = settings.GEMINI_API_KEY # System fallback for API key

        self.client: Optional[new_genai.Client] = None # Correct type hint for the new SDK client
        self.configured_successfully = False

        if settings.GOOGLE_GENAI_USE_VERTEXAI:
            # Vertex AI Path
            if settings.GOOGLE_CLOUD_PROJECT and settings.GOOGLE_CLOUD_LOCATION:
                try:
                    self.client = new_genai.Client(
                        vertexai=True, # Enable Vertex AI mode
                        project=settings.GOOGLE_CLOUD_PROJECT,
                        location=settings.GOOGLE_CLOUD_LOCATION
                        # For Vertex, API key is usually handled by Application Default Credentials (ADC)
                        # and not passed directly to new_genai.Client constructor if vertexai=True.
                        # If an API key is still needed for Vertex AI with this SDK, this might need adjustment.
                    )
                    self.configured_successfully = True
                    print("GeminiLLMService configured successfully for Vertex AI with new SDK client.")
                except Exception as e:
                    self.client = None
                    self.configured_successfully = False
                    print(f"Error configuring Gemini client for Vertex AI with new SDK: {e}")
            else:
                self.client = None
                self.configured_successfully = False
                print("Warning: GOOGLE_GENAI_USE_VERTEXAI is True, but GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_LOCATION is not set.")
        else:
            # Gemini API (API Key) Path
            if self.effective_api_key and self.effective_api_key != "YOUR_GEMINI_API_KEY" and self.effective_api_key.strip(): # Check for placeholder and empty
                try:
                    self.client = new_genai.Client(api_key=self.effective_api_key)
                    self.configured_successfully = True
                    print("GeminiLLMService configured successfully for Gemini API (API Key) with new SDK client.")
                except Exception as e:
                    self.client = None
                    self.configured_successfully = False
                    print(f"Error configuring Gemini client for Gemini API (API Key) with new SDK: {e}")
            else:
                self.client = None
                self.configured_successfully = False
                print("Warning: Gemini API key (user or system) not configured or is a placeholder. Cannot initialize Gemini API client for Gemini Developer API.")
        
        self.feature_prompt_service = FeaturePromptService()

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        if not self.configured_successfully or not self.client:
            return False
        try:
            # Use a lightweight API call to check availability, e.g., listing top 1 model
            # The new SDK uses self.client.models.list() or self.client.aio.models.list()
            await self.client.aio.models.list(config={'page_size': 1}) # Test with async client
            return True
        except google_auth_exceptions.DefaultCredentialsError as e: # Specific handler for ADC issues
            print(f"Gemini service not available due to DefaultCredentialsError (Vertex AI setup issue): {e}")
            # Re-raise as LLMServiceUnavailableError with a user-friendly message
            raise LLMServiceUnavailableError(
                "Authentication failed for Vertex AI. Application Default Credentials are not set up correctly. "
                "Please run 'gcloud auth application-default login' or ensure your environment is configured for ADC."
            ) from e
        except google_api_exceptions.PermissionDenied as e: # More specific error for auth issues
            print(f"Gemini service not available due to Permission Denied (API key issue?): {e}")
            return False
        except google_api_exceptions.Unauthenticated as e: # More specific error for auth issues
            print(f"Gemini service not available due to Unauthenticated (API key issue?): {e}")
            return False
        except new_genai.errors.APIError as e: # Catch general new SDK API errors
            print(f"Gemini service not available. New SDK API check failed: {e}")
            return False
        except Exception as e: # Catch other unexpected errors
            print(f"Gemini service not available. Unexpected error during API check: {e}")
            return False

    # _get_model_instance method is to be removed.
   
    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not self.client: # Should be caught by is_available, but as a safeguard
            raise LLMServiceUnavailableError("Gemini client not initialized.")
        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        model_to_use = f"models/{model or self.DEFAULT_MODEL}"

        generation_config_dict = {}
        if temperature is not None:
            # Ensure temperature is within valid range if SDK requires (e.g. 0.0 to 1.0 or 2.0)
            # Assuming google_types.GenerationConfig handles validation or API does.
            generation_config_dict["temperature"] = temperature
        if max_tokens is not None:
            generation_config_dict["max_output_tokens"] = max_tokens
        
        # Use google_types.GenerationConfig from the new SDK (or equivalent)
        # The new SDK might take dict directly or have its own config object.
        # Assuming new_genai.types.GenerationConfig or directly passing the dict.
        # Let's use the new SDK's types: google_types.GenerationConfig
        effective_generation_config = google_types.GenerationConfig(**generation_config_dict) if generation_config_dict else None

        try:
            # Use the new client's async method for generating content
            # response = await self.client.generate_content_async( # This was for the old model instance
            # Example: response = await self.client.aio.generate_content(
            response = await self.client.aio.models.generate_content( # Corrected: client.aio.models.generate_content
                model=model_to_use,
                contents=[prompt], # New SDK expects a list of contents
                generation_config=effective_generation_config
            )
                
            # Process response - new SDK structure might differ
            # Assuming response.text directly gives the combined text
            if response.text:
                return response.text
            # Fallback for older structure or if parts are still relevant
            elif hasattr(response, 'parts') and response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else: # Handle cases where response might be empty or malformed
                error_details = "Unknown reason for empty content."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    # Accessing prompt_feedback might be different, e.g., response.prompt_feedback.block_reason
                    feedback_info = response.prompt_feedback
                    if hasattr(feedback_info, 'block_reason'):
                         error_details = f"Prompt feedback: Blocked - {feedback_info.block_reason}"
                         if hasattr(feedback_info, 'block_reason_message'):
                             error_details += f" ({feedback_info.block_reason_message})"
                    else:
                        error_details = f"Prompt feedback: {feedback_info}"
                elif not response.candidates: # No candidates means no valid response.
                    error_details = "No candidates returned in response."
                raise LLMGenerationError(f"Gemini API call succeeded but returned no usable content. Model: {model_to_use}. Details: {error_details}")

        except NewBlockedPromptError as e: # Specific error for blocked prompts
            print(f"Gemini API error (model: {model_to_use}): Blocked prompt - {e}")
            raise LLMGenerationError(f"Content generation blocked for model {model_to_use}. Reason: {e}") from e
        except google_api_exceptions.PermissionDenied as e:
            print(f"Gemini API error (model: {model_to_use}): Permission Denied - {e}")
            raise LLMServiceUnavailableError(f"Permission denied for Gemini model {model_to_use}. API key issue or model access not granted: {e}") from e
        except google_api_exceptions.InvalidArgument as e: # E.g. invalid model name, bad request format
            print(f"Gemini API error (model: {model_to_use}): Invalid Argument - {e}")
            raise LLMGenerationError(f"Invalid argument for Gemini model {model_to_use} (e.g., model name, parameters): {e}") from e
        except new_genai.errors.APIError as e: # General new SDK API errors
            print(f"Gemini API error (model: {model_to_use}): {type(e).__name__} - {e}")
            raise LLMServiceUnavailableError(f"Failed to generate text with Gemini model {model_to_use} due to API error: {str(e)}") from e
        except Exception as e: # Catch broader exceptions
            print(f"Unexpected error during text generation (model: {model_to_use}): {type(e).__name__} - {e}")
            raise LLMGenerationError(f"An unexpected error occurred while generating text with {model_to_use}: {str(e)}") from e

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")
        # model_instance = self._get_model_instance(model) # _get_model_instance removed
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
                       f"Generate a detailed and engaging RPG campaign concept based on this idea: {user_prompt}. Include potential plot hooks, key NPCs, and unique settings."
        
        # Re-use generate_text for actual generation, passing current_user and db
        # Model passed to generate_text should be the short ID, generate_text will prefix with "models/"
        return await self.generate_text(prompt=final_prompt, current_user=current_user, db=db, model=(model or self.DEFAULT_MODEL), temperature=0.7, max_tokens=1000)

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
        
        # model_instance = self._get_model_instance(model) # _get_model_instance removed
        effective_model_for_toc = model or self.DEFAULT_MODEL


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
            model=effective_model_for_toc, # Use short model ID
            temperature=0.5,
            max_tokens=700
        )
        if not raw_toc_string:
             raise LLMGenerationError(f"Gemini API call for Display TOC (model: models/{effective_model_for_toc}) succeeded but returned no usable content.")

        return self._parse_toc_string_with_types(raw_toc_string)

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> List[str]: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass args
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")
        # model_instance = self._get_model_instance(model) # _get_model_instance removed
        effective_model_for_titles = model or self.DEFAULT_MODEL
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names", db=db)
        final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count) if custom_prompt_template else \
                       f"Based on the following RPG campaign concept: '{campaign_concept}', generate {count} alternative, catchy campaign titles. List each title on a new line. Ensure only the titles are listed, nothing else."
        text_response = await self.generate_text(prompt=final_prompt, current_user=current_user, db=db, model=effective_model_for_titles, temperature=0.7, max_tokens=150 + (count * 20)) # Pass args
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
        # model_instance = self._get_model_instance(model) # _get_model_instance removed
        effective_model_for_section = model or self.DEFAULT_MODEL
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
        
        return await self.generate_text(prompt=final_prompt_for_generation, current_user=current_user, db=db, model=effective_model_for_section, temperature=0.7, max_tokens=4000)

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, any]]:
        if not await self.is_available(current_user=current_user, db=db):
            print("Warning: Gemini API key not configured or service unavailable. Cannot fetch models.")
            return [] # Return empty list as per new requirement for unavailability

        if not self.client: # Should be caught by is_available
            return []

        available_models_list: List[Dict[str, any]] = []
        try:
            print("Fetching available models from new Gemini SDK...")
            # Use self.client.aio.models.list()
            api_models_iterator = await self.client.aio.models.list()

            async for sdk_model in api_models_iterator:
                # DEBUG Logging for each SDK model
                print(f"DEBUG SDK Model: Name={sdk_model.name}, Display={sdk_model.display_name}, Methods={sdk_model.supported_generation_methods}")

                model_id_full = sdk_model.name # e.g., "models/gemini-1.5-pro-latest"
                model_id_short = model_id_full.split('/')[-1]
                model_name_display = sdk_model.display_name

                capabilities = []
                # Inspect sdk_model.supported_generation_methods
                # Example: ['generateContent', 'embedContent', 'generateAnswer']
                # Example for Imagen: ['generateImages', 'upscaleImages'] (speculative)
                if 'generateContent' in sdk_model.supported_generation_methods:
                    capabilities.append("chat")
                if 'generateImages' in sdk_model.supported_generation_methods: # For Imagen models
                    capabilities.append("image_generation")
                if 'embedContent' in sdk_model.supported_generation_methods:
                    capabilities.append("embedding")

                # Determine model_type
                model_type = "image" if "image_generation" in capabilities else "chat"
                if not capabilities: # If no known capabilities, mark as other or skip
                    model_type = "other"

                # Assume True for temperature for now, or check sdk_model attributes if available
                # sdk_model might have attributes like `temperature_control` (bool) or similar
                supports_temperature = True # Default assumption

                available_models_list.append({
                    "id": model_id_short, # Store short ID
                    "name": model_name_display,
                    "model_type": model_type,
                    "supports_temperature": supports_temperature,
                    "capabilities": capabilities,
                    "provider": "gemini" # Add provider info
                })

            if not available_models_list:
                print("Warning: New Gemini SDK returned no models. Using hardcoded list as fallback.")
                # Fallback logic can be similar to before, or simplified
                raise Exception("No suitable models found from API with new SDK")

        except Exception as e:
            print(f"Could not dynamically fetch models from new Gemini SDK: {e}. Using a hardcoded list as fallback.")
            # Fallback list (ensure it matches the new structure)
            available_models_list = [
                {"id": "gemini-1.5-pro-latest", "name": "Gemini 1.5 Pro (Latest)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"], "provider": "gemini"},
                {"id": "gemini-1.5-flash-latest", "name": "Gemini 1.5 Flash (Latest)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"], "provider": "gemini"},
                {"id": "imagen-latest", "name": "Imagen (Latest)", "model_type": "image", "supports_temperature": True, "capabilities": ["image_generation"], "provider": "gemini"}, # Example Imagen
            ]
            # Ensure default model is in the list if using fallback
            default_model_id_short = self.DEFAULT_MODEL # e.g., "gemini-1.5-flash-latest"
            if not any(m['id'] == default_model_id_short for m in available_models_list):
                 available_models_list.insert(0, {
                        "id": default_model_id_short,
                        "name": default_model_id_short.replace("-", " ").title() + " (Default)",
                        "model_type": "chat", # Assuming default is chat
                        "supports_temperature": True,
                        "capabilities": ["chat", "vision"] if "vision" in default_model_id_short or "flash" in default_model_id_short else ["chat"], # Basic assumption
                        "provider": "gemini"
                    })

        # Sort models
        available_models_list.sort(key=lambda x: (
            "imagen" in x["id"], # Put Imagen models last or first based on preference
            "latest" not in x["id"],
            "pro" not in x["id"],
            "flash" not in x["id"],
            x["name"]
        ))
        return available_models_list

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # The new google-genai SDK's Client object might have a close method,
        # especially if it uses gRPC or HTTP/2 connections.
        # For an async client (self.client.aio), it might be self.client.aio.close()
        # or the underlying transport might need closing.
        # For now, assume no explicit close is needed or it's handled by garbage collection.
        if hasattr(self.client, 'aio') and hasattr(self.client.aio, '_transport') and hasattr(self.client.aio._transport, 'close'):
            try:
                await self.client.aio._transport.close()
                print("Closed Gemini async client transport.")
            except Exception as e:
                print(f"Error closing Gemini async client transport: {e}")
        elif hasattr(self.client, 'close'): # If the main client has close
             try:
                if asyncio.iscoroutinefunction(self.client.close):
                    await self.client.close()
                else:
                    self.client.close()
                print("Closed Gemini client.")
             except Exception as e:
                print(f"Error closing Gemini client: {e}")
        pass

    async def generate_homebrewery_toc_from_sections(self, sections_summary:str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        if not sections_summary:
            return "{{toc,wide\n# Table Of Contents\n}}\n"

        # model_instance = self._get_model_instance(model) # _get_model_instance removed
        effective_model_for_hb_toc = model or self.DEFAULT_MODEL


        prompt_template_str = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not prompt_template_str:
            raise LLMGenerationError("Homebrewery TOC prompt template ('TOC Homebrewery') not found in database for Gemini.")

        final_prompt = prompt_template_str.format(sections_summary=sections_summary)

        generated_toc = await self.generate_text(
            prompt=final_prompt,
            current_user=current_user,
            db=db,
            model=effective_model_for_hb_toc, # Use short model ID
            temperature=0.3, # Consistent with OpenAI
            max_tokens=1000    # Consistent with OpenAI
        )
        if not generated_toc:
            raise LLMGenerationError(f"Gemini API call for Homebrewery TOC from sections (model: models/{effective_model_for_hb_toc}) succeeded but returned no usable content.")

        return generated_toc

    async def generate_image(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, size: Optional[str] = None) -> bytes:
        """
        Generates an image using an Imagen model via the new Gemini SDK.
        The 'size' parameter is currently conceptual and not directly mapped to API.
        """
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service (for image generation) is not available.")
        if not self.client:
             raise LLMServiceUnavailableError("Gemini client not initialized for image generation.")

        if not prompt:
            raise ValueError("Prompt cannot be empty for image generation.")

        # Default to a known Imagen model if not specified.
        # User should pass short ID like "imagen-005" or "imagen-latest"
        imagen_model_id_short = model or "imagen-latest" # TODO: Confirm a default Imagen model ID from list_available_models
        model_to_use = f"models/{imagen_model_id_short}"

        # Configure image generation parameters
        # TODO: Map 'size' (e.g., "1024x1024") to API if supported.
        # google_types.GenerateImagesConfig might take width, height, aspect_ratio, etc.
        # For now, number_of_images and mime_type are common.
        image_gen_config = google_types.GenerateImagesConfig(
            number_of_images=1,
            # output_mime_type='image/png' # This might be specific to older SDK or a different method.
            # The new SDK's generate_images might infer or have different config.
            # For now, let's assume the default is PNG or the SDK handles it.
        )
        # If size is "WxH", parse it. Example:
        # width, height = None, None
        # if size and 'x' in size:
        #   try:
        #       width, height = map(int, size.split('x'))
        #       image_gen_config.width = width # If supported by GenerateImagesConfig
        #       image_gen_config.height = height # If supported
        #   except ValueError:
        #       print(f"Warning: Could not parse size '{size}' for Imagen.")


        try:
            print(f"Attempting to generate image with Imagen model: {model_to_use} using prompt: '{prompt[:50]}...'")

            # Use the new client's async method for generating images
            # response = await self.client.aio.generate_images( # This was a guess
            response = await self.client.aio.models.generate_images( # Corrected: client.aio.models.generate_images
                model=model_to_use,
                prompt=prompt,
                # config=image_gen_config # config might not be a direct param here, or named differently
                # The method signature for client.aio.models.generate_images needs to be confirmed.
                # It might be: generate_images(resource_name=model_to_use, prompt=prompt)
                # Let's assume for now it takes prompt directly. If config is needed, it might be part of model options.
            )

            # Process the response to extract image bytes
            # This is speculative and needs to be verified against the actual new SDK response structure.
            # Assuming response.generated_images is a list of objects, each with image data.
            if hasattr(response, 'generated_images') and response.generated_images and len(response.generated_images) > 0:
                img_obj = response.generated_images[0] # Get the first image

                # Try to access image bytes. Common attributes could be:
                # img_obj.image_bytes, img_obj.data, img_obj._image_bytes, img_obj.content
                if hasattr(img_obj, '_image_bytes'): # Based on some Google SDK patterns
                    image_bytes = img_obj._image_bytes
                    if image_bytes: return image_bytes
                elif hasattr(img_obj, 'image_bytes'):
                    image_bytes = img_obj.image_bytes
                    if image_bytes: return image_bytes
                elif hasattr(img_obj, 'data'): # Another common pattern
                    image_bytes = img_obj.data
                    if isinstance(image_bytes, bytes): return image_bytes

                # If direct byte access fails, log for debugging
                print(f"DEBUG: Imagen response img_obj type: {type(img_obj)}, attributes: {dir(img_obj)}")
                raise LLMGenerationError(f"Could not extract image bytes from Imagen response object of type {type(img_obj)}.")
            else:
                # Log details if the response is not as expected.
                error_message = "Imagen API call succeeded but returned no image data or unexpected structure."
                # You might want to log the full response here for debugging if it's small enough
                # print(f"Unexpected response structure from Imagen generation: {response}")
                raise LLMGenerationError(error_message)

        except google_api_exceptions.PermissionDenied as e:
            print(f"Imagen API error (model: {model_to_use}): Permission Denied - {e}")
            raise LLMServiceUnavailableError(f"Permission denied for Imagen model {model_to_use}. API key issue, allowlist, or model access not granted: {e}") from e
        except google_api_exceptions.InvalidArgument as e:
             print(f"Imagen API error (model: {model_to_use}): Invalid Argument - {e}")
             raise LLMGenerationError(f"Invalid argument for Imagen model {model_to_use} (e.g., model name, parameters): {e}") from e
        except new_genai.errors.APIError as e: # General new SDK API errors
            print(f"Error during Imagen image generation (model: {model_to_use}): {type(e).__name__} - {e}")
            raise LLMGenerationError(f"Failed to generate image with Imagen model {model_to_use}: {e}") from e
        except Exception as e:
            print(f"Unexpected error during Imagen image generation (model: {model_to_use}): {type(e).__name__} - {e}")
            raise LLMGenerationError(f"An unexpected error occurred with Imagen model {model_to_use}: {e}") from e


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
