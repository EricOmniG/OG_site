# ============================================================
#  OMNIGENIUS — app/main.py
#  FastAPI application entrypoint
#  Runs locally with: uvicorn app.main:app --reload
#  Deployed as AWS Lambda via Mangum adapter
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.auth import ClerkAuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

from app.api.v1.routes import (
    auth,
    chat,
    search,
    reason,
    users,
    conversations,
    sharing,
    apikeys,
    billing,
    waitlist,
    uploads,
    admin,
    health,
)

# ── Setup ────────────────────────────────────────────────────
setup_logging()

app = FastAPI(
    title="Omnigenius API",
    description="The ORCA model API — Chat, Search, Reason, and Auto modes.",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,   # disable Swagger in prod
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom Middleware ─────────────────────────────────────────
app.add_middleware(ClerkAuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# ── Routers ──────────────────────────────────────────────────
API_PREFIX = "/v1"

app.include_router(health.router,         prefix="/health",           tags=["Health"])
app.include_router(auth.router,           prefix=f"{API_PREFIX}/auth",          tags=["Auth"])
app.include_router(chat.router,           prefix=f"{API_PREFIX}/chat",          tags=["Chat"])
app.include_router(search.router,         prefix=f"{API_PREFIX}/search",        tags=["Search"])
app.include_router(reason.router,         prefix=f"{API_PREFIX}/reason",        tags=["Reason"])
app.include_router(users.router,          prefix=f"{API_PREFIX}/users",         tags=["Users"])
app.include_router(conversations.router,  prefix=f"{API_PREFIX}/conversations",  tags=["Conversations"])
app.include_router(sharing.router,        prefix=f"{API_PREFIX}/share",         tags=["Sharing"])
app.include_router(apikeys.router,        prefix=f"{API_PREFIX}/apikeys",       tags=["API Keys"])
app.include_router(billing.router,        prefix=f"{API_PREFIX}/billing",       tags=["Billing"])
app.include_router(waitlist.router,       prefix=f"{API_PREFIX}/waitlist",      tags=["Waitlist"])
app.include_router(uploads.router,        prefix=f"{API_PREFIX}/uploads",       tags=["Uploads"])
app.include_router(admin.router,          prefix=f"{API_PREFIX}/admin",         tags=["Admin"])

# ── Lambda Handler ────────────────────────────────────────────
# Mangum wraps FastAPI for AWS Lambda + API Gateway
handler = Mangum(app, lifespan="off")
