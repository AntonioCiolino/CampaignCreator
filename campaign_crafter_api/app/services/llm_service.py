from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models import User as UserModel # Added UserModel import

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
    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str: # Changed signature
        """
        Generates text using an LLM based on a generic prompt.
        This is a general-purpose method. Specific generation tasks might have dedicated methods.
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
    async def generate_section_content( # Changed signature
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
        """
        Generates content for a new campaign section.
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

    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str:
        print(f"Dummy LLMService: generate_text called for user {current_user.id} with model {model}")
        return f"Dummy generated text for prompt: {prompt}"

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
        campaign_concept: str,
        db: Session,
        current_user: UserModel,
        existing_sections_summary: Optional[str],
        section_creation_prompt: Optional[str],
        section_title_suggestion: Optional[str],
        model: Optional[str] = None,
        section_type: Optional[str] = None
    ) -> str:
        print(f"Dummy LLMService: generate_section_content called for user {current_user.id} with model {model} and type {section_type}")
        if section_type:
            return f"Dummy section content for: {campaign_concept} (Type: {section_type}) - Title: {section_title_suggestion}"
        return f"Dummy section content for: {campaign_concept} - Title: {section_title_suggestion}"

    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        print(f"Dummy LLMService: generate_homebrewery_toc_from_sections called for user {current_user.id} with model {model}")
        if not sections_summary:
            return ""
        return f"Dummy Homebrewery TOC based on sections: {sections_summary}"
