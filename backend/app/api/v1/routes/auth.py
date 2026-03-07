# ============================================================
#  app/api/v1/routes/auth.py
# ============================================================
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: SignUpRequest):
    """
    Create a new user account via Clerk.
    - Creates Clerk user
    - Creates Supabase user profile row
    - Returns session token
    TODO: implement Clerk user creation, then insert into public.users
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/signin", response_model=TokenResponse)
async def signin(body: SignInRequest):
    """
    Sign in with email + password via Clerk.
    TODO: Clerk signIn, return JWT
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/signout", status_code=204)
async def signout(request: Request):
    """
    Invalidate the current session.
    TODO: revoke Clerk session token
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    """
    Refresh an expired access token using Clerk's refresh mechanism.
    TODO: call Clerk refresh endpoint
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/webhooks/clerk", status_code=200)
async def clerk_webhook(request: Request):
    """
    Receive Clerk webhook events (user.created, user.updated, user.deleted).
    Validates Svix signature before processing.
    TODO: verify CLERK_WEBHOOK_SECRET, handle event types
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me")
async def get_me(request: Request):
    """
    Return the currently authenticated user's profile.
    Requires: valid Clerk JWT in Authorization header.
    TODO: extract user_id from Clerk JWT, fetch from Supabase
    """
    raise HTTPException(status_code=501, detail="Not implemented")
