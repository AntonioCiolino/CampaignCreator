from pydantic_settings import BaseSettings

from typing import Optional # Ensure Optional is imported

class Settings(BaseSettings):
    OPENAI_API_KEY: str = "YOUR_API_KEY_HERE" # Default value if not in .env
    GEMINI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
