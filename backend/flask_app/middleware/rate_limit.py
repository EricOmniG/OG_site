# ============================================================
#  flask_app/middleware/rate_limit.py
#  Redis-backed rate limiting per user per day
# ============================================================

import time
from flask import request, jsonify, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _get_rate_limit_key() -> str:
    """
    Key function for Flask-Limiter.
    Uses authenticated user ID when available, falls back to IP.
    """
    user = getattr(g, "user", None)
    if user and user.get("clerk_id"):
        return f"user:{user['clerk_id']}"
    return f"ip:{get_remote_address()}"


limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=[],          # No global default — limits applied per route
    storage_uri=None,           # Set from app config in init_rate_limiter()
    strategy="fixed-window",
)


def init_rate_limiter(app):
    redis_url = app.config.get("REDIS_URL", "redis://localhost:6379")
    limiter._storage_uri = redis_url
    limiter.init_app(app)


def daily_limit_for_plan(plan: str) -> str:
    """
    Return a Flask-Limiter limit string based on the user's plan.
    Used as a dynamic limit on inference routes (FastAPI side handles
    the actual enforcement; this is the Flask-side version for non-inference).
    """
    limits = {
        "free":     "50 per day",
        "pro":      "1000 per day",
        "advanced": "10000 per day",
    }
    return limits.get(plan, "50 per day")
