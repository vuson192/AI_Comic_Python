import logging
from fastapi import APIRouter, Depends

from app.dependencies import get_ollama
from app.services.ollama_service import OllamaService
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="Tin nhắn gửi tới model")
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt tùy chỉnh (không bắt buộc)"
    )


class ChatResponse(BaseModel):
    reply: str
    model: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    ollama: OllamaService = Depends(get_ollama),
):
    """
    Chat trực tiếp với LLM (Ollama).
    Không liên quan đến comic generation - chỉ hỏi đáp thông thường.
    """
    logger.info("Chat: '%s'", request.message[:80])

    reply = await ollama.chat(
        user_message=request.message,
        system_prompt=request.system_prompt,
    )

    return ChatResponse(
        reply=reply,
        model=ollama.chat_model,
    )
