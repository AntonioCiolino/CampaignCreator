from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.llm_service import AbstractLLMService, LLMServiceUnavailableError, LLMGenerationError
from app.services.feature_prompt_service import FeaturePromptService
from app.models import User as UserModel # Added UserModel import
# Removed import from llm_factory: from app.services.llm_factory import LLMServiceUnavailableError
# import os # For the __main__ block, commented out

class DeepSeekLLMService(AbstractLLMService):
    PROVIDER_NAME = "deepseek" # For easy reference

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        # DeepSeek might also have a specific base URL, but usually it's a standard OpenAI-compatible one.
        # self.api_url = settings.DEEPSEEK_API_URL 
        # Removed self.is_available() call from __init__
        if not (self.api_key and self.api_key not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"]):
            print(f"Warning: {self.PROVIDER_NAME.title()} API key not configured or is a placeholder.")

        self.feature_prompt_service = FeaturePromptService() # Added initialization
        # Placeholder for actual client initialization. DeepSeek often uses an OpenAI-compatible client.
        print(f"{self.PROVIDER_NAME.title()}LLMService initialized (placeholder).")

    async def is_available(self, _current_user: UserModel, _db: Session) -> bool: # Added _current_user, _db
        # Checks if essential configuration is present.
        return bool(self.api_key and self.api_key not in ["YOUR_DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE"])

    async def generate_text(self, prompt: str, _current_user: UserModel, db: Session, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 500) -> str: # Added _current_user, db
        if not await self.is_available(_current_user=_current_user, _db=_db): # Pass args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available. Please configure API key.")
        
        error_message = (
            f"{self.PROVIDER_NAME.title()}LLMService.generate_text is not implemented. "
            f"Prompt: '{prompt}', Model: '{model or 'default'}', Temp: {temperature}, MaxTokens: {max_tokens}"
        )
        print(f"WARNING: {error_message}")
        raise NotImplementedError(error_message)

    async def generate_campaign_concept(self, user_prompt: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> str: # Added current_user
        if not await self.is_available(_current_user=current_user, _db=db): # Pass args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        raise NotImplementedError(f"{self.PROVIDER_NAME.title()}LLMService.generate_campaign_concept not implemented.")

    async def generate_titles(self, campaign_concept: str, db: Session, current_user: UserModel, count: int = 5, model: Optional[str] = None) -> list[str]: # Added current_user
        if not await self.is_available(_current_user=current_user, _db=db): # Pass args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        raise NotImplementedError(f"{self.PROVIDER_NAME.title()}LLMService.generate_titles not implemented.")

    async def generate_toc(self, campaign_concept: str, db: Session, current_user: UserModel, model: Optional[str] = None) -> Dict[str, str]: # Added current_user
        if not await self.is_available(_current_user=current_user, _db=db): # Pass args
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
        generated_display_toc = await self.generate_text(prompt=display_final_prompt, _current_user=current_user, db=db, model=model, temperature=0.5, max_tokens=700) # Pass args
        if not generated_display_toc:
             raise LLMGenerationError(f"{self.PROVIDER_NAME.title()} API call for Display TOC succeeded but returned no usable content.")

        generated_homebrewery_toc = await self.generate_text(prompt=homebrewery_final_prompt, _current_user=current_user, db=db, model=model, temperature=0.5, max_tokens=1000) # Pass args
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
        if not await self.is_available(_current_user=current_user, _db=db): # Pass args
            raise LLMServiceUnavailableError(f"{self.PROVIDER_NAME.title()} service not available.")
        # This method also directly raises NotImplementedError.
        raise NotImplementedError(
            f"{self.PROVIDER_NAME.title()}LLMService.generate_section_content not implemented. "
            f"Received section_type: {section_type}"
        )

    async def list_available_models(self, _current_user: UserModel, _db: Session) -> List[Dict[str, str]]: # Added _current_user, _db
        if not await self.is_available(_current_user=_current_user, _db=_db): # Pass args
            print(f"Warning: {self.PROVIDER_NAME.title()} service not available. Cannot list models.")
            return []
        
        # Placeholder: DeepSeek has models like 'deepseek-chat' and 'deepseek-coder'.
        print(f"Warning: {self.PROVIDER_NAME.title()}LLMService.list_available_models is returning a placeholder list.")
        return [
            {"id": "deepseek-chat", "name": f"{self.PROVIDER_NAME.title()} Chat (Placeholder)", "capabilities": ["chat"]},
            {"id": "deepseek-coder", "name": f"{self.PROVIDER_NAME.title()} Coder (Placeholder)", "capabilities": ["completion", "code"]},
        ]

    async def close(self):
        """Close any persistent connections if the SDK requires it."""
        # Placeholder, as DeepSeek (if OpenAI compatible) might use an AsyncClient that needs closing.
        # For now, assuming no explicit close is needed for a placeholder.
        print(f"{self.PROVIDER_NAME.title()}LLMService close method called (placeholder).")
        pass

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
