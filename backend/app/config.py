from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/studyqna")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Admin
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    
    # Storage
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
    ENCRYPT_STORAGE: bool = True
    
    # Email - Brevo API (Recommended)
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    BREVO_FROM_EMAIL: str = os.getenv("BREVO_FROM_EMAIL", "noreply@studyqna.com")
    BREVO_FROM_NAME: str = os.getenv("BREVO_FROM_NAME", "StudyQnA")
    
    # Email - SMTP (Alternative/Backup)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "StudyQnA <noreply@studyqna.com>")
    
    # Email Provider Selection
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "brevo")  # "brevo" or "smtp"
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # App
    APP_NAME: str = "StudyQnA Generator"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
    
    # CORS
    # For production, set CORS_ORIGINS in .env as comma-separated values
    # Example: CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
    _cors_origins_env: str = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS: List[str] = (
        _cors_origins_env.split(",") if _cors_origins_env else 
        ["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Limits
    MAX_PDF_SIZE_MB: int = 6  # Regular upload limit
    MAX_BOOK_PDF_SIZE_MB: int = 100  # Maximum size for book splitting feature
    MAX_IMAGE_SIZE_MB: int = 10  # Increased for mobile camera photos (typically 3-8MB)
    MAX_PDF_PAGES: int = 40
    MAX_FREE_PDF_PAGES: int = 10
    MAX_QUESTIONS_PER_GENERATE: int = 20
    PREMIUM_PDF_QUOTA: int = 15
    PREMIUM_IMAGE_QUOTA: int = 20
    PREMIUM_VALIDITY_DAYS: int = 30
    
    # Daily Generation Limits
    FREE_DAILY_GENERATION_LIMIT: int = int(os.getenv("FREE_DAILY_GENERATION_LIMIT", "10"))  # Free users: 10 generations/day
    PREMIUM_DAILY_GENERATION_LIMIT: int = int(os.getenv("PREMIUM_DAILY_GENERATION_LIMIT", "50"))  # Premium users: 50 generations/day
    
    # Total Questions Limit (Premium)
    PREMIUM_TOTAL_QUESTIONS_LIMIT: int = int(os.getenv("PREMIUM_TOTAL_QUESTIONS_LIMIT", "700"))  # Premium users: 700 questions total
    QUESTIONS_PER_PDF_UPLOAD: int = int(os.getenv("QUESTIONS_PER_PDF_UPLOAD", "20"))  # Each PDF upload allows 20 questions
    QUESTIONS_PER_IMAGE_UPLOAD: int = int(os.getenv("QUESTIONS_PER_IMAGE_UPLOAD", "20"))  # Each Image upload allows 20 questions
    
    # AI Usage Tracking
    AI_USAGE_THRESHOLD_TOKENS: int = int(os.getenv("AI_USAGE_THRESHOLD_TOKENS", "1000000"))  # Default: 1M tokens
    AI_USAGE_ALERT_EMAIL: str = os.getenv("AI_USAGE_ALERT_EMAIL", "")  # Email to send alerts to
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

