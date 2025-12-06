import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Sales Agent"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/sales_agent_db")
    
    # ML Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "disabled")
    
    # Search Settings
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")
    BING_SEARCH_API_KEY: str = os.getenv("BING_SEARCH_API_KEY", "")
    
    # Email Settings (SMTP for sending)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 1025))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "agent@salesbot.ai")
    
    # Email Monitoring Settings (IMAP for reading)
    IMAP_HOST: str = os.getenv("IMAP_HOST", "imap.gmail.com")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", 993))
    IMAP_USER: str = os.getenv("IMAP_USER", "")
    IMAP_PASS: str = os.getenv("IMAP_PASS", "")
    
    # MailHog Settings (testing)
    MAILHOG_API_URL: str = os.getenv("MAILHOG_API_URL", "http://localhost:8025")
    
    # Monitoring Settings
    EMAIL_CHECK_INTERVAL_MINUTES: int = int(os.getenv("EMAIL_CHECK_INTERVAL_MINUTES", 5))
    AUTO_RETRAIN_ENABLED: bool = os.getenv("AUTO_RETRAIN_ENABLED", "true").lower() == "true"
    MIN_LABELS_FOR_RETRAIN: int = int(os.getenv("MIN_LABELS_FOR_RETRAIN", 50))
    SENTIMENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("SENTIMENT_CONFIDENCE_THRESHOLD", 0.7))
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default-secret-key-if-not-set")
    
    # LangGraph Feature Flag (default: false = use existing agent)
    USE_LANGGRAPH: bool = os.getenv("USE_LANGGRAPH", "false").lower() == "true"
    
    class Config:
        case_sensitive = True

settings = Settings()
