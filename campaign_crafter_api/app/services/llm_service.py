from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app import models, orm_models # Changed import, Added orm_models import
from app.models import User as UserModel

class LLMServiceUnavailableError(Exception):
    """Custom exception for when an LLM service cannot be initialized or is unavailable."""
    pass

class LLMGenerationError(Exception):
    """Custom exception for errors during LLM content generation attempts."""
    pass

class AbstractLLMService(ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    async def is_available(self, current_user: UserModel, db: Session) -> bool: # Changed signature
        pass

    @abstractmethod
    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, str]]: # Changed signature
        """
        Lists available LLM models for the specific provider, considering user context.
        Returns a list of dicts, e.g., [{"id": "model_id_for_provider", "name": "Model Name"}]
        The 'id' should be usable in the 'model' parameter of generation methods.
        """
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        current_user: UserModel,
        db: Session,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        # Context fields for generic endpoint to become context-aware
        db_campaign: Optional[orm_models.Campaign] = None,
        section_title_suggestion: Optional[str] = None,
        section_type: Optional[str] = None
        # existing_sections_summary, campaign_concept, campaign_characters are derived from db_campaign if provided
    ) -> str:
        """
        Generates text using an LLM based on a generic prompt.
        Can become context-aware if db_campaign and other context fields are provided,
        allowing it to format the 'prompt' string if it contains placeholders.
        The 'model' parameter is the specific model ID for the provider (e.g., "gpt-3.5-turbo" for OpenAI).
        """
        pass

    @abstractmethod
    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str: # Changed signature
        """
        Generates a campaign concept using an LLM based on a user prompt.
        The 'model' parameter is the specific model ID for the provider.
        """
        pass

    @abstractmethod
    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]: # Changed signature
        """
        Generates a list of alternative campaign titles based on a campaign concept.
        The 'model' parameter is the specific model ID for the provider.
        """
        pass

    @abstractmethod
    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> List[Dict[str, str]]: # Changed signature
            """
            Generates a display-friendly Table of Contents for a campaign based on its concept,
            parses it, and returns a list of dictionaries, each with "title" and "type".
            Example: [{"title": "Chapter 1: The Beginning", "type": "chapter"}, {"title": "NPC: Elara", "type": "npc"}]
            """
            pass

    @abstractmethod
    async def generate_section_content(
        self, 
        db_campaign: orm_models.Campaign, # Changed: campaign_concept to db_campaign
        db: Session,
        current_user: UserModel,
        existing_sections_summary: Optional[str], 
        section_creation_prompt: Optional[str], 
        section_title_suggestion: Optional[str], 
        model: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        """
        Generates content for a new campaign section.
        Accepts the full Campaign ORM object to allow access to characters.
        'section_type' can be used to tailor the generation (e.g., "NPC", "Location").
        The 'model' parameter is the specific model ID for the provider.
        """
        pass

    @abstractmethod
    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        '''
        Generates a Homebrewery-formatted Table of Contents based on a summary of campaign sections.
        Returns the raw Homebrewery Markdown string.
        '''
        pass

    @abstractmethod
    async def generate_character_response(
        self,
        character_name: str,
        character_notes: str, # This will contain personality, background, etc.
        user_prompt: str,     # The query or situation the character should respond to
        current_user: UserModel,
        db: Session,
        chat_history: Optional[List[models.ChatMessage]] = None, # Corrected type hint
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 300 # Default to a moderate length for dialogue/response
    ) -> str:
        """
        Generates a response as if spoken or written by a specific character.
        Uses character_notes to inform the LLM about the character's persona.
        """
        pass

# --- Dummy LLMService for placeholder/testing, updated to match async and new signatures ---
class LLMService(AbstractLLMService): # Note: This is a dummy implementation
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        # print(f"Dummy LLMService initialized with API key: {'Provided' if api_key else 'Not Provided'}")

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        print(f"Dummy LLMService: is_available called for user {current_user.id}")
        return True

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, str]]:
        print(f"Dummy LLMService: list_available_models called for user {current_user.id}")
        return [
            {"id": "dummy/model-1", "name": "Dummy Model 1"},
            {"id": "dummy/model-2", "name": "Dummy Model 2"},
        ]

    async def generate_text(
        self,
        prompt: str,
        current_user: UserModel,
        db: Session,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        # Context fields
        db_campaign: Optional[orm_models.Campaign] = None,
        section_title_suggestion: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        formatted_prompt = prompt
        if db_campaign:
            # Simplified formatting for dummy service
            campaign_concept_str = db_campaign.concept or "N/A Concept"

            character_info_parts = []
            if db_campaign.characters:
                for char in db_campaign.characters:
                    char_details = f"Character: {char.name}"
                    if char.description: char_details += f" (Desc: {char.description[:20]}...)"
                    if char.notes_for_llm: char_details += f" (LLM Notes: {char.notes_for_llm[:20]}...)"
                    character_info_parts.append(char_details)
            campaign_characters_str = "\n".join(character_info_parts) if character_info_parts else "No characters."

            # Attempt to fill placeholders if they exist in the prompt template
            try:
                # Basic placeholder replacement attempt for the dummy
                # A real implementation would be more robust or use a templating engine carefully
                temp_prompt = prompt
                if "{campaign_concept}" in temp_prompt:
                    temp_prompt = temp_prompt.replace("{campaign_concept}", campaign_concept_str)
                if "{campaign_characters}" in temp_prompt:
                    temp_prompt = temp_prompt.replace("{campaign_characters}", campaign_characters_str)
                if "{section_title_suggestion}" in temp_prompt and section_title_suggestion:
                    temp_prompt = temp_prompt.replace("{section_title_suggestion}", section_title_suggestion)
                if "{title}" in temp_prompt and section_title_suggestion: # common alternative
                    temp_prompt = temp_prompt.replace("{title}", section_title_suggestion)
                if "{section_type}" in temp_prompt and section_type:
                    temp_prompt = temp_prompt.replace("{section_type}", section_type)
                if "{section_type_for_llm}" in temp_prompt and section_type: # common alternative
                    temp_prompt = temp_prompt.replace("{section_type_for_llm}", section_type)
                # existing_sections_summary would require DB query, skipping for dummy
                if "{existing_sections_summary}" in temp_prompt:
                    temp_prompt = temp_prompt.replace("{existing_sections_summary}", "Dummy sections summary.")
                formatted_prompt = temp_prompt
            except Exception as e:
                print(f"Dummy LLMService: Error trying to format prompt - {e}")
                # Keep original prompt if formatting fails

        print(f"Dummy LLMService: generate_text called for user {current_user.id} with model {model}. Campaign ID: {db_campaign.id if db_campaign else 'N/A'}")
        if prompt != formatted_prompt:
            print(f"Dummy LLMService: Original prompt was: '{prompt[:100]}...'")
            print(f"Dummy LLMService: Formatted prompt is: '{formatted_prompt[:100]}...'")
        return f"Dummy generated text for prompt: {formatted_prompt}"

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        print(f"Dummy LLMService: generate_campaign_concept called for user {current_user.id} with model {model}")
        return f"Dummy campaign concept for: {user_prompt}"

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]:
        print(f"Dummy LLMService: generate_titles called for user {current_user.id} with model {model}")
        return [f"Dummy Title {i+1} for {campaign_concept}" for i in range(count)]

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> List[Dict[str, str]]:
        print(f"Dummy LLMService: generate_toc called for user {current_user.id} with model {model}")
        return [
            {"title": f"Dummy Section 1 for {campaign_concept}", "type": "generic"},
            {"title": "Dummy NPC Section", "type": "npc"}
        ]

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
        campaign_concept = db_campaign.concept if db_campaign else "Unknown Campaign Concept"
        characters_info = "No character info available."
        if db_campaign and db_campaign.characters:
            characters_info = f"{len(db_campaign.characters)} characters in campaign."

        print(f"Dummy LLMService: generate_section_content called for user {current_user.id}, campaign ID {db_campaign.id if db_campaign else 'N/A'}, model {model}, type {section_type}. Characters: {characters_info}")

        base_response = f"Dummy section content for: {campaign_concept} - Title: {section_title_suggestion}."
        if section_type:
            base_response += f" (Type: {section_type})"
        if db_campaign and db_campaign.characters:
            base_response += f" (Aware of {len(db_campaign.characters)} characters)."
        return base_response

    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        print(f"Dummy LLMService: generate_homebrewery_toc_from_sections called for user {current_user.id} with model {model}")
        if not sections_summary:
            return ""
        return f"Dummy Homebrewery TOC based on sections: {sections_summary}"

    async def generate_character_response(
        self,
        character_name: str,
        character_notes: str,
        user_prompt: str,
        current_user: UserModel,
        db: Session,
        chat_history: Optional[List[models.ChatMessage]] = None, # Corrected type hint
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 300
    ) -> str:
        print(f"Dummy LLMService: generate_character_response called for character '{character_name}' by user {current_user.id} with model {model}")

        messages = []
        # System message incorporating character_notes
        system_message = f"You are {character_name}. Your personality and background are: {character_notes}. Respond to the user's last message as {character_name}."
        messages.append({"role": "system", "content": system_message})

        if chat_history:
            for message in chat_history:
                role = "user" if message.speaker == "user" else "assistant"
                # If speaker is the character_name, it's still 'assistant' from LLM's perspective
                if message.speaker == character_name:
                    role = "assistant"
                messages.append({"role": role, "content": message.text})

        # Current user prompt
        messages.append({"role": "user", "content": user_prompt})

        print(f"Constructed messages for LLM: {messages}")

        # Dummy response generation
        response_text = (
            f"As {character_name}, responding to '{user_prompt}' (after reviewing history if any): "
            f"'This is a dummy response from {self.__class__.__name__} considering the context. My instructions started with: {system_message[:100]}...'"
        )
        if chat_history:
            response_text += f" I recall {len(chat_history)} past messages."

        return response_text
