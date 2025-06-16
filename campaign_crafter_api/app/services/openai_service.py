from openai import AsyncOpenAI, APIError
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import decrypt_key
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app.models import User as UserModel
from app import crud # Added crud import

class OpenAILLMService(AbstractLLMService):
    PROVIDER_NAME = "openai"
    DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
    DEFAULT_COMPLETION_MODEL = "gpt-3.5-turbo-instruct"

    def __init__(self):
        self.feature_prompt_service = FeaturePromptService()

    async def _get_openai_api_key_for_user(self, current_user: UserModel, db: Session) -> str: # Added db
        """
        Retrieves the appropriate OpenAI API key for the given user from DB.
        1. User's own key (decrypted from ORM user model)
        2. Superuser fallback (from settings.OPENAI_API_KEY)
        Raises HTTPException if no valid key is found or user not found.
        """
        orm_user = crud.get_user(db, user_id=current_user.id)
        if not orm_user:
            # This should ideally not happen if current_user (Pydantic) is valid
            raise HTTPException(status_code=404, detail="User not found in database for API key retrieval.")

        if orm_user.encrypted_openai_api_key: # Use orm_user here
            decrypted_user_key = decrypt_key(orm_user.encrypted_openai_api_key)
            if decrypted_user_key:
                return decrypted_user_key
            else:
                print(f"Warning: Failed to decrypt stored OpenAI API key for user {orm_user.id}")

        # Check superuser status from orm_user or current_user (Pydantic model should be up-to-date)
        # Using orm_user.is_superuser is fine if we trust the DB state is what we need for this check.
        if orm_user.is_superuser:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY", ""]:
                return settings.OPENAI_API_KEY
            else:
                print("Warning: Superuser attempted to use OpenAI, but settings.OPENAI_API_KEY is not configured or is a placeholder.")

        raise HTTPException(status_code=403, detail="OpenAI API key not available for this user, and no valid fallback key is configured.")

    async def is_available(self, current_user: UserModel, db: Session) -> bool: # Added db
        try:
            api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
            # api_key check is implicitly handled by _get_openai_api_key_for_user raising HTTPException

            async with AsyncOpenAI(api_key=api_key) as client:
                await client.models.list()
            return True
        except HTTPException:
            return False
        except APIError as e:
            print(f"OpenAI service check failed for user {current_user.id} due to APIError: {e.status_code} - {e.message}")
            return False
        except Exception as e:
            print(f"OpenAI service check failed for user {current_user.id} due to an unexpected error: {e}")
            return False

    def _get_model(self, preferred_model: Optional[str], use_chat_model: bool = True) -> str:
        """Helper to determine the model to use, falling back to defaults if None."""
        if preferred_model:
            return preferred_model
        return self.DEFAULT_CHAT_MODEL if use_chat_model else self.DEFAULT_COMPLETION_MODEL

    async def _perform_chat_completion(self, selected_model: str, messages: List[Dict[str,str]], temperature: float, max_tokens: int, api_key: str) -> str:
        if not api_key:
             raise LLMServiceUnavailableError("OpenAI API key not provided for chat completion.")
        try:
            async with AsyncOpenAI(api_key=api_key) as client:
                chat_completion = await client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens
                )
            if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
                return chat_completion.choices[0].message.content.strip()
            # If no content, it's a generation issue.
            raise LLMGenerationError("OpenAI API call (ChatCompletion) succeeded but returned no usable content.")
        except APIError as e:
            error_detail = f"OpenAI API Error ({e.status_code}): {e.message or str(e)}"
            print(error_detail)
            if e.status_code == 401: # Unauthorized (this might mean the user-provided key is bad)
                raise LLMServiceUnavailableError(f"OpenAI API key is invalid or unauthorized. Detail: {error_detail}") from e
            elif e.status_code == 429: # Rate limit
                raise LLMGenerationError(f"OpenAI rate limit exceeded. Detail: {error_detail}") from e
            else: # Other API errors (400 for bad input, 5xx for server issues)
                raise LLMGenerationError(error_detail) from e
        except Exception as e: # Catch other unexpected errors
            print(f"Unexpected error with model {selected_model} (ChatCompletion): {e}")
            raise LLMGenerationError(f"Unexpected error during OpenAI call: {str(e)}") from e

    async def _perform_legacy_completion(self, selected_model: str, prompt: str, temperature: float, max_tokens: int, api_key: str) -> str:
        if not api_key:
            raise LLMServiceUnavailableError("OpenAI API key not provided for legacy completion.")
        print(f"Warning: Using legacy completions endpoint for model {selected_model}. Consider migrating to chat completions if possible.")
        try:
            async with AsyncOpenAI(api_key=api_key) as client:
                completion = await client.completions.create(
                    model=selected_model,
                    prompt=prompt,
                    temperature=temperature,
                    max_completion_tokens=max_tokens
                )
            if completion.choices and completion.choices[0].text:
                return completion.choices[0].text.strip()
            raise LLMGenerationError("OpenAI API call (Legacy Completion) succeeded but returned no content.")
        except APIError as e:
            error_detail = f"OpenAI API Error ({e.status_code}): {e.message or str(e)}"
            print(error_detail)
            if e.status_code == 401: # Unauthorized
                raise LLMServiceUnavailableError(f"OpenAI API key is invalid or unauthorized. Detail: {error_detail}") from e
            elif e.status_code == 429: # Rate limit
                raise LLMGenerationError(f"OpenAI rate limit exceeded. Detail: {error_detail}") from e
            else: # Other API errors
                raise LLMGenerationError(error_detail) from e
        except Exception as e:
            print(f"Unexpected error with model {selected_model} (Legacy Completion): {e}")
            raise LLMGenerationError(f"Unexpected error during OpenAI legacy completion call: {str(e)}") from e

    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str: # Added db
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
        # No longer using self.is_available() here.
        # _get_openai_api_key_for_user handles key availability/permissions.
        # _perform_... methods handle API errors if key is invalid.

        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        selected_model = self._get_model(model, use_chat_model=True)
        
        # Prioritize ChatCompletion, especially for newer models.
        if selected_model.endswith("-instruct") or "davinci" in selected_model or "curie" in selected_model or "babbage" in selected_model or "ada" in selected_model:
            if selected_model in ["text-davinci-003", "text-davinci-002", "davinci", "curie", "babbage", "ada"]:
                 return await self._perform_legacy_completion(selected_model, prompt, temperature, max_tokens, api_key=openai_api_key)
        
        messages = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}]
        if selected_model == "gpt-3.5-turbo-instruct":
            messages = [{"role": "user", "content": prompt}]

        return await self._perform_chat_completion(selected_model, messages, temperature, max_tokens, api_key=openai_api_key)

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
        # Removed is_available check

        # For creative tasks like campaign concept, chat models are generally preferred.
        selected_model = self._get_model(model, use_chat_model=True)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
                       f"Generate a detailed campaign concept, including potential plot hooks and key NPCs, based on the following idea: {user_prompt}"

        messages = [
            {"role": "system", "content": "You are a creative assistant helping to brainstorm RPG campaign concepts."},
            {"role": "user", "content": final_prompt}
        ]
        return await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=1000, api_key=openai_api_key)

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> Dict[str, str]:
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
        # Removed is_available check

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
        generated_display_toc = await self._perform_chat_completion(selected_model, display_messages, temperature=0.5, max_tokens=700, api_key=openai_api_key)
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
        generated_homebrewery_toc = await self._perform_chat_completion(selected_model, homebrewery_messages, temperature=0.5, max_tokens=700, api_key=openai_api_key)
        if not generated_homebrewery_toc:
            raise LLMGenerationError("OpenAI API call for Homebrewery TOC succeeded but returned no usable content.")

        return {
            "display_toc": generated_display_toc,
            "homebrewery_toc": generated_homebrewery_toc
        }

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]:
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
        # Removed is_available check

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

        titles_text = await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=150 + (count * 20), api_key=openai_api_key)
        titles_list = [title.strip() for title in titles_text.split('\n') if title.strip()]
        return titles_list[:count]

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
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
        # Removed is_available check

        if not campaign_concept:
            raise ValueError("Campaign concept is required.")

        selected_model = self._get_model(model, use_chat_model=True)

        # Determine effective section creation prompt based on section_type and provided prompt
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
            # Combine if both exist, ensuring type_based_instruction is clearly framed as context or a primary goal
            effective_section_prompt = f"{type_based_instruction}\n\nFurther specific instructions for this section: {section_creation_prompt}"
        elif not effective_section_prompt:
            effective_section_prompt = "Continue the story from where it left off, or introduce a new related event/location/character interaction."


        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content", db=db)
        if custom_prompt_template:
            final_prompt_for_user_role = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=effective_section_prompt,
                section_title_suggestion=section_title_suggestion or "Next Chapter"
            )
        else: # Simplified default if CSV prompt is missing
            final_prompt_for_user_role = f"Campaign Concept: {campaign_concept}\n"
            if existing_sections_summary:
                final_prompt_for_user_role += f"Summary of existing sections: {existing_sections_summary}\n"
            final_prompt_for_user_role += f"Instruction for new section (titled '{section_title_suggestion or 'Next Chapter'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"

        system_message_content = "You are an expert RPG writer, crafting a new section for an ongoing campaign. Ensure the content is engaging and fits the narrative style implied by the concept and existing sections."
        if section_type and section_type.lower() not in ["generic", "unknown", "", None]:
            system_message_content += f" Pay special attention to the section type: {section_type}."


        messages = [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": final_prompt_for_user_role}
        ]
        return await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=1500, api_key=openai_api_key)

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, any]]: # Made current_user and db non-optional, changed return type
        api_key_to_use = await self._get_openai_api_key_for_user(current_user, db)

        processed_models: List[Dict[str, any]] = []
        # Using a set for quick lookup of already processed model IDs from the API
        # to give preference to our manually defined common_models.
        processed_api_model_ids = set()


        # Manually add well-known models with user-friendly names and correct types
        # These are preferred and will be shown first if available.
        common_models_data = [
            {"id": "gpt-4", "name": "GPT-4", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-4o", "name": "GPT-4 Omni", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            # {"id": "gpt-4.1-nano", "name": "OpenAI GPT 4.1 Nano", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]}, # Example, if such model exists
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Chat)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-3.5-turbo-instruct", "name": "GPT-3.5 Turbo Instruct", "model_type": "completion", "supports_temperature": True, "capabilities": ["completion"]},
        ]

        for model_data in common_models_data:
            processed_models.append(model_data)
            processed_api_model_ids.add(model_data["id"])

        try:
            async with AsyncOpenAI(api_key=api_key_to_use) as client:
                response = await client.models.list()

            if response and response.data:
                for model_obj in response.data:
                    model_id = model_obj.id
                    if model_id in processed_api_model_ids: # Already added with preferred details
                        continue

                    name_parts = [part.capitalize() for part in model_id.split('-')]
                    name = " ".join(name_parts)

                    model_type = "chat" # Default for modern OpenAI models
                    supports_temperature = True # Most OpenAI generative models do

                    if "instruct" in model_id or \
                       any(legacy_kw in model_id for legacy_kw in ["davinci", "curie", "babbage", "ada"]) and \
                       not any(ft_kw in model_id for ft_kw in ["ft:gpt-3.5-turbo", "ft:gpt-4"]) and \
                       not "embed" in model_id and not "turbo" in model_id : # ensure turbo isn't miscategorized if it's not -instruct
                        model_type = "completion"

                    # Refine naming and capabilities based on model type and ID
                    capabilities = [model_type]
                    if model_type == "chat":
                        if "gpt-3.5" in model_id and "turbo" in model_id and "instruct" not in model_id:
                            name = f"{name} (Chat)" if not name.endswith("(Chat)") else name
                        elif model_id.startswith("ft:gpt-3.5-turbo") or model_id.startswith("ft:gpt-4"):
                             name = f"Fine-tuned ({'GPT-3.5T' if 'gpt-3.5' in model_id else 'GPT-4'}): {model_id.split(':')[-1]}"
                    elif model_type == "completion":
                        if "instruct" in model_id:
                             name = f"{name} (Instruct)" if not name.endswith("(Instruct)") else name
                        elif any(legacy_kw in model_id for legacy_kw in ["davinci", "curie", "babbage", "ada"]):
                             name = f"{name} (Legacy Completion)" if not name.endswith("(Legacy Completion)") else name
                        elif model_id.startswith("ft:") and not (model_id.startswith("ft:gpt-3.5-turbo") or model_id.startswith("ft:gpt-4")): # other fine-tunes assumed completion
                             name = f"Fine-tuned (Legacy Base): {model_id.split(':')[-1]}"


                    processed_models.append({
                        "id": model_id,
                        "name": name,
                        "model_type": model_type,
                        "supports_temperature": supports_temperature,
                        "capabilities": capabilities
                    })
                    processed_api_model_ids.add(model_id)

        except APIError as e:
            user_id_info = f"user {current_user.id}" if current_user else "system key"
            error_detail = f"OpenAI API Error ({e.status_code}) while listing models for {user_id_info}: {e.message or str(e)}"
            print(error_detail)
            # Return whatever we have (common models) even if API fails
        except Exception as e:
            user_id_info = f"user {current_user.id}" if current_user else "system key"
            print(f"An unexpected error occurred when listing OpenAI models for {user_id_info}: {e}. Returning manually curated list if any.")

        # Sort models: GPT-4 versions first, then GPT-3.5 Turbo, then Instruct, then others alphabetically.
        # This sort order might need adjustment based on how model_type should influence sorting.
        # For now, keeping a similar sort logic.
        sorted_models_list = sorted(processed_models, key=lambda x: (
            not x['name'].startswith("GPT-4"),
            not x['name'].startswith("GPT-3.5 Turbo (Chat)"),
            not x['name'].startswith("GPT-3.5 Turbo Instruct"),
            x['model_type'] != "chat", # Prioritize chat models
            x['name']
        ))
        return sorted_models_list

    async def close(self):
        """Close the AsyncOpenAI client if it was initialized."""
        # Since clients are created per-request with 'async with',
        # a global self.async_client no longer exists to be closed here.
        # This method can be removed or left as a no-op.
        pass
        # if self.async_client:
        #     await self.async_client.close()
        #     print("OpenAI AsyncClient closed.")

    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        print(f"DEBUG OPENAI_HB_TOC: Received sections_summary: {sections_summary}")
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db)

        if not sections_summary:
            # Return a basic empty TOC if no sections are provided, or raise an error.
            # For now, returning a minimal valid Homebrewery TOC structure.
            return "{{toc,wide\n# Table Of Contents\n}}\n"

        selected_model = self._get_model(model, use_chat_model=True)

        homebrewery_prompt_template_str = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        print(f"DEBUG OPENAI_HB_TOC: Fetched prompt template: {homebrewery_prompt_template_str}")
        if not homebrewery_prompt_template_str:
            raise LLMGenerationError("Homebrewery TOC prompt template ('TOC Homebrewery') not found in database.")

        final_prompt = homebrewery_prompt_template_str.format(sections_summary=sections_summary)
        print(f"DEBUG OPENAI_HB_TOC: Formatted final_prompt: {final_prompt}")

        messages = [
            {"role": "system", "content": "You are an assistant skilled in creating RPG Table of Contents strictly following Homebrewery Markdown formatting, using provided section titles."},
            {"role": "user", "content": final_prompt}
        ]

        generated_toc = await self._perform_chat_completion(selected_model, messages, temperature=0.3, max_tokens=1000, api_key=openai_api_key)
        if not generated_toc:
            raise LLMGenerationError("OpenAI API call for Homebrewery TOC from sections succeeded but returned no usable content.")

        return generated_toc
