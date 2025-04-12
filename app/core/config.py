import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the project root
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_NAME: str

    # JWT
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # URLs (Optional, load if needed for redirects etc.)
    # BACKEND_URL: str | None = None
    # FRONTEND_URL: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore" # Ignore extra fields from .env

settings = Settings()