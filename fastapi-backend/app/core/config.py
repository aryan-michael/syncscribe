import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    # API Settings
    API_NAME: str = "Zoom Bot API"
    API_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"  # Fixed syntax: added quotes and colon
    PORT: int = 5000       # Fixed syntax: added type and colon
    DEBUG: bool = True     # Fixed syntax: added type and colon
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for now
    
    # Zoom API Credentials
    ZOOM_API_KEY: str = ""
    ZOOM_API_SECRET: str = ""
    ZOOM_SDK_KEY: str = ""
    ZOOM_SDK_SECRET: str = ""
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    ZOOM_ACCOUNT_ID: str = ""
    
    # External API Keys
    COHERE_API_KEY: str = ""
    
    # Google Cloud Settings
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    
    # File Storage
    MEETING_OUTPUTS_DIR: str = "meeting_outputs"
    TEMP_DIR: str = "temp"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        # Add this to allow extra fields from .env
        extra = "ignore"  # This allows extra fields from the environment

# Global settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.MEETING_OUTPUTS_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)