from google import genai
from google.genai import types
import re
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app import models, orm_models
from app.models import User as UserModel
from pathlib import Path
import asyncio


class GeminiLLMService(AbstractLLMService):
    PROVIDER_NAME = "gemini"
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.effective_api_key = self.api_key
        if not self.effective_api_key:
            self.effective_api_key = settings.GEMINI_API_KEY

        self.configured_successfully = False
        self.client: Optional[genai.Client] = None
        
        if self.effective_api_key and self.effective_api_key != "YOUR_GEMINI_API_KEY":
            try:
                self.client = genai.Client(api_key=self.effective_api_key)
                self.configured_successfully = True
            except Exception as e:
                print(f"Error configuring Gemini client during __init__ with effective_api_key: {e}")
        else:
            print("Warning: Gemini API key (user or system) not configured or is a placeholder.")

        self.feature_prompt_service = FeaturePromptService()

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        if not self.configured_successfully or not self.client:
            return False
        try:
            # Quick test call with minimal tokens
            response = self.client.models.generate_content(
                model=self.DEFAULT_MODEL,
                contents="test",
                config=types.GenerateContentConfig(
                    candidate_count=1,
                    max_output_tokens=1
                )
            )
            return True
        except Exception as e:
            print(f"Gemini service not available. API check failed (using effective_api_key): {e}")
            return False

    def _get_model_id(self, model_id: Optional[str] = None) -> str:
        """Get the effective model ID to use."""
        effective_model_id = model_id or self.DEFAULT_MODEL
        if not effective_model_id or not effective_model_id.strip():
            effective_model_id = self.DEFAULT_MODEL
        return effective_model_id

    async def generate_text(
        self,
        prompt: str,
        current_user: UserModel,
        db: Session,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        model_id = self._get_model_id(model)
        
        config_params: Dict[str, Any] = {}
        if temperature is not None:
            config_params["temperature"] = max(0.0, min(temperature, 1.0))
        if max_tokens is not None:
            config_params["max_output_tokens"] = max_tokens

        try:
            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params) if config_params else None
            )

            if response.text:
                return response.text
            elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                return "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            else:
                error_details = "Unknown reason for empty content."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    error_details = f"Prompt feedback: {response.prompt_feedback}"
                elif not response.candidates:
                    error_details = "No candidates returned in response."
                raise LLMServiceUnavailableError(
                    f"Gemini API call succeeded but returned no usable content. Model: {model_id}. Details: {error_details}"
                )
        except Exception as e:
            print(f"Gemini API error (model: {model_id}): {type(e).__name__} - {e}")
            raise LLMServiceUnavailableError(
                f"Failed to generate text with Gemini model {model_id} due to API error: {str(e)}"
            ) from e

    async def generate_campaign_concept(
        self,
        user_prompt: str,
        db: Session,
        current_user: UserModel,
        model: Optional[str] = None
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        model_id = self._get_model_id(model)
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt_template.format(user_prompt=user_prompt) if custom_prompt_template else \
            f"Generate a detailed and engaging RPG campaign concept based on this idea: {user_prompt}. Include potential plot hooks, key NPCs, and unique settings."

        return await self.generate_text(
            prompt=final_prompt,
            current_user=current_user,
            db=db,
            model=model_id,
            temperature=0.7,
            max_tokens=1000
        )

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

    async def generate_toc(
        self,
        campaign_concept: str,
        db: Session,
        current_user: UserModel,
        model: Optional[str] = None
    ) -> List[Dict[str, str]]:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")

        model_id = self._get_model_id(model)

        display_prompt_template_str = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template_str:
            raise LLMGenerationError("Display TOC prompt template ('TOC Display') not found in database for Gemini.")

        try:
            display_final_prompt = display_prompt_template_str.format(campaign_concept=campaign_concept)
        except KeyError:
            print(f"ERROR: Gemini formatting 'TOC Display' prompt failed due to KeyError.")
            raise LLMGenerationError("Failed to format 'TOC Display' prompt due to unexpected placeholders for Gemini.")

        raw_toc_string = await self.generate_text(
            prompt=display_final_prompt,
            current_user=current_user,
            db=db,
            model=model_id,
            temperature=0.5,
            max_tokens=700
        )
        if not raw_toc_string:
            raise LLMGenerationError(f"Gemini API call for Display TOC (model: {model_id}) succeeded but returned no usable content.")

        return self._parse_toc_string_with_types(raw_toc_string)

    async def generate_titles(
        self,
        campaign_concept: str,
        db: Session,
        current_user: UserModel,
        count: int = 5,
        model: Optional[str] = None
    ) -> List[str]:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")

        model_id = self._get_model_id(model)
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names", db=db)
        final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count) if custom_prompt_template else \
            f"Based on the following RPG campaign concept: '{campaign_concept}', generate {count} alternative, catchy campaign titles. List each title on a new line. Ensure only the titles are listed, nothing else."

        text_response = await self.generate_text(
            prompt=final_prompt,
            current_user=current_user,
            db=db,
            model=model_id,
            temperature=0.7,
            max_tokens=150 + (count * 20)
        )
        titles = [title.strip() for title in text_response.split('\n') if title.strip()]
        return titles[:count]


    async def generate_section_content(
        self,
        db_campaign: orm_models.Campaign,
        db: Session,
        current_user: UserModel,
        existing_sections_summary: Optional[str],
        section_creation_prompt: Optional[str],
        section_title_suggestion: Optional[str],
        model: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        campaign_concept = db_campaign.concept
        if not campaign_concept:
            campaign_concept = "A new creative piece."

        model_id = self._get_model_id(model)
        effective_section_prompt = section_creation_prompt
        type_based_instruction = ""

        if section_type and section_type.lower() not in ["generic", "unknown", "", None]:
            title_str = section_title_suggestion or "the current section"
            if section_type.lower() in ["npc", "character"]:
                type_based_instruction = f"This section is about an NPC or character named '{title_str}'. Generate a detailed description including appearance, personality, motivations, potential plot hooks, and if appropriate, a basic stat block suitable for a tabletop RPG."
            elif section_type.lower() == "location":
                type_based_instruction = f"This section describes a location: '{title_str}'. Detail its key features, atmosphere, inhabitants (if any), notable points of interest, secrets, and potential encounters."
            elif section_type.lower() in ["chapter", "quest"]:
                type_based_instruction = f"This section outlines a chapter or quest titled '{title_str}'. Describe the main events, objectives, challenges, potential rewards, and any key NPCs or locations involved."
            else:
                type_based_instruction = f"This section is specifically about '{title_str}' which is a '{section_type}'. Generate detailed content appropriate for this type."

        if not effective_section_prompt and type_based_instruction:
            effective_section_prompt = type_based_instruction
        elif effective_section_prompt and type_based_instruction:
            effective_section_prompt = f"{type_based_instruction}\n\nFurther specific instructions for this section: {section_creation_prompt}"
        elif not effective_section_prompt:
            effective_section_prompt = "Continue the story logically, introducing new elements or developing existing ones."

        # Character Information Injection
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

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content", db=db)
        final_prompt_for_generation: str

        if custom_prompt_template:
            try:
                final_prompt_for_generation = custom_prompt_template.format(
                    campaign_concept=campaign_concept,
                    existing_sections_summary=existing_sections_summary or "N/A",
                    section_creation_prompt=effective_section_prompt,
                    section_title_suggestion=section_title_suggestion or "Next Part",
                    campaign_characters=campaign_characters_formatted
                )
            except KeyError as e:
                print(f"Warning: Prompt template 'Section Content' is missing a key: {e}. Falling back to default prompt structure.")
                final_prompt_for_generation = (
                    f"Campaign Concept: {campaign_concept}\n"
                    f"Relevant Characters in this Campaign:\n{campaign_characters_formatted}\n\n"
                    f"Summary of existing sections: {existing_sections_summary or 'N/A'}\n"
                    f"Instruction for new section (titled '{section_title_suggestion or 'Next Part'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"
                )
        else:
            final_prompt_for_generation = (
                f"Campaign Concept: {campaign_concept}\n"
                f"Relevant Characters in this Campaign:\n{campaign_characters_formatted}\n\n"
            )
            if existing_sections_summary:
                final_prompt_for_generation += f"Summary of existing sections: {existing_sections_summary}\n"
            final_prompt_for_generation += f"Instruction for new section (titled '{section_title_suggestion or 'Next Part'}', Type: '{section_type or 'Generic'}'): {effective_section_prompt}"

        return await self.generate_text(
            prompt=final_prompt_for_generation,
            current_user=current_user,
            db=db,
            model=model_id,
            temperature=0.7,
            max_tokens=4000
        )

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, Any]]:
        if not await self.is_available(current_user=current_user, db=db):
            print("Warning: Gemini API key not configured or service unavailable. Cannot fetch models.")
            fallback_models = [
                {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Unavailable/Fallback)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Unavailable/Fallback)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat"]},
            ]
            return fallback_models

        available_models: List[Dict[str, Any]] = []
        try:
            print("Fetching available models from Gemini API...")
            api_models = self.client.models.list()
            
            for m in api_models:
                # Filter for models that support generateContent
                supported_methods = getattr(m, 'supported_generation_methods', []) or []
                if 'generateContent' in supported_methods:
                    model_id = m.name.split('/')[-1] if '/' in m.name else m.name
                    display_name = getattr(m, 'display_name', model_id)

                    model_type = "chat"
                    supports_temperature = True
                    capabilities = ["chat"]

                    if "vision" in model_id.lower() or "vision" in display_name.lower():
                        capabilities.append("vision")

                    available_models.append({
                        "id": model_id,
                        "name": display_name,
                        "model_type": model_type,
                        "supports_temperature": supports_temperature,
                        "capabilities": capabilities
                    })

            if not available_models:
                print("Warning: Gemini API returned no models supporting 'generateContent'. Using hardcoded list as fallback.")
                raise Exception("No suitable models found from API")

        except Exception as e:
            print(f"Could not dynamically fetch models from Gemini API: {e}. Using a hardcoded list as fallback.")
            available_models = [
                {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"]},
                {"id": "gemini-1.5-pro-latest", "name": "Gemini 1.5 Pro (Latest)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"]},
                {"id": "gemini-1.5-flash-latest", "name": "Gemini 1.5 Flash (Latest)", "model_type": "chat", "supports_temperature": True, "capabilities": ["chat", "vision"]},
            ]
            default_model_id = self.DEFAULT_MODEL
            if not any(m['id'] == default_model_id for m in available_models):
                available_models.insert(0, {
                    "id": default_model_id,
                    "name": default_model_id.replace("-", " ").title() + " (Default)",
                    "model_type": "chat",
                    "supports_temperature": True,
                    "capabilities": ["chat", "vision"] if "vision" in default_model_id else ["chat"]
                })

        available_models.sort(key=lambda x: (
            "latest" not in x["id"],
            "2.0" not in x["id"],
            "pro" not in x["id"],
            "flash" not in x["id"],
            x["name"]
        ))
        return available_models

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # The new google-genai SDK doesn't require explicit client closing
        pass

    async def generate_homebrewery_toc_from_sections(
        self,
        sections_summary: str,
        db: Session,
        current_user: UserModel,
        model: Optional[str] = None
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        if not sections_summary:
            return "{{toc,wide\n# Table Of Contents\n}}\n"

        model_id = self._get_model_id(model)

        prompt_template_str = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not prompt_template_str:
            raise LLMGenerationError("Homebrewery TOC prompt template ('TOC Homebrewery') not found in database for Gemini.")

        final_prompt = prompt_template_str.format(sections_summary=sections_summary)

        generated_toc = await self.generate_text(
            prompt=final_prompt,
            current_user=current_user,
            db=db,
            model=model_id,
            temperature=0.3,
            max_tokens=1000
        )
        if not generated_toc:
            raise LLMGenerationError(f"Gemini API call for Homebrewery TOC from sections (model: {model_id}) succeeded but returned no usable content.")

        return generated_toc


    async def generate_image(
        self,
        prompt: str,
        current_user: UserModel,
        db: Session,
        model: Optional[str] = "gemini-2.0-flash",
        size: Optional[str] = None
    ) -> bytes:
        """
        Generates an image based on the given prompt using Gemini.
        Note: Image generation capabilities depend on the model used.
        """
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")

        if not prompt:
            raise ValueError("Prompt cannot be empty for image generation.")

        model_id = self._get_model_id(model)

        try:
            print(f"Attempting to generate image with model: {model_id} using prompt: '{prompt[:50]}...'")

            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt
            )

            # Process the response to extract image bytes
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                        return part.inline_data.data

            error_message = "Gemini API call for image generation succeeded but returned no image data."
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                error_message += f" Prompt feedback: {response.prompt_feedback}"
            if not response.candidates:
                error_message += " No candidates were generated."
            raise LLMGenerationError(error_message)

        except LLMGenerationError:
            raise
        except LLMServiceUnavailableError:
            raise
        except Exception as e:
            print(f"Error during Gemini image generation (model: {model_id}): {type(e).__name__} - {e}")
            raise LLMGenerationError(f"Failed to generate image with Gemini model {model_id}: {e}") from e

    async def generate_character_response(
        self,
        character_name: str,
        character_notes: str,
        user_prompt: str,
        current_user: UserModel,
        db: Session,
        chat_history: Optional[List[models.ConversationMessageContext]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 300
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError("Gemini service is not available.")
        if not user_prompt:
            raise ValueError("User prompt cannot be empty for character response.")

        model_id = self._get_model_id(model)
        truncated_notes = (character_notes[:1000] + '...') if character_notes and len(character_notes) > 1000 else character_notes

        effective_temperature = temperature if temperature is not None else 0.75
        effective_max_tokens = max_tokens or 300

        config_params: Dict[str, Any] = {}
        if effective_temperature is not None:
            config_params["temperature"] = max(0.0, min(effective_temperature, 1.0))
        if effective_max_tokens is not None:
            config_params["max_output_tokens"] = effective_max_tokens

        generation_config = types.GenerateContentConfig(**config_params) if config_params else None

        if chat_history:
            # Build contents for multi-turn chat
            contents = []

            # Initial context setting for the character
            initial_context = (
                f"You are embodying the character named '{character_name}'. "
                f"Your personality, background, and way of speaking are defined by the following notes: "
                f"'{truncated_notes if truncated_notes else 'A typically neutral character.'}' "
                f"Respond naturally as this character would. Do not break character. Do not mention that you are an AI. "
                f"The conversation starts now."
            )

            contents.append({"role": "user", "parts": [{"text": initial_context}]})
            contents.append({"role": "model", "parts": [{"text": f"Understood. I am {character_name}. I will respond according to these instructions."}]})

            for message in chat_history:
                role = "user" if message.speaker.lower() == "user" else "model"
                contents.append({"role": role, "parts": [{"text": message.text}]})

            # Add the current user prompt
            contents.append({"role": "user", "parts": [{"text": user_prompt}]})

            try:
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=generation_config
                )

                if response.text:
                    return response.text
                elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    return "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                else:
                    raise LLMGenerationError(f"Gemini API call (character response with history) succeeded but returned no usable content. Model: {model_id}")
            except Exception as e:
                print(f"Gemini API error (character response with history, model: {model_id}): {type(e).__name__} - {e}")
                raise LLMGenerationError(f"Failed to generate character response with Gemini (history) model {model_id}: {str(e)}") from e

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
                model=model_id,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens
            )


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    env_path_api_root = Path(__file__).resolve().parent.parent.parent / ".env"
    env_path_monorepo_root = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path_api_root.exists():
        load_dotenv(dotenv_path=env_path_api_root)
    elif env_path_monorepo_root.exists():
        load_dotenv(dotenv_path=env_path_monorepo_root)
    else:
        print(f"Warning: .env file not found. Service might not initialize correctly.")

    class DummyUser(UserModel):
        id: int = 1
        username: str = "testuser"
        email: Optional[str] = "test@example.com"
        full_name: Optional[str] = "Test User"
        disabled: bool = False
        is_superuser: bool = False
        openai_api_key_provided: bool = False
        sd_api_key_provided: bool = False
        gemini_api_key_provided: bool = False
        other_llm_api_key_provided: bool = False
        campaigns = []
        llm_configs = []
        roll_tables = []

    mock_user = DummyUser()
    mock_db_session: Optional[Session] = None

    async def main_test():
        system_gemini_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        settings.GEMINI_API_KEY = system_gemini_key

        print(f"Attempting to initialize GeminiLLMService with system key: ...{system_gemini_key[-4:] if system_gemini_key and system_gemini_key != 'YOUR_GEMINI_API_KEY' else 'Not Set or Placeholder'}")
        gemini_service = GeminiLLMService()

        is_available = await gemini_service.is_available(current_user=mock_user, db=mock_db_session)
        if not is_available:
            print("Skipping GeminiLLMService tests as GEMINI_API_KEY is not set or service is unavailable.")
            await gemini_service.close()
            return

        print("GeminiLLMService is available.")

        try:
            print("\n--- Testing Generic Text Generation ---")
            generic_text = await gemini_service.generate_text(
                prompt="Tell me a short story about a robot learning to paint.",
                current_user=mock_user,
                db=mock_db_session,
                temperature=0.8,
                max_tokens=200
            )
            print("Generic Text Output (first 250 chars):", generic_text[:250] + "..." if generic_text else "No generic text generated.")

            print("\n--- Testing List Available Models ---")
            models_list = await gemini_service.list_available_models(current_user=mock_user, db=mock_db_session)
            for m in models_list[:5]:
                print(f"- {m['name']} (id: {m['id']})")

        except Exception as e:
            print(f"An error occurred during testing: {e}")
        finally:
            await gemini_service.close()

    asyncio.run(main_test())
