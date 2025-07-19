from pydantic_settings import BaseSettings
from typing import Optional, List, Dict

class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS_CSV: Optional[str] = None

    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        if self.BACKEND_CORS_ORIGINS_CSV:
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS_CSV.split(',')]
        return ["http://localhost:3000"] # Default if the env var is not set

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

    # Image Storage Settings
    IMAGE_STORAGE_PATH: str = "/app/static/generated_images/"
    IMAGE_BASE_URL: str = "/static/generated_images/" # URL path to access stored images

    # Azure Blob Storage Settings
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = None
    AZURE_STORAGE_CONTAINER_NAME: Optional[str] = "campaignimages" # Default container name
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None

    # Stable Diffusion Image Generation Settings
    STABLE_DIFFUSION_API_KEY: Optional[str] = "YOUR_STABLE_DIFFUSION_API_KEY_HERE"
    # STABLE_DIFFUSION_API_URL: Optional[str] = "YOUR_STABLE_DIFFUSION_API_URL_HERE" # Old one
    STABLE_DIFFUSION_API_BASE_URL: Optional[str] = "https://api.stability.ai" # Base URL
    STABLE_DIFFUSION_ENGINES: Dict[str, str] = {
        "core": "v2beta/stable-image/generate/core",
        "ultra": "v2beta/stable-image/generate/ultra", # Assumed
        "sd3": "v2beta/stable-image/generate/sd3"      # Assumed
    }
    STABLE_DIFFUSION_DEFAULT_ENGINE: str = "core" # New default engine
    STABLE_DIFFUSION_DEFAULT_MODEL: Optional[str] = "stable-diffusion-v1-5" # Model checkpoint name if API supports it
    STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE: str = "512x512"
    STABLE_DIFFUSION_DEFAULT_STEPS: int = 30
    STABLE_DIFFUSION_DEFAULT_CFG_SCALE: float = 7.5

    # Generic Local LLM Provider (OpenAI-Compatible API)
    LOCAL_LLM_PROVIDER_NAME: str = "local_llm" # Used as a key in the LLM factory
    LOCAL_LLM_API_BASE_URL: Optional[str] = None # e.g., "http://localhost:11434/v1" for Ollama's OpenAI compat endpoint
    LOCAL_LLM_DEFAULT_MODEL_ID: Optional[str] = None # e.g., "mistral:latest" or just "mistral"

    DATABASE_URL: str = "sqlite:///./campaign_crafter_default.db"

    # JWT Settings
    SECRET_KEY: str = "your-secret-key"  # TODO: Load from environment variable for production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440 # 1 day

    # Chat Summarization Settings
    CHAT_SUMMARIZATION_INTERVAL: int = 20  # Summarize after N total messages (user + AI)
    CHAT_MIN_MESSAGES_FOR_SUMMARY_TRIGGER: int = 30 # Min total messages before first summary
    CHAT_MIN_MESSAGES_FOR_SUMMARY_CRUD: int = 15 # Min messages in conversation before crud.update_conversation_summary attempts to summarize
    CHAT_RECENT_MESSAGES_TO_EXCLUDE_FROM_SUMMARY: int = 5 # Number of recent messages to keep out of summary, send as direct short-term context

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore' 

settings = Settings()
