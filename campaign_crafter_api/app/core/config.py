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
    OPENAI_DALLE_DEFAULT_IMAGE_SIZE: str = "1024x1024" # Valid sizes for DALL-E 3: 1024x1024, 1792x1024, 1024x1792
    OPENAI_DALLE_DEFAULT_IMAGE_QUALITY: str = "standard" # Valid qualities for DALL-E 3: "standard", "hd"

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
# print(f"DALL-E Model: {settings.OPENAI_DALLE_MODEL_NAME}")
# print(f"DALL-E Size: {settings.OPENAI_DALLE_DEFAULT_IMAGE_SIZE}")
# print(f"DALL-E Quality: {settings.OPENAI_DALLE_DEFAULT_IMAGE_QUALITY}")
