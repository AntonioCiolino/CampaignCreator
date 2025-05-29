import google.generativeai as genai # type: ignore
from typing import List, Dict, Optional
from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.feature_prompt_service import FeaturePromptService

class GeminiLLMService(LLMService):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.")
        
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            # This could be due to various reasons, including invalid API key format
            # or issues with the google.auth library if it's used implicitly by genai.configure
            raise ValueError(f"Failed to configure Gemini client, possibly due to API key issue: {e}")

        self.feature_prompt_service = FeaturePromptService()
        # Example: Initialize a specific model if all methods use the same one by default
        # self.model_instance = genai.GenerativeModel('gemini-pro') # Or a specific model string from input

    def _get_model_instance(self, model_id: str = "gemini-pro"):
        # Helper to get a model instance, allowing for different models per call if needed
        # The model_id here is the part after "gemini/", e.g., "gemini-pro"
        # If the full prefixed ID is passed, strip it.
        if model_id.startswith("gemini/"):
            model_id = model_id.split("/", 1)[1]
        
        # Basic safety check for model_id, though Gemini SDK might have its own validation
        if not model_id or not model_id.strip():
            model_id = "gemini-pro" # Fallback to a default if empty/whitespace

        try:
            return genai.GenerativeModel(model_id)
        except Exception as e:
            # This can catch errors if the model_id is invalid or not supported
            raise ValueError(f"Failed to initialize Gemini model '{model_id}': {e}")


    def generate_campaign_concept(self, user_prompt: str, model: str = "gemini/gemini-pro") -> str:
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(user_prompt=user_prompt)
        else:
            print("Warning: 'Campaign' prompt not found in features.csv. Using default prompt for Gemini.")
            final_prompt = f"Generate a detailed and engaging RPG campaign concept based on this idea: {user_prompt}. Include potential plot hooks, key NPCs, and unique settings."
        
        try:
            response = model_instance.generate_content(final_prompt)
            if response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif response.text: # Fallback if .parts is not the way or empty but .text exists
                 return response.text
            else: # Handle cases where the response structure might be unexpected or empty
                 raise Exception("Gemini API call succeeded but returned no usable content (no parts or text).")

        except Exception as e:
            print(f"Gemini API error during campaign concept generation: {e}")
            raise Exception(f"Failed to generate campaign concept due to Gemini API error: {str(e)}") from e

    def generate_toc(self, campaign_concept: str, model: str = "gemini/gemini-pro") -> str:
        model_instance = self._get_model_instance(model)
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Table of Contents")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept)
        else:
            print("Warning: 'Table of Contents' prompt not found in features.csv. Using default prompt for Gemini.")
            final_prompt = f"""Based on the following RPG campaign concept, generate a hierarchical Table of Contents.
Campaign Concept:
{campaign_concept}

Return only the Table of Contents. Example:
Part 1: Title
  Chapter 1: Subtitle
  Chapter 2: Subtitle
Part 2: Title
  Chapter 3: Subtitle"""
        
        try:
            response = model_instance.generate_content(final_prompt)
            if response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif response.text:
                 return response.text
            else:
                 raise Exception("Gemini API call for TOC succeeded but returned no usable content.")
        except Exception as e:
            print(f"Gemini API error during TOC generation: {e}")
            raise Exception(f"Failed to generate TOC due to Gemini API error: {str(e)}") from e

    def generate_titles(self, campaign_concept: str, count: int = 5, model: str = "gemini/gemini-pro") -> List[str]:
        model_instance = self._get_model_instance(model)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count)
        else:
            print("Warning: 'Campaign Names' prompt not found in features.csv. Using default prompt for Gemini.")
            final_prompt = f"""Based on the following RPG campaign concept, generate {count} alternative campaign titles.
Campaign Concept:
{campaign_concept}
Return only the {count} titles, each on a new line. Do not include numbering or any other surrounding text."""

        try:
            response = model_instance.generate_content(final_prompt)
            text_response = ""
            if response.parts:
                 text_response = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif response.text:
                 text_response = response.text
            else:
                 raise Exception("Gemini API call for titles succeeded but returned no usable content.")

            titles = [title.strip() for title in text_response.split('\n') if title.strip()]
            return titles[:count]
        except Exception as e:
            print(f"Gemini API error during title generation: {e}")
            raise Exception(f"Failed to generate titles due to Gemini API error: {str(e)}") from e

    def generate_section_content(self, campaign_concept: str, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: str = "gemini/gemini-pro") -> str:
        model_instance = self._get_model_instance(model)

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=section_creation_prompt or "Continue the story logically.",
                section_title_suggestion=section_title_suggestion or "Untitled Section"
            )
        else:
            print("Warning: 'Section Content' prompt not found in features.csv. Using default prompt for Gemini.")
            prompt_parts = ["You are writing a new section for a tabletop role-playing game campaign."]
            prompt_parts.append(f"The overall campaign concept is:\n{campaign_concept}\n")
            if existing_sections_summary:
                prompt_parts.append(f"So far, the campaign includes these sections (titles or brief summaries):\n{existing_sections_summary}\n")
            if section_title_suggestion:
                prompt_parts.append(f"The suggested title for this new section is: {section_title_suggestion}\n")
            if section_creation_prompt:
                prompt_parts.append(f"The specific instructions or starting prompt for this section are: {section_creation_prompt}\n")
            else:
                prompt_parts.append("Please write the next logical section for this campaign.\n")
            prompt_parts.append("Generate detailed and engaging content for this new section.")
            final_prompt = "\n".join(prompt_parts)
        
        try:
            response = model_instance.generate_content(final_prompt)
            if response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif response.text:
                 return response.text
            else:
                 raise Exception("Gemini API call for section content succeeded but returned no usable content.")
        except Exception as e:
            print(f"Gemini API error during section content generation: {e}")
            raise Exception(f"Failed to generate section content due to Gemini API error: {str(e)}") from e

    def list_available_models(self) -> List[Dict[str, str]]:
        # Gemini API has a models.list() but it can be extensive.
        # For now, returning a curated list of commonly used text generation models.
        # Prefixed with "gemini/" for the factory.
        # In a real scenario, you might want to filter models.list() by supported generation methods.
        
        # Example: genai.list_models() returns Model objects
        # for m in genai.list_models():
        #   if 'generateContent' in m.supported_generation_methods:
        #     print(m.name, m.display_name) # e.g. models/gemini-pro, Gemini Pro
        
        # Hardcoded list for now, assuming these are generally available and suitable.
        # The 'id' should be what the Gemini SDK expects (e.g., 'gemini-pro', not 'models/gemini-pro' directly for GenerativeModel())
        # But the factory will expect the prefix.
        return [
            {"id": "gemini/gemini-pro", "name": "Gemini Pro"},
            {"id": "gemini/gemini-1.0-pro", "name": "Gemini 1.0 Pro"}, # Example if specific versions are listed
            # Add other relevant models if known, e.g., gemini-pro-vision if handling multimodal
        ]

    def is_available(self) -> bool:
        return bool(self.api_key)

# Dummy .env for testing if run directly (not needed for agent execution)
# DATABASE_URL=...
# OPENAI_API_KEY=...
# GEMINI_API_KEY=your_key_here

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    
    # Load .env from the project root if this script is run directly for testing
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=project_root / ".env")
    
    # Update settings object if you want to test with loaded .env values
    # This is a bit hacky for direct script run; in app, FastAPI handles settings.
    settings.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    settings.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


    if not settings.GEMINI_API_KEY:
        print("Skipping GeminiLLMService tests as GEMINI_API_KEY is not set in .env")
    else:
        print(f"Attempting to initialize GeminiLLMService with key: ...{settings.GEMINI_API_KEY[-4:] if settings.GEMINI_API_KEY else 'None'}")
        try:
            gemini_service = GeminiLLMService()
            print("GeminiLLMService Initialized.")

            print("\nAvailable Gemini Models:")
            models = gemini_service.list_available_models()
            for m in models:
                print(f"- {m['name']} ({m['id']})")

            if models:
                test_model = models[0]['id'] # Use the first available model for tests
                print(f"\nUsing model: {test_model} for generation tests...")

                print("\n--- Testing Campaign Concept Generation ---")
                concept = gemini_service.generate_campaign_concept("A group of adventurers find a mysterious portal in an ancient library.", model=test_model)
                print("Concept:", concept[:150] + "..." if concept else "No concept generated.")

                if concept:
                    print("\n--- Testing TOC Generation ---")
                    toc = gemini_service.generate_toc(concept, model=test_model)
                    print("TOC:", toc[:150] + "..." if toc else "No TOC generated.")

                    print("\n--- Testing Titles Generation ---")
                    titles = gemini_service.generate_titles(concept, count=3, model=test_model)
                    print("Titles:", titles)

                    print("\n--- Testing Section Content Generation ---")
                    section_content = gemini_service.generate_section_content(
                        campaign_concept=concept,
                        existing_sections_summary="Chapter 1: The Portal. Chapter 2: First Steps into Another World.",
                        section_creation_prompt="The adventurers encounter a strange, glowing creature.",
                        section_title_suggestion="Chapter 3: The Glow",
                        model=test_model
                    )
                    print("Section Content:", section_content[:150] + "..." if section_content else "No section content generated.")
            else:
                print("No Gemini models listed, skipping generation tests.")

        except ValueError as ve:
            print(f"Error initializing or using GeminiLLMService: {ve}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

```
