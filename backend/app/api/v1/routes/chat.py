# ============================================================
#  app/api/v1/routes/chat.py
#  POST /v1/chat — single-turn and streamed chat
# ============================================================
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    conversation_id: Optional[str] = None   # null = new conversation
    stream: bool = True
    max_tokens: Optional[int] = None        # defaults to ORCA_MAX_TOKENS
    system_prompt: Optional[str] = None     # Advanced plan only


class ChatResponse(BaseModel):
    id: str                  # message ID
    conversation_id: str
    role: str = "assistant"
    content: str
    model: str
    tokens_used: int
    created_at: str


@router.post("", summary="Send a chat message")
async def chat(body: ChatRequest, request: Request):
    """
    Send one or more messages to the ORCA model in Chat mode.

    - Requires: authenticated user (Clerk JWT) OR valid og- API key
    - Enforces daily query limits based on plan (Free: 50, Pro: 1000, Advanced: unlimited)
    - Persists message pair to Supabase conversations table
    - Supports SSE streaming when stream=true

    TODO:
    1. Auth: extract user from Clerk JWT or API key
    2. Rate limit: check + decrement Redis counter for user's plan
    3. Persist: upsert conversation row, insert user message
    4. Forward: call ORCA_SERVICE_URL with messages + model config
    5. Stream: yield SSE chunks or return full response
    6. Persist: insert assistant message, update token usage
    """
    pass


# ============================================================
#  app/api/v1/routes/search.py
#  POST /v1/search — web-augmented search mode
# ============================================================
from fastapi import APIRouter as _AR
search_router = _AR()


class SearchRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    stream: bool = True
    max_results: int = Field(default=8, ge=1, le=20)


@search_router.post("", summary="Run a web-augmented search query")
async def search(body: SearchRequest, request: Request):
    """
    Search mode: ORCA retrieves and synthesises web results before responding.

    TODO:
    1. Auth + rate limit (same as chat)
    2. Retrieve: call internal search service (SerpAPI / Brave Search)
    3. Forward to ORCA with retrieved context injected as system messages
    4. Stream response with inline source citations
    5. Persist conversation + sources used
    """
    pass


# ============================================================
#  app/api/v1/routes/reason.py
#  POST /v1/reason — multi-step reasoning mode
# ============================================================
reason_router = _AR()


class ReasonRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None
    stream: bool = True
    max_loops: int = Field(default=3, ge=1, le=8)  # Advanced plan unlocks up to 8
    show_reasoning: bool = True                      # Whether to surface chain-of-thought


@reason_router.post("", summary="Run a multi-step reasoning query")
async def reason(body: ReasonRequest, request: Request):
    """
    Reason mode: ORCA iterates through up to max_loops reasoning cycles.
    Each loop can refine, verify, or expand on the previous step.

    - max_loops > 3 requires Advanced plan
    - Streams reasoning steps as SSE events with type: 'reasoning' | 'response'

    TODO:
    1. Auth + plan check (loop limit enforcement)
    2. Rate limit
    3. Call ORCA with reason mode flag + loop config
    4. Stream reasoning chunks (type=reasoning) then final answer (type=response)
    5. Persist full chain + final answer
    """
    pass


# Re-export as named routers for main.py
from fastapi import APIRouter

router = APIRouter()

# Mount search and reason onto the chat router file's exports
# Each router is imported individually in main.py — see route files below
