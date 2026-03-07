# ============================================================
#  flask_app/config.py
# ============================================================
import os
from typing import List


class FlaskConfig:
    # Core
    SECRET_KEY: str         = os.getenv("APP_SECRET_KEY", "dev-secret-change-me")
    DEBUG: bool             = os.getenv("DEBUG", "true").lower() == "true"
    TESTING: bool           = False
    ENV: str                = os.getenv("APP_ENV", "development")

    # CORS
    CORS_ORIGINS: List[str] = [
        o.strip() for o in
        os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ]

    # Database (SQLAlchemy — used for Flask-Migrate)
    SQLALCHEMY_DATABASE_URI: str     = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_POOL_SIZE: int        = int(os.getenv("DATABASE_POOL_SIZE", 5))
    SQLALCHEMY_MAX_OVERFLOW: int     = int(os.getenv("DATABASE_MAX_OVERFLOW", 10))

    # Supabase
    SUPABASE_URL: str                = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str   = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Clerk
    CLERK_SECRET_KEY: str            = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_WEBHOOK_SECRET: str        = os.getenv("CLERK_WEBHOOK_SECRET", "")
    CLERK_JWT_KEY: str               = os.getenv("CLERK_JWT_KEY", "")

    # Stripe
    STRIPE_SECRET_KEY: str           = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str       = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_PRO_MONTHLY: str    = os.getenv("STRIPE_PRICE_PRO_MONTHLY", "")
    STRIPE_PRICE_PRO_ANNUAL: str     = os.getenv("STRIPE_PRICE_PRO_ANNUAL", "")
    STRIPE_PRICE_ADV_MONTHLY: str    = os.getenv("STRIPE_PRICE_ADVANCED_MONTHLY", "")
    STRIPE_PRICE_ADV_ANNUAL: str     = os.getenv("STRIPE_PRICE_ADVANCED_ANNUAL", "")

    # Email (Microsoft Graph)
    MS_TENANT_ID: str                = os.getenv("MS_TENANT_ID", "")
    MS_CLIENT_ID: str                = os.getenv("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET: str            = os.getenv("MS_CLIENT_SECRET", "")
    MS_SENDER_EMAIL: str             = os.getenv("MS_SENDER_EMAIL", "")
    EMAIL_BACKEND: str               = os.getenv("EMAIL_BACKEND", "graph")
    # SMTP fallback
    SMTP_HOST: str                   = os.getenv("SMTP_HOST", "smtp.office365.com")
    SMTP_PORT: int                   = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str               = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str               = os.getenv("SMTP_PASSWORD", "")

    # AWS
    AWS_REGION: str                  = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET: str               = os.getenv("AWS_S3_BUCKET", "omnigenius-assets")
    AWS_CLOUDFRONT_URL: str          = os.getenv("AWS_CLOUDFRONT_URL", "")

    # Redis
    REDIS_URL: str                   = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Rate limits
    RATE_LIMIT_FREE_DAILY: int       = int(os.getenv("RATE_LIMIT_FREE_DAILY", 50))
    RATE_LIMIT_PRO_DAILY: int        = int(os.getenv("RATE_LIMIT_PRO_DAILY", 1000))

    # Security
    API_KEY_PREFIX: str              = os.getenv("API_KEY_PREFIX", "og-")
    INTERNAL_API_SECRET: str         = os.getenv("INTERNAL_API_SECRET", "")
    ADMIN_EMAILS: List[str]          = [
        e.strip() for e in
        os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
    ]

    # Feature flags
    FEATURE_WAITLIST_MODE: bool      = os.getenv("FEATURE_WAITLIST_MODE", "false").lower() == "true"
    FEATURE_SHARING_ENABLED: bool    = os.getenv("FEATURE_SHARING_ENABLED", "true").lower() == "true"

    # Sentry
    SENTRY_DSN: str                  = os.getenv("SENTRY_DSN", "")

    @classmethod
    def from_env(cls) -> "FlaskConfig":
        env = os.getenv("APP_ENV", "development")
        mapping = {
            "production":  ProductionConfig,
            "staging":     StagingConfig,
            "testing":     TestingConfig,
        }
        return mapping.get(env, DevelopmentConfig)()


class DevelopmentConfig(FlaskConfig):
    DEBUG = True


class StagingConfig(FlaskConfig):
    DEBUG = False


class ProductionConfig(FlaskConfig):
    DEBUG = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20


class TestingConfig(FlaskConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
