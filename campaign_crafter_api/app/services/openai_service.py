import openai # type: ignore
from typing import Optional, List, Dict # Ensure these are imported if not already
from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.feature_prompt_service import FeaturePromptService # Import the new service

class OpenAILLMService(LLMService):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.")
        openai.api_key = self.api_key
        self.feature_prompt_service = FeaturePromptService() # Instantiate the prompt service

    def generate_campaign_concept(self, user_prompt: str, model: str = "gpt-3.5-turbo-instruct") -> str:
        """
        Generates a campaign concept using OpenAI's API based on a user prompt.
        """
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(user_prompt=user_prompt)
        else:
            print("Warning: 'Campaign' prompt not found in features.csv. Using default prompt.")
            final_prompt = f"Generate a detailed campaign concept, including potential plot hooks and key NPCs, based on the following idea: {user_prompt}"
        
        try:
            # Note: The 'Completion' endpoint is for older models like text-davinci-003 or gpt-3.5-turbo-instruct.
            # For newer chat models (gpt-3.5-turbo, gpt-4), you'd use openai.ChatCompletion.create()
            # and structure the prompt as a list of messages.
            if model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]: # Example chat models
                 response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a creative assistant helping to brainstorm RPG campaign concepts."},
                        {"role": "user", "content": prompt_template}
                    ],
                    temperature=0.7,
                    max_tokens=1000 # Adjust as needed
                )
                 if response.choices and response.choices[0].message:
                    return response.choices[0].message.content.strip()
                 else:
                    raise Exception("OpenAI API call succeeded but returned no content.")

            else: # Assuming older completion models like gpt-3.5-turbo-instruct
                response = openai.Completion.create(
                    engine=model,  # Or 'model=model' for newer versions of the library
                    prompt=final_prompt, # Use the potentially customized prompt
                    temperature=0.7,
                    max_tokens=1000,  # Adjust as needed
                    n=1,
                    stop=None
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
                else:
                    raise Exception("OpenAI API call succeeded but returned no content.")

        except openai.error.OpenAIError as e:
            # Handle specific OpenAI errors or re-raise a custom one
            # For example, log e.http_status, e.error
            print(f"OpenAI API error: {e}")
            raise Exception(f"Failed to generate campaign concept due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM concept generation: {e}")
            raise Exception(f"An unexpected error occurred: {str(e)}") from e

    def generate_toc(self, campaign_concept: str, model: str = "gpt-3.5-turbo-instruct") -> str:
        """
        Generates a Table of Contents for a campaign based on its concept using OpenAI.
        """
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty when generating a Table of Contents.")

        custom_prompt_template = self.feature_prompt_service.get_prompt("Table of Contents")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept)
        else:
            print("Warning: 'Table of Contents' prompt not found in features.csv. Using default prompt.")
            final_prompt = f"""Based on the following campaign concept, generate a hierarchical Table of Contents suitable for a tabletop role-playing game campaign. The Table of Contents should outline the main parts, chapters, or adventures of the campaign.

Campaign Concept:
{campaign_concept}

Return only the Table of Contents. For example:
Part 1: Introduction
  Chapter 1: The Beginning
  Chapter 2: The Plot Thickens
Part 2: Rising Action
  Chapter 3: A New Challenge
  Chapter 4: Confrontations
Part 3: Climax & Conclusion
  Chapter 5: The Final Battle
  Chapter 6: Epilogue
"""
        try:
            if model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]: # Example chat models
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an assistant skilled in structuring RPG campaign narratives and creating detailed Table of Contents."},
                        {"role": "user", "content": final_prompt} # Use the potentially customized prompt
                    ],
                    temperature=0.5, # Slightly lower temp for more structured output
                    max_tokens=700 # Adjust as needed for TOC length
                )
                if response.choices and response.choices[0].message:
                    return response.choices[0].message.content.strip()
                else:
                    raise Exception("OpenAI API call for TOC succeeded but returned no content.")
            else: # Assuming older completion models
                response = openai.Completion.create(
                    engine=model,
                    prompt=final_prompt, # Use the potentially customized prompt
                    temperature=0.5,
                    max_tokens=700,
                    n=1,
                    stop=None 
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
                else:
                    raise Exception("OpenAI API call for TOC succeeded but returned no content.")
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during TOC generation: {e}")
            raise Exception(f"Failed to generate TOC due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM TOC generation: {e}")
            raise Exception(f"An unexpected error occurred during TOC generation: {str(e)}") from e

    def generate_titles(self, campaign_concept: str, count: int = 5, model: str = "gpt-3.5-turbo-instruct") -> list[str]:
        """
        Generates a list of alternative campaign titles based on a campaign concept using OpenAI.
        """
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty when generating titles.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count)
        else:
            print("Warning: 'Campaign Names' prompt not found in features.csv. Using default prompt.")
            final_prompt = f"""Based on the following campaign concept, generate {count} alternative campaign titles. Each title should be on a new line. The campaign concept is:

{campaign_concept}

Return only the {count} titles, each on a new line. Do not include numbering or any other surrounding text.
"""
        try:
            if model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]: # Example chat models
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an assistant skilled in brainstorming creative and catchy titles for RPG campaigns."},
                        {"role": "user", "content": final_prompt} # Use the potentially customized prompt
                    ],
                    temperature=0.7,
                    max_tokens=150 + (count * 20) # Base + per title buffer
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    titles_text = response.choices[0].message.content.strip()
                    titles_list = [title.strip() for title in titles_text.split('\n') if title.strip()]
                    return titles_list[:count] # Ensure we return only the requested count
                else:
                    raise Exception("OpenAI API call for titles succeeded but returned no content.")
            else: # Assuming older completion models
                response = openai.Completion.create(
                    engine=model,
                    prompt=final_prompt, # Use the potentially customized prompt
                    temperature=0.7,
                    max_tokens=150 + (count * 20),
                    n=1,
                    stop=None 
                )
                if response.choices and response.choices[0].text:
                    titles_text = response.choices[0].text.strip()
                    titles_list = [title.strip() for title in titles_text.split('\n') if title.strip()]
                    return titles_list[:count] # Ensure we return only the requested count
                else:
                    raise Exception("OpenAI API call for titles succeeded but returned no content.")
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during title generation: {e}")
            raise Exception(f"Failed to generate titles due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM title generation: {e}")
            raise Exception(f"An unexpected error occurred during title generation: {str(e)}") from e

    def generate_section_content(self, campaign_concept: str, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: str = "gpt-3.5-turbo-instruct") -> str:
        """
        Generates content for a new campaign section using OpenAI.
        """
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty when generating section content.")

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=section_creation_prompt or "Continue the story.",
                section_title_suggestion=section_title_suggestion or "Untitled Section"
            )
        else:
            print("Warning: 'Section Content' prompt not found in features.csv. Using default prompt.")
            # Construct the default prompt
            prompt_parts = ["You are writing a new section for a tabletop role-playing game campaign."]
            prompt_parts.append(f"The overall campaign concept is:\n{campaign_concept}\n")

            if existing_sections_summary:
                prompt_parts.append(f"So far, the campaign includes these sections (titles or brief summaries):\n{existing_sections_summary}\n")

            if section_title_suggestion:
                prompt_parts.append(f"The suggested title for this new section is: {section_title_suggestion}\n")
            
            if section_creation_prompt:
                prompt_parts.append(f"The specific instructions or starting prompt for this section are: {section_creation_prompt}\n")
            else:
                prompt_parts.append("Please write the next logical section for this campaign, continuing from the existing sections if provided, or starting a new major part if appropriate.\n")
            
            prompt_parts.append("Generate the content for this new section. Ensure it is detailed, engaging, and provides new developments, locations, NPCs, or plot points relevant to the campaign. Aim for a few paragraphs of content.")
            final_prompt = "\n".join(prompt_parts)

        try:
            if model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]: # Example chat models
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert RPG writer, crafting a new section for an ongoing campaign."},
                        {"role": "user", "content": final_prompt} # Use the potentially customized prompt
                    ],
                    temperature=0.7,
                    max_tokens=1500 # Allow for longer content
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                else:
                    raise Exception("OpenAI API call for section content succeeded but returned no content.")
            else: # Assuming older completion models
                response = openai.Completion.create(
                    engine=model,
                    prompt=final_prompt, # Use the potentially customized prompt
                    temperature=0.7,
                    max_tokens=1500, 
                    n=1,
                    stop=None 
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
                else:
                    raise Exception("OpenAI API call for section content succeeded but returned no content.")
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during section content generation: {e}")
            raise Exception(f"Failed to generate section content due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM section content generation: {e}")
            raise Exception(f"An unexpected error occurred during section content generation: {str(e)}") from e

    def list_available_models(self) -> List[Dict[str, str]]:
        """
        Lists available LLM models from OpenAI, with a curated list of common models.
        """
        models_to_return: Dict[str, Dict[str,str]] = {} # Use dict to avoid duplicates, then convert to list

        # Add some well-known, generally useful models manually
        # This ensures a baseline list even if the API's own listing is too verbose or misses some
        common_models = {
            "gpt-4": {"id": "gpt-4", "name": "GPT-4"},
            "gpt-4-turbo-preview": {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview"},
            "gpt-3.5-turbo": {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            "gpt-3.5-turbo-instruct": {"id": "gpt-3.5-turbo-instruct", "name": "GPT-3.5 Turbo Instruct"},
            "text-davinci-003": {"id": "text-davinci-003", "name": "Text Davinci 003 (Legacy)"},
            # Add other models if desired, e.g., older ones or specific fine-tunes if listed by default
        }
        models_to_return.update(common_models)

        try:
            # Fetch models from OpenAI API
            # Note: openai.Model.list() might return a large list, including many older or less relevant models.
            # The filtering here is a basic attempt to narrow it down.
            response = openai.Model.list()
            if response and response.data:
                for model_obj in response.data:
                    model_id = model_obj.id
                    # Filter for standard models and potentially user's fine-tuned models
                    # 'owned_by' can be 'openai', 'openai-dev', 'openai-internal', 'system', or user's organization ID.
                    if model_id not in models_to_return and (
                        model_obj.owned_by.startswith("openai") or 
                        model_obj.owned_by == "system" or
                        (hasattr(model_obj, 'root') and model_obj.root == model_id) # Include root models
                        # Add a check for user's org ID if fine-tuned models are a primary concern
                        # and if settings.OPENAI_ORG_ID is available
                    ):
                         # Prioritize already added common models if IDs clash but OpenAI name is different
                        models_to_return[model_id] = {"id": model_id, "name": model_id} # Simple name for now

        except openai.error.OpenAIError as e:
            print(f"OpenAI API error when listing models: {e}. Returning manually curated list only.")
            # We can choose to return only the manually curated list if API fails
            # Or raise an exception if API access is critical for this function.
            # For now, we'll proceed with what we have.
        except Exception as e:
            print(f"An unexpected error occurred when listing models: {e}. Returning manually curated list only.")
            # Similar handling for other unexpected errors.

        return list(models_to_return.values())
