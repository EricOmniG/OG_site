# ============================================================
#  app/api/v1/routes/users.py
# ============================================================
from fastapi import APIRouter, Request, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdatePreferencesRequest(BaseModel):
    theme: Optional[str] = None          # dark | light | system
    font_size: Optional[int] = None      # 12-18
    show_reasoning: Optional[bool] = None
    compact_view: Optional[bool] = None
    animate_responses: Optional[bool] = None
    notif_product_updates: Optional[bool] = None
    notif_usage_alerts: Optional[bool] = None
    notif_marketing: Optional[bool] = None
    allow_model_improvement: Optional[bool] = None
    conversation_history_enabled: Optional[bool] = None


@router.get("/me", summary="Get current user profile")
async def get_profile(request: Request):
    """
    Returns the authenticated user's full profile, preferences, plan, and usage stats.
    TODO: fetch from Supabase users + user_preferences tables
    """
    pass


@router.patch("/me", summary="Update profile fields")
async def update_profile(body: UpdateProfileRequest, request: Request):
    """
    Partial update of profile fields.
    TODO: validate, update Clerk user + Supabase users row
    """
    pass


@router.patch("/me/preferences", summary="Update user preferences")
async def update_preferences(body: UpdatePreferencesRequest, request: Request):
    """
    Update appearance, notification, and privacy preferences.
    TODO: upsert user_preferences row in Supabase
    """
    pass


@router.post("/me/avatar", summary="Upload avatar image")
async def upload_avatar(file: UploadFile = File(...), request: Request = None):
    """
    Upload a profile picture. Accepts JPEG, PNG, GIF, WEBP. Max 5MB.
    Uploads to S3, stores CloudFront URL in users.avatar_url.
    TODO:
    1. Validate file type + size
    2. Resize to 400x400 (Pillow)
    3. Upload to S3 under avatars/{user_id}/avatar.webp
    4. Update users.avatar_url in Supabase
    """
    pass


@router.delete("/me/avatar", status_code=204, summary="Remove avatar")
async def remove_avatar(request: Request):
    """Delete avatar from S3 and clear avatar_url."""
    pass


@router.get("/me/usage", summary="Get usage stats for current billing period")
async def get_usage(request: Request):
    """
    Returns queries used today, this month, and all-time, broken down by mode.
    TODO: aggregate from messages table filtered by user_id + date range
    """
    pass


@router.post("/me/export", status_code=202, summary="Request data export")
async def request_export(request: Request):
    """
    Queue a data export job. User receives download link via email within 24h.
    TODO: enqueue Lambda async job, log export_requests row
    """
    pass


@router.delete("/me", status_code=204, summary="Delete account")
async def delete_account(request: Request):
    """
    Permanently delete the account. Cancels Stripe subscription, deletes
    Clerk user, anonymises Supabase rows (GDPR soft delete).
    TODO: cancel Stripe sub, delete Clerk user, mark users.deleted_at
    """
    pass
