from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

class LLMServiceUnavailableError(Exception):
    """Custom exception for when an LLM service cannot be initialized or is unavailable."""
    pass

class LLMGenerationError(Exception):
    """Custom exception for errors during LLM content generation attempts."""
    pass

class AbstractLLMService(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Generates text using an LLM based on a generic prompt.
        This is a general-purpose method. Specific generation tasks might have dedicated methods.
        The 'model' parameter is the specific model ID for the provider (e.g., "gpt-3.5-turbo" for OpenAI).
        """
        pass

    @abstractmethod
    def generate_campaign_concept(self, user_prompt: str, db: Session, model: Optional[str] = None) -> str:
        """
        Generates a campaign concept using an LLM based on a user prompt.
        The 'model' parameter is the specific model ID for the provider.
        """
        pass

    @abstractmethod
    def generate_titles(self, campaign_concept: str, db: Session, count: int = 5, model: Optional[str] = None) -> list[str]:
        """
        Generates a list of alternative campaign titles based on a campaign concept.
        The 'model' parameter is the specific model ID for the provider.
        """
        pass

    @abstractmethod
    def generate_toc(self, campaign_concept: str, db: Session, model: Optional[str] = None) -> Dict[str, str]:
            # Docstring should be updated to reflect it returns a dict with "display_toc" and "homebrewery_toc"
            """
            Generates both a display-friendly and a Homebrewery-formatted Table of Contents
            for a campaign based on its concept.
            Returns a dictionary with keys "display_toc" and "homebrewery_toc".
            """
            pass

    @abstractmethod
    def generate_section_content(
        self, 
        campaign_concept: str, 
        db: Session,
        existing_sections_summary: Optional[str], 
        section_creation_prompt: Optional[str], 
        section_title_suggestion: Optional[str], 
        model: Optional[str] = None,
        section_type: Optional[str] = None # New parameter
    ) -> str:
        """
        Generates content for a new campaign section.
        'section_type' can be used to tailor the generation (e.g., "NPC", "Location").
        The 'model' parameter is the specific model ID for the provider.
        """
        pass

    @abstractmethod
    def list_available_models(self) -> List[Dict[str, str]]:
        """
        Lists available LLM models for the specific provider.
        Returns a list of dicts, e.g., [{"id": "model_id_for_provider", "name": "Model Name"}]
        The 'id' should be usable in the 'model' parameter of generation methods.
        """
        pass

    def is_available(self) -> bool:
        """
        Checks if the service is configured and available for use (e.g., API key is set).
        Provides a default implementation that can be overridden if more complex checks are needed.
        """
        return True # Base implementation assumes availability if instantiated.
                    # Concrete classes should override if they have specific checks (e.g. API key presence).

# --- ADD THIS CONCRETE IMPLEMENTATION BELOW ---

class LLMService(AbstractLLMService):
    def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str:
        return f"Generated text for prompt: {prompt}"

    def generate_campaign_concept(self, user_prompt: str, db: Session, model: Optional[str] = None) -> str:
        return f"Campaign concept for: {user_prompt}"

    def generate_titles(self, campaign_concept: str, db: Session, count: int = 5, model: Optional[str] = None) -> list[str]:
        return [f"Title {i+1} for {campaign_concept}" for i in range(count)]

    def generate_toc(self, campaign_concept: str, db: Session, model: Optional[str] = None) -> Dict[str, str]:
            return {
                "display_toc": f"Display Table of Contents for: {campaign_concept}",
                "homebrewery_toc": f"Homebrewery Table of Contents for: {campaign_concept}"
            }

    def generate_section_content(
        self,
        campaign_concept: str,
        db: Session,
        existing_sections_summary: Optional[str],
        section_creation_prompt: Optional[str],
        section_title_suggestion: Optional[str],
        model: Optional[str] = None,
        section_type: Optional[str] = None # New parameter
    ) -> str:
        # Basic demonstration of using section_type.
        # In a real implementation, this would involve more sophisticated prompt engineering.
        if section_type:
            return f"Section content for: {campaign_concept} (Type: {section_type}) - Title: {section_title_suggestion}"
        return f"Section content for: {campaign_concept} - Title: {section_title_suggestion}"

    def list_available_models(self) -> List[Dict[str, str]]:
        return [
            {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            {"id": "openai/gpt-4", "name": "GPT-4"},
        ]
