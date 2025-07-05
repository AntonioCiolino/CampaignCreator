from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app import models, orm_models
from app.models import User as UserModel
# Removed import from llm_factory: from app.services.llm_factory import LLMServiceUnavailableError

class LlamaLLMService(AbstractLLMService):
    PROVIDER_NAME = "llama" # For easy reference

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.effective_api_key = self.api_key # Key from constructor (user-provided)
        if not self.effective_api_key:
            self.effective_api_key = settings.LLAMA_API_KEY # Fallback to system key

        self.api_url = settings.LLAMA_API_URL # Assuming a base URL might be needed

        self.configured_successfully = False
        # For Llama, URL might also be essential if it's a self-hosted or specific endpoint
        key_is_valid = bool(self.effective_api_key and self.effective_api_key not in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"])
        # url_is_valid = bool(self.api_url and "YOUR_LLAMA_API_URL" not in self.api_url) # Add if URL is also mandatory from settings
        # For now, primarily relying on key for placeholder configuration status
        if key_is_valid: # And url_is_valid if that's a strict requirement
            self.configured_successfully = True
            # print(f"{self.PROVIDER_NAME.title()}LLMService configured with an effective API key.")
        else:
            print(f"Warning: {self.PROVIDER_NAME.title()} API key (user or system) not configured or is a placeholder.") # Add URL status if relevant

        self.feature_prompt_service = FeaturePromptService()
        # Placeholder for actual client initialization if needed
        # print(f"{self.PROVIDER_NAME.title()}LLMService initialized (placeholder).") # Optional: can be removed if too verbose

    async def is_available(self, current_user: UserModel, db: Session) -> bool:
        key_present = bool(self.api_key and self.api_key not in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"])
        # In a real scenario, this might involve an async check to an API endpoint if one exists
        # For this placeholder, key_present is sufficient.
        return key_present 

    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str: # Changed _current_user
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available. Please configure API key/URL.")
        
        error_message = (
            f"{self.PROVIDER_NAME.title()}LLMService.generate_text is not implemented. "
            f"Prompt: '{prompt}', Model: '{model or 'default'}', Temp: {temperature}, MaxTokens: {max_tokens}"
        )
        print(f"WARNING: {error_message}")
        raise NotImplementedError(error_message)

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        # This method directly raises NotImplementedError, so no internal call to generate_text to update yet.
        raise NotImplementedError(f"{self.PROVIDER_NAME.title()}LLMService.generate_campaign_concept not implemented.")

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        raise NotImplementedError(f"{self.PROVIDER_NAME.title()}LLMService.generate_titles not implemented.")

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> Dict[str, str]:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")

        # model_to_use = model or "default-llama-model" # Or some default for Llama

        display_prompt_template = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template:
            raise LLMGenerationError(f"Display TOC prompt template ('TOC Display') not found for {self.PROVIDER_NAME}.")
        display_final_prompt = display_prompt_template.format(campaign_concept=campaign_concept)

        homebrewery_prompt_template = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not homebrewery_prompt_template:
            raise LLMGenerationError(f"Homebrewery TOC prompt template ('TOC Homebrewery') not found for {self.PROVIDER_NAME}.")
        homebrewery_final_prompt = homebrewery_prompt_template.format(campaign_concept=campaign_concept)

        # These calls will fail until generate_text is implemented
        generated_display_toc = await self.generate_text(prompt=display_final_prompt, current_user=current_user, db=db, model=model, temperature=0.5, max_tokens=700)
        if not generated_display_toc:
             raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Display TOC succeeded but returned no usable content.")

        generated_homebrewery_toc = await self.generate_text(prompt=homebrewery_final_prompt, current_user=current_user, db=db, model=model, temperature=0.5, max_tokens=1000)
        if not generated_homebrewery_toc:
             raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Homebrewery TOC succeeded but returned no usable content.")

        return {
            "display_toc": generated_display_toc,
            "homebrewery_toc": generated_homebrewery_toc
        }

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
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")

        # campaign_concept = db_campaign.concept if db_campaign else "N/A"
        # characters_info = "N/A"
        # if db_campaign and db_campaign.characters:
        #     characters_info = f"{len(db_campaign.characters)} characters associated."
        # print(f"Llama generate_section_content called with campaign_id: {db_campaign.id if db_campaign else 'N/A'}, characters: {characters_info}")

        raise NotImplementedError(
            f"{self.PROVIDER_NAME.title()}LLMService.generate_section_content not implemented. "
            f"Received section_type: {section_type}"
        )

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, any]]:
        if not await self.is_available(current_user=current_user, db=db):
            print(f"Warning: {self.PROVIDER_NAME.title()} service not available. Cannot list models.")
            return []
        
        print(f"Warning: {self.PROVIDER_NAME.title()}LLMService.list_available_models is returning a placeholder list.")
        # Assuming Llama models are generally chat-based and support temperature.
        # This is a placeholder; a real implementation would fetch from an API or config.
        placeholder_models = [
            {
                "id": "llama-7b-chat",
                "name": f"{self.PROVIDER_NAME.title()} 7B Chat (Placeholder)",
                "model_type": "chat",
                "supports_temperature": True,
                "capabilities": ["chat"]
            },
            {
                "id": "llama-13b-chat",
                "name": f"{self.PROVIDER_NAME.title()} 13B Chat (Placeholder)",
                "model_type": "chat",
                "supports_temperature": True,
                "capabilities": ["chat"]
            },
            {
                "id": "codellama-34b-instruct",
                "name": f"Code{self.PROVIDER_NAME.title()} 34B Instruct (Placeholder)",
                "model_type": "completion", # Or "chat" if it's conversational for code
                "supports_temperature": True,
                "capabilities": ["completion", "code"] # "chat-adaptable" could be added if true
            },
        ]
        return placeholder_models

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # For most Llama implementations (e.g. via huggingface transformers or local http endpoints),
        # explicit closing might not be needed in the same way as an AsyncClient.
        # This is a placeholder.
        print(f"{self.PROVIDER_NAME.title()}LLMService close method called (placeholder).")
        pass

    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available. Please configure API key/URL.")

        if not sections_summary:
            return "{{toc,wide\n# Table Of Contents\n}}\n"

        prompt_template_str = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not prompt_template_str:
            raise LLMGenerationError(f"Homebrewery TOC prompt template ('TOC Homebrewery') not found for {self.PROVIDER_NAME}.")

        final_prompt = prompt_template_str.format(sections_summary=sections_summary)

        # This will raise NotImplementedError because self.generate_text is not implemented
        generated_toc = await self.generate_text(
            prompt=final_prompt,
            current_user=current_user,
            db=db,
            model=model, # Pass the model selected for this operation
            temperature=0.3,
            max_tokens=1000
        )
        # The following lines would only be reached if generate_text was implemented and returned content:
        # if not generated_toc:
        #     raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Homebrewery TOC from sections succeeded but returned no usable content.")
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
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")

        # Construct messages list, similar to OpenAI/DeepSeek
        messages = []

        # System message for character persona
        truncated_notes = (character_notes[:1000] + '...') if character_notes and len(character_notes) > 1000 else character_notes
        system_content = (
            f"You are embodying the character named '{character_name}'. "
            f"Your personality, background, and way of speaking are defined by the following notes: "
            f"'{truncated_notes if truncated_notes else 'A typically neutral character.'}' "
            f"Respond naturally as this character would. Do not break character. Do not mention that you are an AI."
        )
        messages.append({"role": "system", "content": system_content})

        # Add chat history
        if chat_history:
            for message_item in chat_history: # Renamed to avoid conflict
                role = "user" if message_item.speaker.lower() == "user" else "assistant"
                messages.append({"role": role, "content": message_item.text})

        # Add the current user prompt
        messages.append({"role": "user", "content": user_prompt})

        # Here, you would typically call the Llama API (often an OpenAI-compatible endpoint)
        # using the 'messages' list. For example:
        # client = AsyncOpenAI(api_key=self.effective_api_key, base_url=self.api_url or "YOUR_LLAMA_ENDPOINT")
        # chat_completion = await client.chat.completions.create(
        #     model=model or "llama-model-name", # Specify your Llama model
        #     messages=messages,
        #     temperature=temperature if temperature is not None else 0.7,
        #     max_tokens=max_tokens or 300
        # )
        # return chat_completion.choices[0].message.content.strip()

        raise NotImplementedError(
            f"{self.PROVIDER_NAME.title()}LLMService.generate_character_response not implemented. "
            f"Constructed messages: {messages}"
        )

# if __name__ == '__main__':
#     from app.core.config import settings
#     from dotenv import load_dotenv
#     from pathlib import Path
#     import os # Required for os.getenv if used in __main__

#     env_path_api_root = Path(__file__).resolve().parent.parent.parent / ".env"
#     if env_path_api_root.exists():
#         load_dotenv(dotenv_path=env_path_api_root)
    
#     # Simulate settings update from .env for testing this script directly
#     settings.LLAMA_API_KEY = settings.LLAMA_API_KEY or os.getenv("LLAMA_API_KEY")
#     settings.LLAMA_API_URL = settings.LLAMA_API_URL or os.getenv("LLAMA_API_URL")

#     print(f"--- Testing {LlamaLLMService.PROVIDER_NAME.title()}LLMService Placeholder ---")

#     # To test async methods, you'd need asyncio.run()
#     # This block would need to be refactored to use an async event loop.
#     # For simplicity in this refactor, we're commenting it out as the service is a placeholder.
    
#     # Example of how you might test (requires Python 3.7+ for asyncio.run):
#     # import asyncio
#     # async def main_test():
#     #     available_check = False
#     #     try:
#     #         original_key = settings.LLAMA_API_KEY
#     #         if not original_key or original_key in ["YOUR_LLAMA_API_KEY", "YOUR_API_KEY_HERE"]:
#     #             print(f"LLAMA_API_KEY not found or is placeholder in .env. Using dummy key for {LlamaLLMService.PROVIDER_NAME.title()} service instantiation test.")
#     #             settings.LLAMA_API_KEY = "dummy_key_for_test"
            
#     #         service = LlamaLLMService() # __init__ is sync
#     #         available_check = await service.is_available()
#     #         print(f"{LlamaLLMService.PROVIDER_NAME.title()} Service initialized. Is Available: {available_check}")

#     #         if available_check:
#     #             print("\nAvailable Llama Models (Placeholder List):")
#     #             models = await service.list_available_models()
#     #             for m in models:
#     #                 print(f"- {m['name']} (id: {m['id']})")

#     #             print("\nAttempting to call generate_text (expected NotImplementedError or LLMServiceUnavailableError):")
#     #             try:
#     #                 await service.generate_text("Test prompt for Llama.")
#     #             except (NotImplementedError, LLMServiceUnavailableError) as e:
#     #                 print(f"Correctly caught: {e}")
#     #         else:
#     #             print(f"{LlamaLLMService.PROVIDER_NAME.title()} service is not available. Skipping further tests.")

#     #         settings.LLAMA_API_KEY = original_key # Restore original key
#     #         await service.close()

#     #     except ValueError as ve:
#     #         print(f"Error during {LlamaLLMService.PROVIDER_NAME.title()} service initialization: {ve}")
#     #     except Exception as e:
#     #         print(f"An unexpected error occurred: {e}")

#     # if os.getenv("RUN_LLAMA_TESTS") == "true": # Control execution if needed
#     #    asyncio.run(main_test())
#     # else:
#     #    print("Skipping LlamaLLMService async tests in __main__ block. Set RUN_LLAMA_TESTS=true to run.")


#     print(f"--- End Test for {LlamaLLMService.PROVIDER_NAME.title()}LLMService ---")
