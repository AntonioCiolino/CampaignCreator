import re
from openai import AsyncOpenAI, APIError
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import decrypt_key
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app import models, orm_models
from app.models import User as UserModel
from app import crud

class OpenAILLMService(AbstractLLMService):
    PROVIDER_NAME = "openai"
    DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
    DEFAULT_COMPLETION_MODEL = "gpt-3.5-turbo-instruct"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.effective_api_key = self.api_key # Key from constructor (user-provided, already decrypted)
        if not self.effective_api_key:
            self.effective_api_key = settings.OPENAI_API_KEY # Fallback to system key

        self.client = None
        self.configured_successfully = False
        if self.effective_api_key and self.effective_api_key not in ["YOUR_API_KEY_HERE", "YOUR_OPENAI_API_KEY", ""]:
            try:
                self.client = AsyncOpenAI(api_key=self.effective_api_key)
                self.configured_successfully = True
            except Exception as e:
                print(f"Error initializing AsyncOpenAI client: {e}")
                # self.configured_successfully remains False
        else:
            print("Warning: OpenAI API key (user or system) not configured or is a placeholder.")

        self.feature_prompt_service = FeaturePromptService()

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        if not self.configured_successfully or not self.client:
            return False
        try:
            await self.client.models.list() # Test call
            return True
        except APIError as e:
            # User ID is available via current_user.id if needed for logging
            print(f"OpenAI service check failed due to APIError: {e.status_code} - {e.message}")
            return False
        except Exception as e:
            print(f"OpenAI service check failed due to an unexpected error: {e}")
            return False

    def _get_model(self, preferred_model: Optional[str], use_chat_model: bool = True) -> str:
        """Helper to determine the model to use, falling back to defaults if None."""
        if preferred_model:
            return preferred_model
        return self.DEFAULT_CHAT_MODEL if use_chat_model else self.DEFAULT_COMPLETION_MODEL

    async def _perform_chat_completion(self, selected_model: str, messages: List[Dict[str,str]], temperature: float, max_tokens: int) -> str: # Removed api_key parameter
        if not self.client:
            raise LLMServiceUnavailableError("OpenAI client not initialized.")
        try:
            chat_completion = await self.client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens
            )
            if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
                return chat_completion.choices[0].message.content.strip()
            raise LLMGenerationError("OpenAI API call (ChatCompletion) succeeded but returned no usable content.")
        except APIError as e:
            error_detail = f"OpenAI API Error ({e.status_code}): {e.message or str(e)}"
            print(error_detail)
            if e.status_code == 401:
                raise LLMServiceUnavailableError(f"OpenAI API key is invalid or unauthorized. Detail: {error_detail}") from e
            elif e.status_code == 429:
                raise LLMGenerationError(f"OpenAI rate limit exceeded. Detail: {error_detail}") from e
            else:
                raise LLMGenerationError(error_detail) from e
        except Exception as e:
            print(f"Unexpected error with model {selected_model} (ChatCompletion): {e}")
            raise LLMGenerationError(f"Unexpected error during OpenAI call: {str(e)}") from e

    async def _perform_legacy_completion(self, selected_model: str, prompt: str, temperature: float, max_tokens: int) -> str: # Removed api_key parameter
        if not self.client:
            raise LLMServiceUnavailableError("OpenAI client not initialized.")
        print(f"Warning: Using legacy completions endpoint for model {selected_model}. Consider migrating to chat completions if possible.")
        try:
            completion = await self.client.completions.create(
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
            if e.status_code == 401:
                raise LLMServiceUnavailableError(f"OpenAI API key is invalid or unauthorized. Detail: {error_detail}") from e
            elif e.status_code == 429:
                raise LLMGenerationError(f"OpenAI rate limit exceeded. Detail: {error_detail}") from e
            else:
                raise LLMGenerationError(error_detail) from e
        except Exception as e:
            print(f"Unexpected error with model {selected_model} (Legacy Completion): {e}")
            raise LLMGenerationError(f"Unexpected error during OpenAI legacy completion call: {str(e)}") from e

    async def generate_text(
        self,
        prompt: str, # This is expected to be the template string if context is provided
        current_user: UserModel,
        db: Session,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        # Context fields
        db_campaign: Optional[orm_models.Campaign] = None,
        section_title_suggestion: Optional[str] = None,
        section_type: Optional[str] = None,
        section_creation_prompt: Optional[str] = None # Added
    ) -> str:
        # --- DEBUG: Log entry parameters ---
        print(f"--- DEBUG OpenAI generate_text ENTRY: db_campaign_id: {db_campaign.id if db_campaign else 'None'}, title_suggestion: {section_title_suggestion}, section_type: {section_type}, section_creation_prompt: {section_creation_prompt[:50] if section_creation_prompt else 'None'}... ---")
        # --- END DEBUG ---
        if not await self.is_available(current_user, db):
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")

        if not prompt: # Prompt here is the template string from the request
            raise ValueError("Prompt template cannot be empty.")

        selected_model = self._get_model(model, use_chat_model=True)
        
        # This will be the string that might get formatted with context
        prompt_to_format = prompt
        system_message_content = "You are a helpful assistant." # Default system message

        if db_campaign:
            campaign_concept_str = db_campaign.concept if db_campaign.concept else "Not specified."

            character_info_parts = []
            if db_campaign.characters:
                for char in db_campaign.characters:
                    char_details = f"Character Name: {char.name}"
                    if char.description: char_details += f"\n  Description: {char.description}"
                    if char.notes_for_llm: char_details += f"\n  LLM Notes: {char.notes_for_llm}"
                    character_info_parts.append(char_details)
            campaign_characters_str = "This campaign has no explicitly defined characters yet."
            if character_info_parts:
                campaign_characters_str = "The following characters are part of this campaign:\n" + "\n\n".join(character_info_parts)

            # existing_sections_summary needs to be fetched if the placeholder is present
            # For simplicity in generate_text, we'll assume if this placeholder exists,
            # the caller (API endpoint) might need to pre-fill it or we make it simpler.
            # Here, we'll just use a placeholder if the main prompt expects it.
            # A more robust solution would involve fetching sections if the placeholder is found.
            all_campaign_sections = crud.get_campaign_sections(db=db, campaign_id=db_campaign.id, limit=None)
            existing_sections_summary_str = "; ".join(
                [s.title for s in all_campaign_sections if s.title]
            ) if all_campaign_sections else "No existing sections yet."

            format_kwargs = {
                "campaign_concept": campaign_concept_str,
                "campaign_characters": campaign_characters_str,
                "existing_sections_summary": existing_sections_summary_str,
                "section_title_suggestion": section_title_suggestion or "N/A",
                "title": section_title_suggestion or "N/A", # common alternative for title
                "section_type": section_type or "N/A",
                "section_type_for_llm": section_type or "N/A", # common alternative for type
                "section_creation_prompt": section_creation_prompt or "Please continue the narrative or generate content for the section based on the overall context." # Added
            }

            try:
                # Only try to format if there seems to be a placeholder
                if any(f"{{{key}}}" in prompt_to_format for key in format_kwargs):
                    prompt_to_format = prompt_to_format.format(**format_kwargs)
                # Update system message if campaign context is available
                system_message_content = "You are an expert RPG writer. Use the provided campaign context to generate content."
                if campaign_characters_str != "This campaign has no explicitly defined characters yet.":
                     system_message_content += f"\nConsider these characters:\n{campaign_characters_str}"

            except KeyError as e:
                print(f"Warning: Key error during prompt formatting in generate_text: {e}. Prompt may be partially formatted.")
                # Continue with potentially partially formatted prompt_to_format

        # --- DEBUG LOGGING for generate_text (now includes formatted prompt) ---
        print(f"--- DEBUG PROMPT START ({self.PROVIDER_NAME} - Generic Generate Text) ---")
        print(f"Model: {selected_model}")
        print(f"System Message: {system_message_content}")
        print(f"User Prompt (after potential formatting): {prompt_to_format[:500]}...") # Log potentially formatted prompt
        if selected_model.endswith("-instruct") or "davinci" in selected_model:
             # For legacy, the raw formatted prompt is used directly
            print(f"Raw Prompt (for legacy, after potential formatting): {prompt_to_format[:500]}...")
        print(f"--- DEBUG PROMPT END ({self.PROVIDER_NAME} - Generic Generate Text) ---")
        # --- END DEBUG LOGGING ---

        # Actual call to LLM
        if selected_model.endswith("-instruct") or "davinci" in selected_model or "curie" in selected_model or "babbage" in selected_model or "ada" in selected_model:
            if selected_model in ["text-davinci-003", "text-davinci-002", "davinci", "curie", "babbage", "ada"]:
                 return await self._perform_legacy_completion(selected_model, prompt_to_format, temperature, max_tokens)

        messages = [{"role": "system", "content": system_message_content}, {"role": "user", "content": prompt_to_format}]
        # Handle gpt-3.5-turbo-instruct specifically if it prefers no system message, though unlikely with context.
        # if selected_model == "gpt-3.5-turbo-instruct":
        #     messages = [{"role": "user", "content": prompt_to_format}]

        return await self._perform_chat_completion(selected_model, messages, temperature, max_tokens)

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user, db):
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")
        selected_model = self._get_model(model, use_chat_model=True)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
                       f"Generate a detailed campaign concept, including potential plot hooks and key NPCs, based on the following idea: {user_prompt}"

        messages = [
            {"role": "system", "content": "You are a creative assistant helping to brainstorm RPG campaign concepts."},
            {"role": "user", "content": final_prompt}
        ]
        return await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=1000)

    def _parse_toc_string_with_types(self, raw_toc_string: str) -> List[Dict[str, str]]:
        parsed_toc_items = []
        # Regex to capture title and type, case-insensitive for "Type"
        # Title: group 1, Type: group 2
        # Allows for optional space after hyphen and before [Type:...]
        regex = r"^\s*-\s*(.+?)\s*\[Type:\s*([^\]]+?)\s*\]\s*$"
        # Fallback regex for lines that might just be titles (e.g. if LLM doesn't provide type)
        fallback_regex = r"^\s*-\s*(.+)"
        # Known types for basic validation - adjust as needed, or make more dynamic
        known_types = ["monster", "character", "npc", "location", "item", "quest", "chapter", "note", "world_detail", "generic", "unknown"]


        for line in raw_toc_string.splitlines():
            line = line.strip()
            if not line:
                continue

            match = re.match(regex, line, re.IGNORECASE) # Match [Type: ...]
            if match:
                title = match.group(1).strip()
                type_str = match.group(2).strip().lower()
                # Optional: Validate against known_types or clean up type_str further
                if type_str not in known_types:
                    # This logic can be adjusted, e.g. log a warning, or try to find closest match
                    print(f"Warning: Unknown type '{type_str}' found for title '{title}'. Defaulting to 'unknown'.")
                    type_str = "unknown"
                parsed_toc_items.append({"title": title, "type": type_str})
            else:
                # If specific [Type: ...] format not found, try to capture it as a title with a default type
                fallback_match = re.match(fallback_regex, line)
                if fallback_match:
                    title = fallback_match.group(1).strip()
                    # Remove any lingering markdown link syntax from title if necessary
                    # e.g. "[A Title](some_link)" -> "A Title"
                    title = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", title).strip()
                    if title: # Ensure title is not empty
                         parsed_toc_items.append({"title": title, "type": "unknown"})
                # else: if no regex matches, the line is ignored or could be logged.
        return parsed_toc_items

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> List[Dict[str, str]]:
        if not await self.is_available(current_user, db): # Added is_available check
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")

        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")

        selected_model = self._get_model(model, use_chat_model=True)

        display_prompt_template_str = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template_str:
            # This is critical, if the main display TOC prompt is missing, we should error.
            raise LLMGenerationError("Display TOC prompt template ('TOC Display') not found in database.")
        
        try:
            display_final_prompt = display_prompt_template_str.format(campaign_concept=campaign_concept)
        except KeyError:
            # This would indicate a misconfigured "TOC Display" prompt, which is an issue.
            print(f"ERROR: Formatting 'TOC Display' prompt failed due to KeyError. Prompt: '{display_prompt_template_str}' Concept: '{campaign_concept}'")
            raise LLMGenerationError("Failed to format 'TOC Display' prompt due to unexpected placeholders.")

        display_messages = [
            {"role": "system", "content": "You are an assistant skilled in structuring RPG campaign narratives and creating user-friendly Table of Contents for on-screen display."},
            {"role": "user", "content": display_final_prompt}
        ]

        # api_key parameter already removed from the call in the previous step
        raw_toc_string = await self._perform_chat_completion(selected_model, display_messages, temperature=0.5, max_tokens=700)

        if not raw_toc_string:
            # If Display TOC generation itself fails or returns empty, this is a problem.
            raise LLMGenerationError("OpenAI API call for Display TOC succeeded but returned no usable content.")

        return self._parse_toc_string_with_types(raw_toc_string)

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]:
        if not await self.is_available(current_user, db):
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")
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

    async def generate_section_content(
        self,
        db_campaign: orm_models.Campaign, # Changed campaign_concept to db_campaign
        db: Session,
        current_user: UserModel,
        existing_sections_summary: Optional[str],
        section_creation_prompt: Optional[str],
        section_title_suggestion: Optional[str],
        model: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        if not await self.is_available(current_user, db):
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")

        campaign_concept = db_campaign.concept if db_campaign else "A general creative writing piece."
        if not campaign_concept: # Should ideally not happen if db_campaign is valid
            raise ValueError("Campaign concept is required and missing from campaign data.")

        selected_model = self._get_model(model, use_chat_model=True)
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
            else:
                type_based_instruction = f"This section is specifically about '{title_str}' which is a '{section_type}'. Generate detailed content appropriate for this type."

        if not effective_section_prompt and type_based_instruction:
            effective_section_prompt = type_based_instruction
        elif effective_section_prompt and type_based_instruction:
            effective_section_prompt = f"{type_based_instruction}\n\nFurther specific instructions for this section: {section_creation_prompt}"
        elif not effective_section_prompt:
            effective_section_prompt = "Continue the story from where it left off, or introduce a new related event/location/character interaction."

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
        final_prompt_for_user_role: str

        if custom_prompt_template:
            try:
                final_prompt_for_user_role = custom_prompt_template.format(
                    campaign_concept=campaign_concept,
                    existing_sections_summary=existing_sections_summary or "N/A",
                    section_creation_prompt=effective_section_prompt,
                    section_title_suggestion=section_title_suggestion or "Next Chapter",
                    campaign_characters=campaign_characters_formatted # Add new parameter
                )
            except KeyError as e:
                print(f"Warning: Prompt template 'Section Content' is missing a key: {e}. Falling back to default prompt structure. Please update the template to include 'campaign_characters'.")
                # Fallback structure if template is old
                final_prompt_for_user_role = (
                    f"Campaign Concept: {campaign_concept}\n"
                    f"Relevant Characters in this Campaign:\n{campaign_characters_formatted}\n\n"
                    f"Summary of existing sections: {existing_sections_summary or 'N/A'}\n"
                    f"Instruction for new section (titled '{section_title_suggestion or 'Next Chapter'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"
                )
        else: # Simplified default if no template found at all
            final_prompt_for_user_role = (
                f"Campaign Concept: {campaign_concept}\n"
                f"Relevant Characters in this Campaign:\n{campaign_characters_formatted}\n\n"
            )
            if existing_sections_summary:
                final_prompt_for_user_role += f"Summary of existing sections: {existing_sections_summary}\n"
            final_prompt_for_user_role += f"Instruction for new section (titled '{section_title_suggestion or 'Next Chapter'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"

        system_message_content = "You are an expert RPG writer, crafting a new section for an ongoing campaign. Ensure the content is engaging and fits the narrative style implied by the concept and existing sections."
        system_message_content += f"\nTake into account these characters who are part of the campaign context:\n{campaign_characters_formatted}" # Also add to system prompt for emphasis
        if section_type and section_type.lower() not in ["generic", "unknown", "", None]:
            system_message_content += f" Pay special attention to the section type: {section_type}."

        messages = [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": final_prompt_for_user_role}
        ]

        # --- DEBUG LOGGING for generate_section_content ---
        print(f"--- DEBUG PROMPT START ({self.PROVIDER_NAME} - generate_section_content) ---")
        print(f"Campaign ID: {db_campaign.id}, Model: {selected_model}")
        print(f"Section Title Suggestion: {section_title_suggestion}")
        print(f"Section Type: {section_type}")
        print(f"Section Creation Prompt (effective_section_prompt): {effective_section_prompt[:300]}...")
        print(f"Campaign Concept: {campaign_concept[:300]}...")
        print(f"Characters: {campaign_characters_formatted[:300]}...")
        print(f"Existing Sections Summary: {existing_sections_summary[:300] if existing_sections_summary else 'N/A'}...")
        print("\nFinal System Message:")
        print(system_message_content)
        print("\nFinal User Role Prompt:")
        print(final_prompt_for_user_role)
        print(f"--- DEBUG PROMPT END ({self.PROVIDER_NAME} - generate_section_content) ---")
        # --- END DEBUG LOGGING ---

        return await self._perform_chat_completion(selected_model, messages, temperature=0.7, max_tokens=1500)

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, any]]:
        if not await self.is_available(current_user, db):
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")

        processed_models: List[Dict[str, any]] = []
        processed_api_model_ids = set()

        common_models_data = [
            {"id": "gpt-4", "name": "GPT-4", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-4o", "name": "GPT-4 Omni", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Chat)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            {"id": "gpt-3.5-turbo-instruct", "name": "GPT-3.5 Turbo Instruct", "model_type": "completion", "supports_temperature": True, "capabilities": ["completion"]},
        ]

        for model_data in common_models_data:
            processed_models.append(model_data)
            processed_api_model_ids.add(model_data["id"])

        try:
            response = await self.client.models.list() # Use self.client

            if response and response.data:
                for model_obj in response.data:
                    model_id = model_obj.id
                    if model_id in processed_api_model_ids:
                        continue

                    name_parts = [part.capitalize() for part in model_id.split('-')]
                    name = " ".join(name_parts)
                    model_type = "chat"
                    supports_temperature = True

                    if "instruct" in model_id or \
                       any(legacy_kw in model_id for legacy_kw in ["davinci", "curie", "babbage", "ada"]) and \
                       not any(ft_kw in model_id for ft_kw in ["ft:gpt-3.5-turbo", "ft:gpt-4"]) and \
                       not "embed" in model_id and not "turbo" in model_id :
                        model_type = "completion"

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
                        elif model_id.startswith("ft:") and not (model_id.startswith("ft:gpt-3.5-turbo") or model_id.startswith("ft:gpt-4")):
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
            user_id_info = f"user {current_user.id}" if current_user else "system key" # Should always have current_user here
            error_detail = f"OpenAI API Error ({e.status_code}) while listing models for {user_id_info}: {e.message or str(e)}"
            print(error_detail)
        except Exception as e:
            user_id_info = f"user {current_user.id}" if current_user else "system key"
            print(f"An unexpected error occurred when listing OpenAI models for {user_id_info}: {e}. Returning manually curated list if any.")

        sorted_models_list = sorted(processed_models, key=lambda x: (
            not x['name'].startswith("GPT-4"),
            not x['name'].startswith("GPT-3.5 Turbo (Chat)"),
            not x['name'].startswith("GPT-3.5 Turbo Instruct"),
            x['model_type'] != "chat",
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

    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user, db): # Added is_available check
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")

        print(f"DEBUG OPENAI_HB_TOC: Received sections_summary: {sections_summary}")
        # openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Removed

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

        # api_key parameter already removed from the call in the previous step
        generated_toc = await self._perform_chat_completion(selected_model, messages, temperature=0.3, max_tokens=1000)
        if not generated_toc:
            raise LLMGenerationError("OpenAI API call for Homebrewery TOC from sections succeeded but returned no usable content.")

        return generated_toc

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
        if not await self.is_available(current_user, db):
            raise LLMServiceUnavailableError("OpenAI service not available or not configured.")
        if not user_prompt:
            raise ValueError("User prompt cannot be empty for character response.")

        selected_model = self._get_model(model, use_chat_model=True)

        # Construct the persona and instruction for the LLM
        # Ensure character_notes are not excessively long for the system prompt.
        # A more sophisticated approach might summarize or truncate character_notes if they are very large.
        truncated_notes = (character_notes[:1000] + '...') if character_notes and len(character_notes) > 1000 else character_notes

        system_content = (
            f"You are embodying the character named '{character_name}'. "
            f"Your personality, background, and way of speaking are defined by the following notes: "
            f"'{truncated_notes if truncated_notes else 'A typically neutral character.'}' "
            f"Respond naturally as this character would. Do not break character. Do not mention that you are an AI."
        )

        messages = [
            {"role": "system", "content": system_content}
        ]

        # Add chat history
        if chat_history:
            for message in chat_history:
                role = "user" if message.speaker.lower() == "user" else "assistant"
                # If the AI/character spoke, it's 'assistant'
                # This also correctly maps if message.speaker == character_name
                messages.append({"role": role, "content": message.text})

        # Add the current user prompt
        messages.append({"role": "user", "content": user_prompt})


        # Use a slightly higher temperature for more creative/natural character responses by default
        effective_temperature = temperature if temperature is not None else 0.75

        return await self._perform_chat_completion(
            selected_model,
            messages,
            temperature=effective_temperature,
            max_tokens=max_tokens or 300
        )
