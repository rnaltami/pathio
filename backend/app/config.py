# backend/app/config.py
from pydantic_settings import BaseSettings  # <-- v2 import

class Settings(BaseSettings):
    openai_api_key: str | None = None
    allow_origins: str = "http://localhost:8501"

    # pydantic v2 config style
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()
