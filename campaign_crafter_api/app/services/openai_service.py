import openai # type: ignore
from typing import Optional, List, Dict 
from app.core.config import settings
from app.services.llm_service import AbstractLLMService # Updated import
from app.services.feature_prompt_service import FeaturePromptService

class OpenAILLMService(AbstractLLMService): # Updated inheritance
    DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
    DEFAULT_COMPLETION_MODEL = "gpt-3.5-turbo-instruct"

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.is_available(): # Use the new method to check availability
            raise ValueError("OpenAI API key not configured or is a placeholder. Please set OPENAI_API_KEY in your .env file.")
        openai.api_key = self.api_key
        self.feature_prompt_service = FeaturePromptService()

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "YOUR_API_KEY_HERE" and self.api_key != "YOUR_OPENAI_API_KEY")

    def _get_model(self, preferred_model: Optional[str], use_chat_model: bool = True) -> str:
        """Helper to determine the model to use, falling back to defaults if None."""
        if preferred_model:
            return preferred_model
        return self.DEFAULT_CHAT_MODEL if use_chat_model else self.DEFAULT_COMPLETION_MODEL

    def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str:
        if not prompt:
            raise ValueError("Prompt cannot be empty.")

        selected_model = self._get_model(model, use_chat_model=True) # Default to chat model for generic text

        try:
            # Determine if the model is a chat-based model or completion-based
            # This is a simplified check; a more robust solution might involve querying model capabilities
            if selected_model.startswith("gpt-4") or selected_model.startswith("gpt-3.5-turbo") or "ft:gpt-3.5-turbo" in selected_model:
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            elif selected_model.startswith("ft:") or selected_model.endswith("-instruct") or "davinci" in selected_model or "curie" in selected_model or "babbage" in selected_model or "ada" in selected_model:
                response = openai.Completion.create(
                    model=selected_model, # Use 'model' for newer versions, 'engine' was for older ones
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
            else:
                # Fallback attempt with ChatCompletion if model type is ambiguous but not explicitly a completion model
                print(f"Warning: Model type for '{selected_model}' is ambiguous. Attempting ChatCompletion API.")
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            
            raise Exception(f"OpenAI API call ({'ChatCompletion' if selected_model.startswith('gpt') else 'Completion'}) succeeded but returned no content for model {selected_model}.")

        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during generic text generation with model {selected_model}: {e}")
            raise Exception(f"Failed to generate text due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during generic text generation with model {selected_model}: {e}")
            raise Exception(f"An unexpected error occurred during generic text generation: {str(e)}") from e


    def generate_campaign_concept(self, user_prompt: str, model: Optional[str] = None) -> str:
        selected_model = self._get_model(model, use_chat_model=False) # Default to completion for this
        
        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(user_prompt=user_prompt)
        else:
            print("Warning: 'Campaign' prompt not found in features.csv. Using default prompt.")
            final_prompt = f"Generate a detailed campaign concept, including potential plot hooks and key NPCs, based on the following idea: {user_prompt}"
        
        try:
            if selected_model.startswith("gpt-4") or selected_model.startswith("gpt-3.5-turbo"):
                 response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a creative assistant helping to brainstorm RPG campaign concepts."},
                        {"role": "user", "content": final_prompt} # Corrected from prompt_template
                    ],
                    temperature=0.7,
                    max_tokens=1000 
                )
                 if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            else: 
                response = openai.Completion.create(
                    model=selected_model, 
                    prompt=final_prompt,
                    temperature=0.7,
                    max_tokens=1000,
                    n=1,
                    stop=None
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
            raise Exception("OpenAI API call succeeded but returned no content.")

        except openai.error.OpenAIError as e:
            print(f"OpenAI API error: {e}")
            raise Exception(f"Failed to generate campaign concept due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM concept generation: {e}")
            raise Exception(f"An unexpected error occurred: {str(e)}") from e

    def generate_toc(self, campaign_concept: str, model: Optional[str] = None) -> str:
        selected_model = self._get_model(model, use_chat_model=True) # Default to chat for this

        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty when generating a Table of Contents.")

        custom_prompt_template = self.feature_prompt_service.get_prompt("Table of Contents")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept)
        else:
            print("Warning: 'Table of Contents' prompt not found in features.csv. Using default prompt.")
            final_prompt = f"""Based on the following campaign concept, generate a hierarchical Table of Contents suitable for a tabletop role-playing game campaign... (rest of prompt)""" # Truncated for brevity
        
        try:
            if selected_model.startswith("gpt-4") or selected_model.startswith("gpt-3.5-turbo"):
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are an assistant skilled in structuring RPG campaign narratives and creating detailed Table of Contents."},
                        {"role": "user", "content": final_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=700 
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            else: 
                response = openai.Completion.create(
                    model=selected_model,
                    prompt=final_prompt,
                    temperature=0.5,
                    max_tokens=700,
                    n=1,
                    stop=None 
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
            raise Exception("OpenAI API call for TOC succeeded but returned no content.")
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during TOC generation: {e}")
            raise Exception(f"Failed to generate TOC due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM TOC generation: {e}")
            raise Exception(f"An unexpected error occurred during TOC generation: {str(e)}") from e

    def generate_titles(self, campaign_concept: str, count: int = 5, model: Optional[str] = None) -> list[str]:
        selected_model = self._get_model(model, use_chat_model=True) # Default to chat

        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty when generating titles.")
        if count <= 0:
            raise ValueError("Count for titles must be a positive integer.")

        custom_prompt_template = self.feature_prompt_service.get_prompt("Campaign Names")
        if custom_prompt_template:
            final_prompt = custom_prompt_template.format(campaign_concept=campaign_concept, count=count)
        else:
            print("Warning: 'Campaign Names' prompt not found in features.csv. Using default prompt.")
            final_prompt = f"""Based on the following campaign concept, generate {count} alternative campaign titles... (rest of prompt)""" # Truncated
        try:
            if selected_model.startswith("gpt-4") or selected_model.startswith("gpt-3.5-turbo"):
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are an assistant skilled in brainstorming creative and catchy titles for RPG campaigns."},
                        {"role": "user", "content": final_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150 + (count * 20) 
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    titles_text = response.choices[0].message.content.strip()
                    titles_list = [title.strip() for title in titles_text.split('\n') if title.strip()]
                    return titles_list[:count] 
            else: 
                response = openai.Completion.create(
                    model=selected_model,
                    prompt=final_prompt,
                    temperature=0.7,
                    max_tokens=150 + (count * 20),
                    n=1,
                    stop=None 
                )
                if response.choices and response.choices[0].text:
                    titles_text = response.choices[0].text.strip()
                    titles_list = [title.strip() for title in titles_text.split('\n') if title.strip()]
                    return titles_list[:count]
            raise Exception("OpenAI API call for titles succeeded but returned no content.")
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during title generation: {e}")
            raise Exception(f"Failed to generate titles due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM title generation: {e}")
            raise Exception(f"An unexpected error occurred during title generation: {str(e)}") from e

    def generate_section_content(self, campaign_concept: str, existing_sections_summary: Optional[str], section_creation_prompt: Optional[str], section_title_suggestion: Optional[str], model: Optional[str] = None) -> str:
        selected_model = self._get_model(model, use_chat_model=True) # Default to chat

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
            prompt_parts = ["You are writing a new section for a tabletop role-playing game campaign." , f"The overall campaign concept is:\n{campaign_concept}\n"] # Truncated
            # ... (rest of default prompt construction)
            final_prompt = "\n".join(prompt_parts)


        try:
            if selected_model.startswith("gpt-4") or selected_model.startswith("gpt-3.5-turbo"):
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are an expert RPG writer, crafting a new section for an ongoing campaign."},
                        {"role": "user", "content": final_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            else:
                response = openai.Completion.create(
                    model=selected_model,
                    prompt=final_prompt, 
                    temperature=0.7,
                    max_tokens=1500, 
                    n=1,
                    stop=None 
                )
                if response.choices and response.choices[0].text:
                    return response.choices[0].text.strip()
            raise Exception("OpenAI API call for section content succeeded but returned no content.")
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error during section content generation: {e}")
            raise Exception(f"Failed to generate section content due to OpenAI API error: {str(e)}") from e
        except Exception as e:
            print(f"An unexpected error occurred during LLM section content generation: {e}")
            raise Exception(f"An unexpected error occurred during section content generation: {str(e)}") from e

    def list_available_models(self) -> List[Dict[str, str]]:
        """
        Lists available LLM models from OpenAI.
        The 'id' in the returned dict is the model ID usable in generation methods.
        """
        if not self.is_available():
            print("Warning: OpenAI API key not configured. Cannot fetch models.")
            return []
            
        models_to_return: Dict[str, Dict[str,str]] = {} 

        # Manually add well-known models with user-friendly names
        # These IDs are what the OpenAI API expects.
        common_models = {
            "gpt-4": {"id": "gpt-4", "name": "GPT-4"},
            "gpt-4-turbo-preview": {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview"},
            "gpt-3.5-turbo": {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Chat)"},
            "gpt-3.5-turbo-instruct": {"id": "gpt-3.5-turbo-instruct", "name": "GPT-3.5 Turbo Instruct (Completion)"},
        }
        # Add legacy models if desired, or specific versions
        # "text-davinci-003": {"id": "text-davinci-003", "name": "Text Davinci 003 (Legacy Completion)"}
        models_to_return.update(common_models)

        try:
            response = openai.Model.list()
            if response and response.data:
                for model_obj in response.data:
                    model_id = model_obj.id
                    # Add to list if not already present from common_models (to keep friendlier names)
                    if model_id not in models_to_return:
                        # Simple naming for less common models pulled from API
                        name = model_id.replace("-", " ").title() 
                        if "gpt-3.5" in model_id and "turbo" in model_id and "instruct" not in model_id:
                            name += " (Chat)"
                        elif "instruct" in model_id:
                             name += " (Completion)"
                        elif "davinci" in model_id or "curie" in model_id or "babbage" in model_id or "ada" in model_id:
                             name += " (Legacy Completion)"

                        models_to_return[model_id] = {"id": model_id, "name": name}
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error when listing models: {e}. Returning manually curated list only.")
        except Exception as e:
            print(f"An unexpected error occurred when listing models: {e}. Returning manually curated list only.")

        # Sort models, perhaps prioritizing chat models or newer models
        sorted_models = sorted(list(models_to_return.values()), key=lambda x: (
            not x['name'].startswith("GPT-4"), # GPT-4 first
            not x['name'].startswith("GPT-3.5 Turbo (Chat)"), # then 3.5 Turbo Chat
            not x['name'].startswith("GPT-3.5 Turbo Instruct"), # then 3.5 Turbo Instruct
            x['name'] # then alphabetically
        ))
        return sorted_models
