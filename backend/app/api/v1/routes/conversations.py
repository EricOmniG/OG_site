# ============================================================
#  app/api/v1/routes/conversations.py
# ============================================================
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


@router.get("", summary="List conversations")
async def list_conversations(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mode: Optional[str] = Query(None),        # chat | search | reason | auto
    search: Optional[str] = Query(None),
):
    """
    Paginated list of the user's conversations, newest first.
    TODO: SELECT from conversations WHERE user_id = ? ORDER BY updated_at DESC
    """
    pass


@router.get("/{conversation_id}", summary="Get conversation with messages")
async def get_conversation(conversation_id: str, request: Request):
    """
    Return conversation metadata + all messages.
    TODO: fetch conversation + messages, verify ownership
    """
    pass


@router.patch("/{conversation_id}", summary="Rename conversation")
async def update_conversation(conversation_id: str, request: Request):
    """
    Update conversation title.
    TODO: UPDATE conversations SET title = ? WHERE id = ? AND user_id = ?
    """
    pass


@router.delete("/{conversation_id}", status_code=204, summary="Delete conversation")
async def delete_conversation(conversation_id: str, request: Request):
    """
    Hard delete a conversation and all its messages.
    TODO: DELETE cascade from messages, then conversations
    """
    pass


@router.delete("", status_code=204, summary="Clear all conversation history")
async def clear_all_conversations(request: Request):
    """
    Delete all conversations for the authenticated user.
    TODO: DELETE FROM conversations WHERE user_id = ?
    """
    pass


# ============================================================
#  app/api/v1/routes/sharing.py
# ============================================================
from fastapi import APIRouter as _R2
sharing_router = _R2()


class CreateShareRequest(BaseModel):
    conversation_id: str
    expires_in_days: Optional[int] = None   # None = never expires


@sharing_router.post("", status_code=201, summary="Create a share link")
async def create_share(body: CreateShareRequest, request: Request):
    """
    Generate a public share link for a conversation.
    Creates a shared_conversations row with a random slug.
    TODO: generate slug, insert shared_conversations, return share URL
    """
    pass


@sharing_router.get("/{slug}", summary="Fetch a shared conversation (public)")
async def get_shared(slug: str):
    """
    Public endpoint — no auth required.
    Returns the conversation + messages for a valid, non-expired share link.
    Increments view_count.
    TODO: SELECT from shared_conversations WHERE slug = ? AND NOT expired
    """
    pass


@sharing_router.delete("/{slug}", status_code=204, summary="Revoke a share link")
async def revoke_share(slug: str, request: Request):
    """
    Delete the share link. Verify ownership before deleting.
    TODO: DELETE FROM shared_conversations WHERE slug = ? AND user_id = ?
    """
    pass


@sharing_router.post("/{slug}/fork", status_code=201, summary="Fork a shared conversation")
async def fork_shared(slug: str, request: Request):
    """
    Copy a shared conversation into the authenticated user's account.
    Creates a new conversation + clones all messages.
    TODO: clone rows, return new conversation_id
    """
    pass


# ============================================================
#  app/api/v1/routes/apikeys.py
# ============================================================
from fastapi import APIRouter as _R3
apikeys_router = _R3()


class CreateKeyRequest(BaseModel):
    label: str
    rate_limit_per_minute: int = 60
    expires_in_days: Optional[int] = None


@apikeys_router.get("", summary="List API keys")
async def list_keys(request: Request):
    """
    Return all API keys for the user (masked). Requires Advanced plan.
    TODO: SELECT from api_keys WHERE user_id = ? AND revoked_at IS NULL
    """
    pass


@apikeys_router.post("", status_code=201, summary="Create API key")
async def create_key(body: CreateKeyRequest, request: Request):
    """
    Generate a new og- prefixed API key. Returns the full key ONCE.
    Stores only the SHA-256 hash in the database.
    TODO:
    1. Verify user has Advanced plan
    2. Generate: og- + secrets.token_urlsafe(32)
    3. Hash with SHA-256, store hash + metadata
    4. Return full key (never stored, shown once)
    """
    pass


@apikeys_router.delete("/{key_id}", status_code=204, summary="Revoke API key")
async def revoke_key(key_id: str, request: Request):
    """
    Soft-delete (set revoked_at). Key immediately stops working.
    TODO: UPDATE api_keys SET revoked_at = now() WHERE id = ? AND user_id = ?
    """
    pass


# ============================================================
#  app/api/v1/routes/billing.py
# ============================================================
from fastapi import APIRouter as _R4, HTTPException
billing_router = _R4()


class CreateCheckoutRequest(BaseModel):
    price_id: str               # Stripe price ID
    success_url: str
    cancel_url: str


@billing_router.post("/checkout", status_code=201, summary="Create Stripe checkout session")
async def create_checkout(body: CreateCheckoutRequest, request: Request):
    """
    Create a Stripe Checkout session for plan upgrade.
    TODO: stripe.checkout.sessions.create with price_id, attach clerk user metadata
    """
    pass


@billing_router.get("/portal", summary="Create Stripe customer portal session")
async def billing_portal(request: Request):
    """
    Redirect user to Stripe Customer Portal for plan management and invoices.
    TODO: stripe.billing_portal.sessions.create, return URL
    """
    pass


@billing_router.get("/subscription", summary="Get current subscription details")
async def get_subscription(request: Request):
    """
    Return current plan, status, renewal date, and usage.
    TODO: fetch from subscriptions table + Stripe API for invoice data
    """
    pass


@billing_router.post("/webhooks/stripe", summary="Handle Stripe webhook events")
async def stripe_webhook(request: Request):
    """
    Process Stripe events: checkout.session.completed, customer.subscription.updated,
    customer.subscription.deleted, invoice.payment_failed.
    Validates Stripe-Signature header before processing.

    TODO:
    1. Verify signature with STRIPE_WEBHOOK_SECRET
    2. Handle event types:
       - checkout.session.completed → activate subscription, update users.plan
       - subscription.updated → sync plan changes
       - subscription.deleted → downgrade to free
       - invoice.payment_failed → flag subscription, notify user
    """
    pass


# ============================================================
#  app/api/v1/routes/waitlist.py
# ============================================================
from fastapi import APIRouter as _R5
from pydantic import EmailStr
waitlist_router = _R5()


class WaitlistRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = None   # twitter | producthunt | direct | referral


@waitlist_router.post("", status_code=201, summary="Join the waitlist")
async def join_waitlist(body: WaitlistRequest):
    """
    Public endpoint — no auth required.
    Add an email to the waitlist. Deduplicates on email.
    TODO: INSERT INTO waitlist ON CONFLICT (email) DO NOTHING
    """
    pass


@waitlist_router.post("/careers", status_code=201, summary="Join careers notification list")
async def join_careers(body: WaitlistRequest):
    """
    Public endpoint. Separate table from product waitlist.
    TODO: INSERT INTO careers_interest
    """
    pass


# ============================================================
#  app/api/v1/routes/uploads.py
# ============================================================
from fastapi import APIRouter as _R6, UploadFile, File
uploads_router = _R6()


@uploads_router.post("/file", status_code=201, summary="Upload a file for use in a conversation")
async def upload_file(file: UploadFile = File(...), request: Request = None):
    """
    Upload PDF or image to S3 for use as conversation context.
    Max 10MB. Returns a file_id for referencing in chat requests.

    TODO:
    1. Validate type (PDF, JPEG, PNG, WEBP) and size
    2. Upload to S3: uploads/{user_id}/{uuid}.{ext}
    3. For PDFs: extract text via pdfplumber, store in file_contents
    4. For images: store S3 key for vision pass-through
    5. INSERT INTO uploaded_files, return file_id
    """
    pass


# ============================================================
#  app/api/v1/routes/admin.py
#  Internal admin endpoints — protected by INTERNAL_API_SECRET header
# ============================================================
from fastapi import APIRouter as _R7
admin_router = _R7()


@admin_router.get("/users", summary="[Admin] List all users")
async def admin_list_users(request: Request, limit: int = 50, offset: int = 0):
    """TODO: paginated user list with plan + usage stats"""
    pass


@admin_router.patch("/users/{user_id}/plan", summary="[Admin] Change user plan")
async def admin_change_plan(user_id: str, request: Request):
    """TODO: update plan, sync Stripe subscription if active"""
    pass


@admin_router.post("/users/{user_id}/suspend", summary="[Admin] Suspend user")
async def admin_suspend_user(user_id: str, request: Request):
    """TODO: set users.suspended_at, revoke Clerk sessions"""
    pass


@admin_router.delete("/users/{user_id}", status_code=204, summary="[Admin] Delete user")
async def admin_delete_user(user_id: str, request: Request):
    """TODO: full deletion cascade"""
    pass


@admin_router.get("/waitlist", summary="[Admin] View waitlist")
async def admin_waitlist(request: Request):
    """TODO: return waitlist with invite status"""
    pass


@admin_router.post("/waitlist/invite", summary="[Admin] Invite waitlist users")
async def admin_invite(request: Request):
    """TODO: mark as invited, trigger email"""
    pass


@admin_router.get("/stats", summary="[Admin] Platform stats")
async def admin_stats(request: Request):
    """TODO: aggregate KPIs — users, MRR, queries, errors"""
    pass


# ============================================================
#  app/api/v1/routes/health.py
# ============================================================
from fastapi import APIRouter as _R8
from datetime import datetime
health_router = _R8()


@health_router.get("", summary="Health check")
async def health():
    """
    Simple liveness check for AWS ALB / API Gateway health probes.
    Returns 200 immediately.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "version": "0.1.0"}


@health_router.get("/deep", summary="Deep health check")
async def deep_health():
    """
    Checks connectivity to Supabase and Redis.
    Returns degraded status if any dependency is unreachable.
    TODO: ping Supabase, ping Redis, return component statuses
    """
    return {
        "status": "ok",
        "components": {
            "database": "ok",    # TODO: real check
            "redis": "ok",       # TODO: real check
            "orca": "ok",        # TODO: real check
        }
    }


# Re-export all routers with correct names for main.py
from fastapi import APIRouter

# Each file that main.py imports should expose `router`
# These are set at module level in their own files.
# This combined file is for reference — split into individual files in production.
router = health_router
