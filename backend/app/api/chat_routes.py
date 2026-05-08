"""Chat API routes for LLM-powered conversations."""

import logging
from typing import Any
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    messages: list[ChatMessage]
    model: str | None = None
    context: dict[str, Any] | None = None  # Optional: entity states, selected cards, etc.


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    message: str
    model: str


async def generate_chat_stream(
    messages: list[dict[str, str]],
    model: str | None,
    context: dict[str, Any] | None,
):
    """Generate streaming chat response using SSE."""
    llm = get_llm_service()

    # Inject context as system message if provided
    if context:
        context_str = _format_context(context)
        messages.insert(
            0,
            {
                "role": "system",
                "content": f"You are a helpful assistant for a Home Assistant dashboard builder. {context_str}",
            }
        )

    try:
        # For streaming, we'll collect chunks and yield them
        # Note: Actual streaming depends on provider support
        full_response = await llm.chat(messages, model)

        # Yield the full response as SSE
        yield f"data: {full_response}\n\n"
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        if isinstance(e, HTTPException):
            yield f"data: Error ({e.status_code}): {e.detail}\n\n"
        else:
            yield f"data: Error: {str(e)}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/chat/messages", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest) -> ChatResponse:
    """Send a chat message to the LLM and get a response.

    POST /api/chat/messages -> 200 { "message": "...", "model": "llama3.2" }

    The request body should include:
    - messages: List of conversation messages (role + content)
    - model: Optional model name (defaults to configured model)
    - context: Optional context data (entity states, dashboard info, etc.)
    """
    llm = get_llm_service()

    try:
        # Convert Pydantic models to dicts for the LLM service
        messages = [msg.model_dump() for msg in request.messages]

        # Inject context as system message if provided
        if request.context:
            context_str = _format_context(request.context)
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": f"You are a helpful assistant for a Home Assistant dashboard builder. {context_str}",
                }
            )

        response = await llm.chat(messages, request.model)

        return ChatResponse(
            message=response,
            model=request.model or llm.model or "default",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")


@router.post("/chat/stream")
async def stream_chat_message(request: ChatRequest):
    """Stream a chat message response from the LLM using SSE.

    POST /api/chat/stream -> text/event-stream
    """
    messages = [msg.model_dump() for msg in request.messages]

    return StreamingResponse(
        generate_chat_stream(messages, request.model, request.context),
        media_type="text/event-stream",
    )


@router.get("/chat/models")
async def list_chat_models() -> dict[str, list[str]]:
    """Get available LLM models for the current provider.

    GET /api/chat/models -> 200 { "models": ["llama3.2", "mistral", ...] }
    """
    llm = get_llm_service()
    models = llm.get_available_models()
    return {"models": models}


@router.get("/chat/providers")
async def list_providers() -> dict[str, list[str]]:
    """Get available LLM providers and their models.

    GET /api/chat/providers -> 200 { "providers": { "ollama": [...], "lmstudio": [...] } }
    """
    from app.services.llm_service import OllamaProvider, LMStudioProvider

    ollama = OllamaProvider()
    lmstudio = LMStudioProvider()

    return {
        "providers": {
            "ollama": ollama.get_available_models(),
            "lmstudio": lmstudio.get_available_models(),
        }
    }


def _format_context(context: dict[str, Any]) -> str:
    """Format context data into a string for the system prompt."""
    parts = []

    if entities := context.get("entities"):
        parts.append(f"Available entities: {len(entities)} total")
        # Include a few example entities
        for e in list(entities)[:5]:
            parts.append(f"  - {e.get('entity_id')}: {e.get('state')}")

    if cards := context.get("selected_cards"):
        parts.append(f"Selected cards: {len(cards)}")
        for c in cards:
            parts.append(f"  - {c.get('card_type')}: {c.get('entity_id')}")

    if dashboard_name := context.get("dashboard_name"):
        parts.append(f"Dashboard: {dashboard_name}")

    return " ".join(parts) if parts else "No additional context."
