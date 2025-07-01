from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app import models # Added models import
from app.models import User as UserModel
# Removed import from llm_factory: from app.services.llm_factory import LLMServiceUnavailableError
# import os # For the __main__ block, commented out

class DeepSeekLLMService(AbstractLLMService):
    PROVIDER_NAME = "deepseek" # For easy reference

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self.effective_api_key = self.api_key # Key from constructor (user-provided)
        if not self.effective_api_key:
            self.effective_api_key = settings.DEEPSEEK_API_KEY # Fallback to system key

        self.configured_successfully = False
        if self.effective_api_key and self.effective_api_key not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
            self.configured_successfully = True
            # print(f"{self.PROVIDER_NAME.title()}LLMService configured with an effective API key.")
        else:
            print(f"Warning: {self.PROVIDER_NAME.title()} API key (user or system) not configured or is a placeholder.")

        self.feature_prompt_service = FeaturePromptService()
        # Placeholder for actual client initialization. DeepSeek often uses an OpenAI-compatible client.
        # print(f"{self.PROVIDER_NAME.title()}LLMService initialized (placeholder).") # Optional: can be removed if too verbose

    async def is_available(self, current_user: UserModel, db: Session) -> bool: # Changed params
        # Checks if essential configuration is present.
        return bool(self.api_key and self.api_key not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"])

    async def generate_text(self, prompt: str, current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str: # Changed _current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass corrected args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available. Please configure API key.")
        
        error_message = (
            f"{self.PROVIDER_NAME.title()}LLMService.generate_text is not implemented. "
            f"Prompt: '{prompt}', Model: '{model or 'default'}', Temp: {temperature}, MaxTokens: {max_tokens}"
        )
        print(f"WARNING: {error_message}")
        raise NotImplementedError(error_message)

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass corrected args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        raise NotImplementedError(f"{self.PROVIDER_NAME.title()}LLMService.generate_campaign_concept not implemented.")

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass corrected args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        raise NotImplementedError(f"{self.PROVIDER_NAME.title()}LLMService.generate_titles not implemented.")

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> Dict[str, str]: # Added current_user
        if not await self.is_available(current_user=current_user, db=db): # Pass corrected args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        if not campaign_concept:
            raise ValueError("Campaign concept cannot be empty.")

        # model_to_use = model or "deepseek-chat" # Or some default for DeepSeek

        display_prompt_template = self.feature_prompt_service.get_prompt("TOC Display", db=db)
        if not display_prompt_template:
            raise LLMGenerationError(f"Display TOC prompt template ('TOC Display') not found for {self.PROVIDER_NAME}.")
        display_final_prompt = display_prompt_template.format(campaign_concept=campaign_concept)

        homebrewery_prompt_template = self.feature_prompt_service.get_prompt("TOC Homebrewery", db=db)
        if not homebrewery_prompt_template:
            raise LLMGenerationError(f"Homebrewery TOC prompt template ('TOC Homebrewery') not found for {self.PROVIDER_NAME}.")
        homebrewery_final_prompt = homebrewery_prompt_template.format(campaign_concept=campaign_concept)

        # These calls will fail until generate_text is implemented
        generated_display_toc = await self.generate_text(prompt=display_final_prompt, current_user=current_user, db=db, model=model, temperature=0.5, max_tokens=700) # Pass corrected args
        if not generated_display_toc:
             raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Display TOC succeeded but returned no usable content.")

        generated_homebrewery_toc = await self.generate_text(prompt=homebrewery_final_prompt, current_user=current_user, db=db, model=model, temperature=0.5, max_tokens=1000) # Pass corrected args
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
        if not await self.is_available(current_user=current_user, db=db): # Pass corrected args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        # This method also directly raises NotImplementedError.
        raise NotImplementedError(
            f"{self.PROVIDER_NAME.title()}LLMService.generate_section_content not implemented. "
            f"Received section_type: {section_type}"
        )

    async def list_available_models(self, current_user: UserModel, db: Session) -> List[Dict[str, any]]: # Changed params
        if not await self.is_available(current_user=current_user, db=db): # Pass corrected args
            print(f"Warning: {self.PROVIDER_NAME.title()} service not available. Cannot list models.")
            return []
        
        # Placeholder: DeepSeek has models like 'deepseek-chat' and 'deepseek-coder'.
        # A real implementation would fetch these from an API if available, or have them more robustly configured.
        print(f"Warning: {self.PROVIDER_NAME.title()}LLMService.list_available_models is returning a placeholder list.")

        placeholder_models = [
            {
                "id": "deepseek-chat",
                "name": f"{self.PROVIDER_NAME.title()} Chat (Placeholder)",
                "model_type": "chat",
                "supports_temperature": True, # Assuming chat models support temperature
                "capabilities": ["chat"]
            },
            {
                "id": "deepseek-coder",
                "name": f"{self.PROVIDER_NAME.title()} Coder (Placeholder)",
                "model_type": "completion", # Coder models are often more completion-focused
                                          # but could be "chat" if they have a conversational interface for coding.
                "supports_temperature": True, # Assuming coder models also support temperature
                "capabilities": ["completion", "code"]
            },
            # Example of a potentially larger chat model if one exists
            # {
            #     "id": "deepseek-chat-large",
            #     "name": f"{self.PROVIDER_NAME.title()} Chat Large (Placeholder)",
            #     "model_type": "chat",
            #     "supports_temperature": True,
            #     "capabilities": ["chat"]
            # },
        ]
        return placeholder_models

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # Placeholder, as DeepSeek (if OpenAI compatible) might use an AsyncClient that needs closing.
        # For now, assuming no explicit close is needed for a placeholder.
        print(f"{self.PROVIDER_NAME.title()}LLMService close method called (placeholder).")
        pass

    async def generate_homebrewery_toc_from_sections(self, sections_summary: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available. Please configure API key.")

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
        chat_history: Optional[List[models.ChatMessage]] = None,
        current_user: UserModel,
        db: Session,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 300
    ) -> str:
        if not await self.is_available(current_user=current_user, db=db):
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")

        # Construct messages list, similar to OpenAI
        messages = []

        # System message for character persona
        # Ensure character_notes are not excessively long for the system prompt.
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
            for message_item in chat_history: # Renamed to avoid conflict with outer 'messages'
                role = "user" if message_item.speaker.lower() == "user" else "assistant"
                messages.append({"role": role, "content": message_item.text})

        # Add the current user prompt
        messages.append({"role": "user", "content": user_prompt})

        # Here, you would typically call the DeepSeek API using the 'messages' list.
        # For example, using an OpenAI-compatible client:
        # client = AsyncOpenAI(api_key=self.effective_api_key, base_url="https://api.deepseek.com/v1")
        # chat_completion = await client.chat.completions.create(
        #     model=model or "deepseek-chat", # Or your preferred DeepSeek model
        #     messages=messages,
        #     temperature=temperature if temperature is not None else 0.7,
        #     max_tokens=max_tokens or 300
        # )
        # return chat_completion.choices[0].message.content.strip()

        raise NotImplementedError(
            f"{self.PROVIDER_NAME.title()}LLMService.generate_character_response not implemented. "
            f"Constructed messages: {messages}" # Log messages for debugging if needed
        )

# if __name__ == '__main__':
#     from app.core.config import settings
#     from dotenv import load_dotenv
#     from pathlib import Path
#     import os # Required for os.getenv

#     env_path_api_root = Path(__file__).resolve().parent.parent.parent / ".env"
#     if env_path_api_root.exists():
#         load_dotenv(dotenv_path=env_path_api_root)
    
#     settings.DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY")

#     print(f"--- Testing {DeepSeekLLMService.PROVIDER_NAME.title()}LLMService Placeholder ---")
    
#     # This block would need to be refactored to use asyncio.run() for async methods
#     # Example:
#     # import asyncio
#     # async def main_test():
#     #     available_check = False
#     #     try:
#     #         original_key = settings.DEEPSEEK_API_KEY
#     #         if not original_key or original_key in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]:
#     #             print(f"DEEPSEEK_API_KEY not found or is placeholder in .env. Using dummy key for {DeepSeekLLMService.PROVIDER_NAME.title()} service instantiation test.")
#     #             settings.DEEPSEEK_API_KEY = "dummy_ds_key_for_test"

#     #         service = DeepSeekLLMService() # __init__ is sync
#     #         available_check = await service.is_available()
#     #         print(f"{DeepSeekLLMService.PROVIDER_NAME.title()} Service initialized. Is Available: {available_check}")

#     #         if available_check:
#     #             print("\nAvailable DeepSeek Models (Placeholder List):")
#     #             models = await service.list_available_models()
#     #             for m in models:
#     #                 print(f"- {m['name']} (id: {m['id']})")

#     #             print("\nAttempting to call generate_text (expected NotImplementedError or LLMServiceUnavailableError):")
#     #             try:
#     #                 await service.generate_text("Test prompt for DeepSeek.")
#     #             except (NotImplementedError, LLMServiceUnavailableError) as e:
#     #                 print(f"Correctly caught: {e}")
#     #         else:
#     #             print(f"{DeepSeekLLMService.PROVIDER_NAME.title()} service is not available. Skipping further tests.")

#     #         settings.DEEPSEEK_API_KEY = original_key # Restore
#     #         await service.close()

#     #     except ValueError as ve:
#     #         print(f"Error during {DeepSeekLLMService.PROVIDER_NAME.title()} service initialization: {ve}")
#     #     except Exception as e:
#     #         print(f"An unexpected error occurred: {e}")

#     # if os.getenv("RUN_DEEPSEEK_TESTS") == "true": # Control execution if needed
#     #    asyncio.run(main_test())
#     # else:
#     #    print("Skipping DeepSeekLLMService async tests in __main__ block. Set RUN_DEEPSEEK_TESTS=true to run.")

#     print(f"--- End Test for {DeepSeekLLMService.PROVIDER_NAME.title()}LLMService ---")
