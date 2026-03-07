# ============================================================
#  flask_app/middleware/auth.py
#  Clerk JWT verification + og- API key verification for Flask
# ============================================================

import os
import hashlib
import functools
from typing import Optional

import httpx
from flask import request, jsonify, g, current_app
from jose import jwt, JWTError


# ── Clerk JWT verification ────────────────────────────────────

def _verify_clerk_jwt(token: str) -> Optional[dict]:
    """
    Verify a Clerk-issued JWT using the public key from CLERK_JWT_KEY.
    Returns the decoded payload dict, or None if invalid.

    TODO:
    1. Load PEM public key from current_app.config["CLERK_JWT_KEY"]
    2. Decode with python-jose: jwt.decode(token, key, algorithms=["RS256"])
    3. Verify iss matches your Clerk frontend API URL
    4. Return claims dict on success, None on JWTError
    """
    try:
        key = current_app.config.get("CLERK_JWT_KEY", "")
        if not key:
            return None
        payload = jwt.decode(token, key, algorithms=["RS256"])
        return payload
    except JWTError:
        return None


def _verify_api_key(raw_key: str) -> Optional[dict]:
    """
    Verify an og- prefixed API key.
    Hashes the raw key with SHA-256 and looks it up in Supabase api_keys table.
    Returns the associated user row, or None if not found / revoked.

    TODO:
    1. Hash: hashlib.sha256(raw_key.encode()).hexdigest()
    2. Query Supabase: SELECT * FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL
    3. Check expiry if expires_at is set
    4. Return user dict on success, None otherwise
    """
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    # TODO: query Supabase with key_hash
    return None


def resolve_auth() -> Optional[dict]:
    """
    Extract and verify auth from the current request.
    Checks Authorization: Bearer <jwt> first, then X-API-Key: og-<key>.
    Sets g.user and g.auth_method on success.
    Returns user dict or None.
    """
    # 1. Try Bearer JWT
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = _verify_clerk_jwt(token)
        if payload:
            g.user = {"clerk_id": payload.get("sub"), "plan": payload.get("plan", "free")}
            g.auth_method = "jwt"
            return g.user

    # 2. Try API key
    api_key = request.headers.get("X-API-Key", "")
    prefix = current_app.config.get("API_KEY_PREFIX", "og-")
    if api_key.startswith(prefix):
        user = _verify_api_key(api_key)
        if user:
            g.user = user
            g.auth_method = "api_key"
            return g.user

    return None


def clerk_required(f):
    """
    Decorator: require valid Clerk JWT or og- API key.
    Sets g.user on success. Returns 401 if missing or invalid.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user = resolve_auth()
        if not user:
            return jsonify({"detail": "Authentication required", "status": 401}), 401
        return f(*args, **kwargs)
    return decorated


def advanced_plan_required(f):
    """
    Decorator: require Advanced plan.
    Must be used after @clerk_required.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        plan = getattr(g, "user", {}).get("plan", "free")
        if plan != "advanced":
            return jsonify({"detail": "Advanced plan required", "status": 403}), 403
        return f(*args, **kwargs)
    return decorated


def internal_only(f):
    """
    Decorator: require X-Internal-Secret header.
    Used to protect admin endpoints from public access.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        secret = request.headers.get("X-Internal-Secret", "")
        expected = current_app.config.get("INTERNAL_API_SECRET", "")
        if not expected or secret != expected:
            return jsonify({"detail": "Forbidden", "status": 403}), 403
        return f(*args, **kwargs)
    return decorated
