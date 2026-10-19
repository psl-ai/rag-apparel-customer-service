from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    conversation_id: UUID
    message_id: UUID | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
