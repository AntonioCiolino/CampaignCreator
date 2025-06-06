from openai import AsyncOpenAI, APIError  # Use AsyncOpenAI and new error type
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError # Import errors
from app.services.feature_prompt_service import FeaturePromptService
# Removed import from llm_factory: from app.services.llm_factory import LLMServiceUnavailableError

class OpenAILLMService(AbstractLLMService):
    PROVIDER_NAME = "openai" # Class variable for provider name
    DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
    DEFAULT_COMPLETION_MODEL = "gpt-3.5-turbo-instruct" # Still relevant if we support legacy

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.async_client: Optional[AsyncOpenAI] = None # Initialize as None
        if self.api_key and self.api_key not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            self.async_client = AsyncOpenAI(api_key=self.api_key)
        else:
            # This will be caught by is_available, or raise error if service used without key
            print("Warning: OpenAI API key not configured or is a placeholder.")
        self.feature_prompt_service = FeaturePromptService()

    async def is_available(self) -> bool:
        if not self.api_key or self.api_key in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY"]:
            return False
        if not self.async_client:
            # Attempt to re-initialize if api_key was set later (though unlikely with current setup)
            # Or simply return False, as __init__ should have set it.
            try:
                self.async_client = AsyncOpenAI(api_key=self.api_key)
            except Exception:
                return False # Failed to initialize client

        try:
            await self.async_client.models.list()
            return True
        except APIError as e:
            print(f"OpenAI service not available due to APIError during models.list(): {e.status_code} - {e.message}")
            # This indicates a fundamental issue like bad API key or connectivity problem.
            raise LLMServiceUnavailableError(f"OpenAI API Error: {e.status_code} - {e.message or str(e)}") from e
        except Exception as e:
            print(f"OpenAI service not available due to an unexpected error during models.list(): {e}")
            raise LLMServiceUnavailableError(f"Unexpected error checking OpenAI availability: {str(e)}") from e

    def _get_model(self, preferred_model: Optional[str], use_chat_model: bool = True) -> str:
        """Helper to determine the model to use, falling back to defaults if None."""
        if preferred_model:
            return preferred_model
        return self.DEFAULT_CHAT_MODEL if use_chat_model else self.DEFAULT_COMPLETION_MODEL

    async def _perform_chat_completion(self, selected_model: str, messages: List[Dict[str,str]], temperature: float, max_tokens: int) -> str:
        if not self.async_client:
             raise LLMServiceUnavailableError("OpenAI AsyncClient not initialized.")
        try:
            chat_completion = await self.async_client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
                return chat_completion.choices[0].message.content.strip()
            # If no content, it's a generation issue.
            raise LLMGenerationError("OpenAI API call (ChatCompletion) succeeded but returned no usable content.")
        except APIError as e:
            error_detail = f"OpenAI API Error ({e.status_code}): {e.message or str(e)}"
            print(error_detail)
            if e.status_code == 401: # Unauthorized
                raise LLMServiceUnavailableError(error_detail) from e
            elif e.status_code == 429: # Rate limit
                raise LLMGenerationError(f"OpenAI rate limit exceeded. Detail: {error_detail}") from e
            else: # Other API errors (400 for bad input, 5xx for server issues)
                raise LLMGenerationError(error_detail) from e
        except Exception as e: # Catch other unexpected errors
            print(f"Unexpected error with model {selected_model} (ChatCompletion): {e}")
            raise LLMGenerationError(f"Unexpected error during OpenAI call: {str(e)}") from e

    async def _perform_legacy_completion(self, selected_model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        if not self.async_client:
             raise LLMServiceUnavailableError("OpenAI AsyncClient not initialized.")
        print(f"Warning: Using legacy completions endpoint for model {selected_model}. Consider migrating to chat completions if possible.")
        try:
            completion = await self.async_client.completions.create(
                model=selected_model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if completion.choices and completion.choices[0].text:
                return completion.choices[0].text.strip()
            raise LLMGenerationError("OpenAI API call (Legacy Completion) succeeded but returned no content.")
        except APIError as e:
            error_detail = f"OpenAI API Error ({e.status_code}): {e.message or str(e)}"
            print(error_detail)
            if e.status_code == 401: # Unauthorized
                raise LLMServiceUnavailableError(error_detail) from e
            elif e.status_code == 429: # Rate limit
                raise LLMGenerationError(f"OpenAI rate limit exceeded. Detail: {error_detail}") from e
            else: # Other API errors
                raise LLMGenerationError(error_detail) from e
        except Exception as e:
            print(f"Unexpected error with model {selected_model} (Legacy Completion): {e}")
            raise LLMGenerationError(f"Unexpected error during OpenAI legacy completion call: {str(e)}") from e

    async def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str:
        if not await self.is_available():
             raise LLMServiceUnavailableError("OpenAI service is not available.")
        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        selected_model = self._get_model(model, use_chat_model=True)
        
        # Prioritize ChatCompletion, especially for newer models.
        # The openai v1.x library encourages ChatCompletion even for instruct-like models.
        # Models like "gpt-3.5-turbo-instruct" are generally completion models.
        if selected_model.endswith("-instruct") or "davinci" in selected_model or "curie" in selected_model or "babbage" in selected_model or "ada" in selected_model:
             # Check if it's one of the few that might strictly need legacy Completion API
            if selected_model in ["text-davinci-003", "text-davinci-002", "davinci", "curie", "babbage", "ada"]: # Add other true legacy models if any
                 return await self._perform_legacy_completion(selected_model, prompt, temperature, max_tokens)
        
        # Default to ChatCompletion for gpt-4, gpt-3.5-turbo, fine-tuned gpt-3.5-turbo, and others.
        # For "gpt-3.5-turbo-instruct", it can also be used with ChatCompletion by structuring the prompt.
        messages = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}]
        if selected_model == "gpt-3.5-turbo-instruct": # Example of adapting an instruct model to chat
            messages = [{"role": "user", "content": prompt}] # Simpler structure for instruct-like via chat

        return await self._perform_chat_completion(selected_model, messages, temperature, max_tokens)

    async def generate_campaign_concept(self, user_prompt: str, db: Session, model: Optional[str] = None) -> str:
        if not await self.is_available():
            raise LLMServiceUnavailableError("OpenAI service is not available.")

        # For creative tasks like campaign concept, chat models are generally preferred.
        selected_model = self._get_model(model, use_chat_model=True)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
                       f"Generate a detailed campaign concept, including potential plot hooks and key NPCs, based on the following idea: {user_prompt}"

        messages = [
            {"role": "system", "content": "You are a creative assistant helping to brainstorm RPG campaign concepts."},
            {"role": "user", "content": final_prompt}
        ]
        return await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=1000)

    async def generate_toc(self, campaign_concept: str, db: Session, model: Optional[str] = None) -> Dict[str, str]:
        if not await self.is_available():
            raise LLMServiceUnavailableError("OpenAI service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")

        selected_model = self._get_model(model, use_chat_model=True)

        # Fetch Display TOC prompt
        display_prompt_template_str = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template_str:
            raise LLMGenerationError("Display TOC prompt template ('TOC Display') not found in database.")
        display_final_prompt = display_prompt_template_str.format(campaign_concept=campaign_concept)
        
        display_messages = [
            {"role": "system", "content": "You are an assistant skilled in structuring RPG campaign narratives and creating user-friendly Table of Contents for on-screen display."},
            {"role": "user", "content": display_final_prompt}
        ]
        generated_display_toc = await self._perform_chat_completion(selected_model, display_messages, temperature=0.5, max_tokens=700)
        if not generated_display_toc:
            raise LLMGenerationError("OpenAI API call for Display TOC succeeded but returned no usable content.")

        # Fetch Homebrewery TOC prompt
        homebrewery_prompt_template_str = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not homebrewery_prompt_template_str:
            raise LLMGenerationError("Homebrewery TOC prompt template ('TOC Homebrewery') not found in database.")
        homebrewery_final_prompt = homebrewery_prompt_template_str.format(campaign_concept=campaign_concept)

        homebrewery_messages = [
            {"role": "system", "content": "You are an assistant skilled in creating RPG Table of Contents strictly following Homebrewery Markdown formatting."},
            {"role": "user", "content": homebrewery_final_prompt}
        ]
        generated_homebrewery_toc = await self._perform_chat_completion(selected_model, homebrewery_messages, temperature=0.5, max_tokens=700)
        if not generated_homebrewery_toc:
            raise LLMGenerationError("OpenAI API call for Homebrewery TOC succeeded but returned no usable content.")

        return {
            "display_toc": generated_display_toc,
            "homebrewery_toc": generated_homebrewery_toc
        }

    async def generate_titles(self, campaign_concept: str, db: Session, count: int = 5, model: Optional[str] = None) -> list[str]:
        if not await self.is_available():
            raise LLMServiceUnavailableError("OpenAI service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")

        selected_model = self._get_model(model, use_chat_model=True)
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names", db=db)
        final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count) if custom_prompt_template else \
                       f"Based on the campaign concept: '{campaign_concept}', generate {count} alternative, catchy campaign titles. List each title on a new line."
        messages = [
            {"role": "system", "content": "You are an assistant skilled in brainstorming creative and catchy titles for RPG campaigns."},
            {"role": "user", "content": final_prompt}
        ]

        titles_text = await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=150 + (count * 20))
        titles_list = [title.strip() for title in titles_text.split('\n') if title.strip()]
        return titles_list[:count]

    async def generate_section_content(self, campaign_concept: str, db: Session, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: Optional[str] = None) -> str:
        if not await self.is_available():
            raise LLMServiceUnavailableError("OpenAI service is not available.")
        if not campaign_concept: # Basic check, though prompt construction is more complex
            raise ValueError("Campaign concept is required.")

        selected_model = self._get_model(model, use_chat_model=True)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content", db=db)
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=section_creation_prompt or "Continue the story from where it left off, or introduce a new related event/location/character interaction.",
                section_title_suggestion=section_title_suggestion or "Next Chapter"
            )
        else: # Simplified default if CSV prompt is missing
            final_prompt = f"Campaign Concept: {campaign_concept}\n"
            if existing_sections_summary:
                final_prompt += f"Summary of existing sections: {existing_sections_summary}\n"
            final_prompt += f"Instruction for new section (titled '{section_title_suggestion or 'Next Chapter'}'): {section_creation_prompt or 'Develop the next part of the story.'}"

        messages = [
            {"role": "system", "content": "You are an expert RPG writer, crafting a new section for an ongoing campaign. Ensure the content is engaging and fits the narrative style implied by the concept and existing sections."},
            {"role": "user", "content": final_prompt}
        ]
        return await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=1500)

    async def list_available_models(self) -> List[Dict[str, str]]:
        if not await self.is_available(): # Use the async is_available
            print("Warning: OpenAI API key not configured or service unavailable. Cannot fetch models.")
            return []
        if not self.async_client:
            return [] # Should have been caught by is_available

        models_to_return: Dict[str, Dict[str, str]] = {}

        # Manually add well-known models with user-friendly names
        # These are preferred and will be shown first if available.
        common_models = {
            "gpt-4": {"id": "gpt-4", "name": "GPT-4", "capabilities": ["chat"]},
            "gpt-4-turbo-preview": {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview", "capabilities": ["chat"]},
            "gpt-4o": {"id": "gpt-4o", "name": "GPT-4 Omni", "capabilities": ["chat"]}, # Assuming chat, may have vision too
            "gpt-3.5-turbo": {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Chat)", "capabilities": ["chat"]},
            "gpt-3.5-turbo-instruct": {"id": "gpt-3.5-turbo-instruct", "name": "GPT-3.5 Turbo Instruct", "capabilities": ["completion", "chat-adaptable"]},
        }
        models_to_return.update(common_models)

        try:
            response = await self.async_client.models.list()
            if response and response.data:
                for model_obj in response.data:
                    model_id = model_obj.id
                    if model_id not in models_to_return: # Prioritize manually defined names
                        # Simple naming for less common models pulled from API
                        name_parts = [part.capitalize() for part in model_id.split('-')]
                        name = " ".join(name_parts)
                        capabilities = ["chat"] # Default to chat for unknown modern models

                        if "gpt-3.5" in model_id and "turbo" in model_id and "instruct" not in model_id:
                            name += " (Chat)"
                            capabilities = ["chat"]
                        elif "instruct" in model_id: # Covers gpt-3.5-turbo-instruct if not in common_models
                             name += " (Instruct)"
                             capabilities = ["completion", "chat-adaptable"]
                        elif any(legacy_kw in model_id for legacy_kw in ["davinci", "curie", "babbage", "ada"]) and "instruct" not in model_id:
                             name += " (Legacy Completion)"
                             capabilities = ["completion"]
                        elif model_id.startswith("ft:gpt-3.5-turbo"):
                            name = f"Fine-tuned (GPT-3.5T): {model_id.split(':')[-1]}"
                            capabilities = ["chat"]
                        elif model_id.startswith("ft:davinci") or model_id.startswith("ft:curie") or model_id.startswith("ft:babbage") or model_id.startswith("ft:ada"):
                            name = f"Fine-tuned (Legacy): {model_id.split(':')[-1]}"
                            capabilities = ["completion"]
                        elif model_id.startswith("ft:"): # Generic fine-tune
                            name = f"Fine-tuned: {model_id.split(':')[-1]}"
                            # Default to chat for unknown fine-tunes, or could be more specific if base model known
                            capabilities = ["chat"]


                        models_to_return[model_id] = {"id": model_id, "name": name, "capabilities": capabilities}
        except APIError as e:
            # If listing models fails due to API key or fundamental issue, it means service is unavailable.
            error_detail = f"OpenAI API Error ({e.status_code}) while listing models: {e.message or str(e)}"
            print(error_detail)
            raise LLMServiceUnavailableError(error_detail) from e
        except Exception as e:
            # Catch any other unexpected errors during model listing
            print(f"An unexpected error occurred when listing OpenAI models: {e}. Returning manually curated list only if any.")
            # Depending on strictness, could raise LLMServiceUnavailableError here too,
            # but returning what we have (even if just common_models) might be acceptable.
            # For now, let's be strict: if API list fails, the service is not fully operational for model discovery.
            if not models_to_return: # If we couldn't even rely on common_models initially
                 raise LLMServiceUnavailableError(f"Unexpected error listing OpenAI models: {str(e)}") from e
            # else, we return the common_models at least

        # Sort models: GPT-4 versions first, then GPT-3.5 Turbo, then Instruct, then others alphabetically.
        sorted_models = sorted(list(models_to_return.values()), key=lambda x: (
            not x['name'].startswith("GPT-4"),
            not x['name'].startswith("GPT-3.5 Turbo (Chat)"),
            not x['name'].startswith("GPT-3.5 Turbo Instruct"),
            x['name']
        ))
        return sorted_models

    async def close(self):
        """Close the AsyncOpenAI client if it was initialized."""
        if self.async_client:
            await self.async_client.close()
            print("OpenAI AsyncClient closed.")
