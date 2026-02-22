import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb"
    )
    
    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = APP_ENV == "development"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "300.0"))
    OLLAMA_MAX_CONCURRENCY: int = int(os.getenv("OLLAMA_MAX_CONCURRENCY", "2"))
    OLLAMA_CHUNK_SIZE: int = int(os.getenv("OLLAMA_CHUNK_SIZE", "1000"))
    OLLAMA_CHUNK_OVERLAP: int = int(os.getenv("OLLAMA_CHUNK_OVERLAP", "100"))
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "Intelligent Book Management System"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered Book Management Platform with recommendations and summaries"
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate critical settings"""
        if not cls.SECRET_KEY or cls.SECRET_KEY == "your-secret-key-change-in-production":
            if cls.APP_ENV == "production":
                raise ValueError("SECRET_KEY must be set in production!")


settings = Settings()
settings.validate()
