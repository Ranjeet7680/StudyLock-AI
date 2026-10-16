"""
StudyLock AI - Application Configuration
Ref: StudyLock AI Architecture Specification Section 24.2
"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_TITLE: str = "StudyLock AI API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # Database: Supports SQLite for zero-setup local dev & Postgres for production
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./studylock.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "studylock-ai-super-secret-key-for-development-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "chrome-extension://*",
        "*"
    ]
    
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
