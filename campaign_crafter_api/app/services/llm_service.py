from abc import ABC, abstractmethod
from typing import Optional, List, Dict # Ensure Dict and List are imported

class LLMService(ABC):
    @abstractmethod
    def generate_campaign_concept(self, user_prompt: str, model: str = "gpt-3.5-turbo-instruct") -> str:
        """
        Generates a campaign concept using an LLM based on a user prompt.
        """
        pass

    @abstractmethod
    def generate_titles(self, campaign_concept: str, count: int = 5, model: str = "gpt-3.5-turbo-instruct") -> list[str]: # Or a newer default model
        """
        Generates a list of alternative campaign titles based on a campaign concept.
        """
        pass

    @abstractmethod
    def generate_toc(self, campaign_concept: str, model: str = "gpt-3.5-turbo-instruct") -> str: # Using a newer default
        """
        Generates a Table of Contents for a campaign based on its concept.
        """
        pass

    @abstractmethod
    def generate_section_content(self, campaign_concept: str, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: str = "gpt-3.5-turbo-instruct") -> str: # Updated default model
        """
        Generates content for a new campaign section.
        """
        pass

    @abstractmethod
    def list_available_models(self) -> List[Dict[str, str]]: # Returns a list of dicts, e.g., [{"id": "model_id", "name": "Model Name"}]
        """
        Lists available LLM models.
        """
        pass

    # Future methods can be added here, e.g.:
