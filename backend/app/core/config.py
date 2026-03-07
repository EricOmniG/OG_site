# ============================================================
#  app/core/config.py
#  Pydantic settings — reads from environment / .env file
# ============================================================

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "omnigenius"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    APP_SECRET_KEY: str = ""
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS — split comma-separated string into list
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [o.strip() for o in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 5

    # Clerk
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = ""
    CLERK_JWT_KEY: str = ""

    # ORCA
    ORCA_SERVICE_URL: str = ""
    ORCA_SERVICE_API_KEY: str = ""
    ORCA_MODEL_ID: str = "chimera-v1"
    ORCA_MAX_TOKENS: int = 4096
    ORCA_TIMEOUT_SECONDS: int = 60
    ORCA_STREAM_ENABLED: bool = True

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO_MONTHLY: str = ""
    STRIPE_PRICE_PRO_ANNUAL: str = ""
    STRIPE_PRICE_ADVANCED_MONTHLY: str = ""
    STRIPE_PRICE_ADVANCED_ANNUAL: str = ""

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "omnigenius-assets"
    AWS_CLOUDFRONT_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL_DEFAULT: int = 3600

    # Rate limits
    RATE_LIMIT_FREE_DAILY: int = 50
    RATE_LIMIT_PRO_DAILY: int = 1000
    RATE_LIMIT_ADVANCED_DAILY: int = -1
    RATE_LIMIT_API_PER_MINUTE_ADVANCED: int = 60

    # Security
    API_KEY_PREFIX: str = "og-"
    API_KEY_LENGTH: int = 32
    MAX_UPLOAD_SIZE_MB: int = 10

    # Email — Microsoft Outlook / Graph API
    MS_TENANT_ID: str = ""
    MS_CLIENT_ID: str = ""
    MS_CLIENT_SECRET: str = ""
    MS_SENDER_EMAIL: str = ""
    # SMTP fallback
    SMTP_HOST: str = "smtp.office365.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str = "Omnigenius"
    SMTP_FROM_EMAIL: str = ""
    EMAIL_BACKEND: str = "graph"   # graph | smtp

    # Feature flags
    FEATURE_SHARING_ENABLED: bool = True
    FEATURE_API_ACCESS_ENABLED: bool = True
    FEATURE_WAITLIST_MODE: bool = False

    # Monitoring
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Internal
    INTERNAL_API_SECRET: str = ""
    ADMIN_EMAILS: str = ""

    @property
    def admin_emails_list(self) -> List[str]:
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
