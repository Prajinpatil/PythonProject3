"""
Configuration Management - Secure Environment Variables
All sensitive data loaded from environment, never hardcoded
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import secrets


class Settings(BaseSettings):
    """
    Application Settings - Production Ready
    Uses pydantic-settings for automatic env var loading
    """
    
    # ========== APPLICATION ==========
    APP_NAME: str = "Surveillance Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # production, staging, development
    
    # ========== SECURITY ==========
    # CRITICAL: Change this in production! Use: openssl rand -hex 32
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password hashing
    PWD_CONTEXT_SCHEMES: list = ["bcrypt"]
    BCRYPT_ROUNDS: int = 12
    
    # ========== DATABASE ==========
    DATABASE_URL: str = "sqlite+aiosqlite:///./surveillance.db"
    DB_ECHO: bool = False  # Set True for SQL logging in dev
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # ========== CORS ==========
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # ========== RATE LIMITING ==========
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ========== THREAT DETECTION ==========
    THREAT_SCORE_THRESHOLD_CRITICAL: int = 80
    THREAT_SCORE_THRESHOLD_HIGH: int = 60
    THREAT_SCORE_THRESHOLD_MEDIUM: int = 40
    
    # Pattern detection
    PATTERN_DETECTION_ENABLED: bool = True
    PATTERN_TIME_WINDOW_MINUTES: int = 30
    PATTERN_MIN_EVENTS: int = 3
    
    # ========== ANALYTICS ==========
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_CACHE_TTL_SECONDS: int = 300
    EVENT_RETENTION_DAYS: int = 90
    
    # ========== NOTIFICATIONS ==========
    NOTIFICATION_ENABLED: bool = True
    ALERT_COOLDOWN_SECONDS: int = 300
    
    # Email (if using)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # Webhook
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_TIMEOUT: int = 10
    
    # ========== LOGGING ==========
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "surveillance.log"
    
    # ========== FILE UPLOAD (if needed) ==========
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".mp4"]
    
    # ========== API DOCUMENTATION ==========
    DOCS_ENABLED: bool = True
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings loader - Singleton pattern
    Called once, reused throughout application lifecycle
    """
    return Settings()


# ========== ENVIRONMENT-SPECIFIC OVERRIDES ==========
def get_database_url(environment: str) -> str:
    """
    Get appropriate database URL based on environment
    """
    urls = {
        "production": "postgresql://user:pass@prod-db:5432/surveillance",
        "staging": "postgresql://user:pass@staging-db:5432/surveillance",
        "development": "sqlite+aiosqlite:///./dev_surveillance.db",
        "testing": "sqlite+aiosqlite:///./test_surveillance.db"
    }
    return urls.get(environment, urls["development"])


def is_production() -> bool:
    """Check if running in production"""
    settings = get_settings()
    return settings.ENVIRONMENT == "production"


def is_development() -> bool:
    """Check if running in development"""
    settings = get_settings()
    return settings.ENVIRONMENT == "development"


# ========== SECURITY HEADERS ==========
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self' https://cdn.jsdelivr.net; "
        "worker-src blob:; "
    ),
    # keep your other headers as-is
}


# Export settings instance
settings = get_settings()
