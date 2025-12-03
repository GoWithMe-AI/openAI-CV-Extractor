"""
Configuration management for the application.
"""
import os
from typing import Optional, List, Set
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "CV Extractor API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Extract and summarize CV information from PDF files"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AI Provider Configuration
    AI_PROVIDER: str = "openai"  # "openai" or "gemini"
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Using mini for cost efficiency
    
    # Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: str = ".pdf"  # Comma-separated or single value (e.g., ".pdf" or ".pdf,.doc,.docx")
    
    @property
    def allowed_extensions_set(self) -> Set[str]:
        """Get allowed extensions as a set."""
        if isinstance(self.ALLOWED_EXTENSIONS, str):
            # Handle comma-separated values or single value
            extensions = [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(',') if ext.strip()]
            return set(extensions)
        elif isinstance(self.ALLOWED_EXTENSIONS, (list, set)):
            return set(self.ALLOWED_EXTENSIONS)
        return {".pdf"}  # Default fallback
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

