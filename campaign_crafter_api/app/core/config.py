from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Existing keys
    OPENAI_API_KEY: str = "YOUR_OPENAI_API_KEY" 
    GEMINI_API_KEY: Optional[str] = "YOUR_GEMINI_API_KEY" 

    # Llama Configuration
    LLAMA_API_KEY: Optional[str] = "YOUR_LLAMA_API_KEY" 
    LLAMA_API_URL: Optional[str] = None 

    # DeepSeek Configuration
    DEEPSEEK_API_KEY: Optional[str] = "YOUR_DEEPSEEK_API_KEY"
    
    # OpenAI DALL-E Image Generation Settings
    OPENAI_DALLE_MODEL_NAME: str = "dall-e-3"
    OPENAI_DALLE_DEFAULT_IMAGE_SIZE: str = "1024x1024"
    OPENAI_DALLE_DEFAULT_IMAGE_QUALITY: str = "standard"

    # Generic Local LLM Provider (OpenAI-Compatible API)
    LOCAL_LLM_PROVIDER_NAME: str = "local_llm" # Used as a key in the LLM factory
    LOCAL_LLM_API_BASE_URL: Optional[str] = None # e.g., "http://localhost:11434/v1" for Ollama's OpenAI compat endpoint
    LOCAL_LLM_DEFAULT_MODEL_ID: Optional[str] = None # e.g., "mistral:latest" or just "mistral"

    # Database URL (example, if you had one)
    # DATABASE_URL: str = "sqlite:///./test.db"

    # JWT Settings (example, if you had them)
    # SECRET_KEY: str = "your_super_secret_key"
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore' 

settings = Settings()

# Optional: For easy debugging of loaded settings
# print(f"OpenAI Key loaded: {'Yes' if settings.OPENAI_API_KEY != 'YOUR_OPENAI_API_KEY' else 'No (Using default placeholder)'}")
# print(f"Local LLM Base URL: {settings.LOCAL_LLM_API_BASE_URL}")
# print(f"Local LLM Provider Name: {settings.LOCAL_LLM_PROVIDER_NAME}")
# print(f"Local LLM Default Model: {settings.LOCAL_LLM_DEFAULT_MODEL_ID}")
