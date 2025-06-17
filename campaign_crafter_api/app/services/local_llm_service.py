import httpx # For making async HTTP requests
from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import User as UserModel # Added UserModel import
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService

# Standard ignored API key for local OpenAI-compatible servers
LOCAL_LLM_DUMMY_API_KEY = "ollama" 

class LocalLLMService(AbstractLLMService):
    # Used by the factory to refer to this provider, matches settings.LOCAL_LLM_PROVIDER_NAME
    PROVIDER_NAME = settings.LOCAL_LLM_PROVIDER_NAME 

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.api_base_url = settings.LOCAL_LLM_API_BASE_URL

        self.configured_successfully = bool(self.api_base_url)
        if not self.configured_successfully:
            raise ValueError(f"{self.PROVIDER_NAME.title()} API base URL not configured. Please set LOCAL_LLM_API_BASE_URL in your .env file.")
        
        if not self.api_base_url.endswith('/'):
            self.api_base_url += '/'
            
        self.client = httpx.AsyncClient(base_url=self.api_base_url, timeout=60.0)
        self.default_model_id = settings.LOCAL_LLM_DEFAULT_MODEL_ID
        self.feature_prompt_service = FeaturePromptService()

    async def close(self):
        """Closes the HTTP client session."""
        await self.client.aclose()

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        if not self.configured_successfully: # Relies on __init__ to set this based on api_base_url
            return False
        try:
            response = await self.client.get("models", headers={"Authorization": f"Bearer {LOCAL_LLM_DUMMY_API_KEY}"})
            return response.status_code == 200
        except httpx.RequestError as e:
            print(f"Error checking {self.PROVIDER_NAME.title()} availability: {e}")
            return False

    async def generate_text(
        self, 
        prompt: str, 
        current_user: UserModel,
        db: Session,
        model: Optional[str] = None, 
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise HTTPException(status_code=503, detail=f"{self.PROVIDER_NAME.title()} service is not available or configured.")

        selected_model = model or self.default_model_id
        if not selected_model:
            raise HTTPException(status_code=400, detail=f"No model specified and no default model configured for {self.PROVIDER_NAME.title()}.")

        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False, # For simplicity, not implementing streaming in this generic method
        }
        # Some servers might require these even if null, others might error.
        # if temperature is not None: payload["temperature"] = temperature
        # if max_tokens is not None: payload["max_tokens"] = max_tokens
        
        headers = {"Authorization": f"Bearer {LOCAL_LLM_DUMMY_API_KEY}"}

        try:
            response = await self.client.post("chat/completions", json=payload, headers=headers)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            
            data = response.json()
            if data.get("choices") and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                message = data["choices"][0].get("message")
                if message and isinstance(message, dict) and message.get("content"):
                    return message["content"].strip()
            
            # If response structure is unexpected
            error_detail = f"{self.PROVIDER_NAME.title()} API response format unexpected: {data}"
            print(error_detail) # Log for debugging
            raise HTTPException(status_code=500, detail=error_detail)

        except httpx.HTTPStatusError as e:
            # Attempt to parse error from local LLM server response
            error_detail = f"Error from {self.PROVIDER_NAME.title()} API: {e.response.status_code} - {e.response.text}"
            try:
                err_json = e.response.json()
                if err_json.get("error") and isinstance(err_json["error"], dict) and err_json["error"].get("message"):
                    error_detail = f"{self.PROVIDER_NAME.title()} API Error: {err_json['error']['message']}"
                elif err_json.get("detail"): # Some FastAPI like errors
                     error_detail = f"{self.PROVIDER_NAME.title()} API Error: {err_json['detail']}"
            except Exception:
                pass # Keep the original text if JSON parsing fails
            print(error_detail)
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        except httpx.RequestError as e: # Network errors
            error_detail = f"Network error connecting to {self.PROVIDER_NAME.title()} API: {e}"
            print(error_detail)
            raise HTTPException(status_code=503, detail=error_detail) # Service Unavailable
        except Exception as e: # Other unexpected errors
            error_detail = f"Unexpected error during {self.PROVIDER_NAME.title()} text generation: {type(e).__name__} - {e}"
            print(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)


    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, Any]]:
        if not await self.is_available(current_user=current_user, db=db):
            return []

        try:
            response = await self.client.get("models", headers={"Authorization": f"Bearer {LOCAL_LLM_DUMMY_API_KEY}"})
            response.raise_for_status()
            
            data = response.json()
            models_list: List[Dict[str, Any]] = []
            
            api_models_data = []
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list): # Standard OpenAI format
                api_models_data = data["data"]
            elif isinstance(data, list): # Some compatible servers
                api_models_data = data
            elif isinstance(data, dict) and "models" in data and isinstance(data["models"], list): # Ollama native /api/tags or some /v1/models proxies
                 api_models_data = data["models"]
            else:
                print(f"Warning: Unexpected format from {self.PROVIDER_NAME.title()} /models endpoint: {data}")
                return []

            for model_obj in api_models_data:
                model_id = model_obj.get("id") or model_obj.get("model") or model_obj.get("name")
                if model_id:
                    friendly_name = model_obj.get("name", model_id)
                    # Default assumptions for local models
                    model_type = "chat"
                    supports_temperature = True
                    capabilities = ["chat"]

                    # Example: if 'coder' in model_id.lower(): model_type = "completion"; capabilities.append("code")

                    models_list.append({
                        "id": model_id,
                        "name": friendly_name,
                        "model_type": model_type,
                        "supports_temperature": supports_temperature,
                        "capabilities": capabilities
                    })
            
            return models_list
        except httpx.HTTPStatusError as e:
            print(f"Error listing models from {self.PROVIDER_NAME.title()} API: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Network error connecting to {self.PROVIDER_NAME.title()} API for model listing: {e}")
        except Exception as e:
            print(f"Unexpected error parsing models from {self.PROVIDER_NAME.title()}: {type(e).__name__} - {e}")
        return [] # Return empty list on error


    # Implement other abstract methods by calling self.generate_text
    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        custom_prompt = self.feature_prompt_service.get_prompt("Campaign", db=db)
        final_prompt = custom_prompt.format(user_prompt=user_prompt) if custom_prompt else f"Generate a detailed RPG campaign concept: {user_prompt}"
        return await self.generate_text(prompt=final_prompt, current_user=current_user, db=db, model=model)

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]:
        custom_prompt = self.feature_prompt_service.get_prompt("Campaign Names", db=db)
        final_prompt = custom_prompt.format(campaign_concept=campaign_concept, count=count) if custom_prompt else f"Generate {count} campaign titles for: {campaign_concept}. Each on a new line."
        generated_string = await self.generate_text(prompt=final_prompt, current_user=current_user, db=db, model=model)
        return [title.strip() for title in generated_string.split('\n') if title.strip()][:count]

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> Dict[str, str]:
        if not await self.is_available(current_user=current_user, db=db):
            raise HTTPException(status_code=503, detail=f"{self.PROVIDER_NAME.title()} service is not available or configured.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")

        display_prompt_template = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template:
            raise LLMGenerationError(f"Display TOC prompt template ('TOC Display') not found for {self.PROVIDER_NAME}.")
        display_final_prompt = display_prompt_template.format(campaign_concept=campaign_concept)

        generated_display_toc = await self.generate_text(
            prompt=display_final_prompt,
            current_user=current_user, db=db,
            model=model,
            temperature=0.5,
            max_tokens=700
        )
        if not generated_display_toc:
             raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Display TOC succeeded but returned no usable content.")

        homebrewery_prompt_template = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not homebrewery_prompt_template:
            raise LLMGenerationError(f"Homebrewery TOC prompt template ('TOC Homebrewery') not found for {self.PROVIDER_NAME}.")
        homebrewery_final_prompt = homebrewery_prompt_template.format(campaign_concept=campaign_concept)

        generated_homebrewery_toc = await self.generate_text(
            prompt=homebrewery_final_prompt,
            current_user=current_user, db=db,
            model=model,
            temperature=0.5,
            max_tokens=1000
        )
        if not generated_homebrewery_toc:
             raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Homebrewery TOC succeeded but returned no usable content.")

        return {
            "display_toc": generated_display_toc,
            "homebrewery_toc": generated_homebrewery_toc
        }

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
            effective_section_prompt = f"{type_based_instruction}\n\nFurther specific instructions for this section: {section_creation_prompt}"
        elif not effective_section_prompt:
            effective_section_prompt = "Continue the story logically, introducing new elements or developing existing ones."

        custom_prompt_template = self.feature_prompt_service.get_prompt("Section Content", db=db)
        final_prompt_for_generation: str
        if custom_prompt_template:
            final_prompt_for_generation = custom_prompt_template.format(
                campaign_concept=campaign_concept,
                existing_sections_summary=existing_sections_summary or "N/A",
                section_creation_prompt=effective_section_prompt, # Use the refined prompt
                section_title_suggestion=section_title_suggestion or "Untitled Section"
            )
        else: # Fallback default prompt construction
            prompt_parts = ["You are writing a new section for a tabletop role-playing game campaign."]
            prompt_parts.append(f"The overall campaign concept is:\n{campaign_concept}\n")
            if existing_sections_summary:
                prompt_parts.append(f"So far, the campaign includes these sections (titles or brief summaries):\n{existing_sections_summary}\n")

            title_display = section_title_suggestion or "Untitled Section"
            type_display = section_type or "Generic"
            prompt_parts.append(f"This new section is titled '{title_display}' and is of type '{type_display}'.\n")

            prompt_parts.append(f"The specific instructions or starting prompt for this section are: {effective_section_prompt}\n")
            prompt_parts.append("Generate detailed and engaging content for this new section.")
            final_prompt_for_generation = "\n".join(prompt_parts)
            
        return await self.generate_text(prompt=final_prompt_for_generation, _current_user=current_user, _db=db, model=model, temperature=0.7, max_tokens=4000)
