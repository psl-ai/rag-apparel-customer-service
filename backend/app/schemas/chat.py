from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.rag import Citation


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    product_id: UUID | None = None
    sku_id: UUID | None = None


class ChatResult(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    intent: str
    citations: list[Citation] = Field(default_factory=list)
    handoff: bool = False
