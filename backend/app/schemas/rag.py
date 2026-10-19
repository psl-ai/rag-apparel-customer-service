from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    section: str | None = None
    source_locator: str | None = None
    snippet: str


class RetrievedChunk(Citation):
    score: float = Field(ge=0)
    product_id: UUID | None = None
    document_type: str
    document_version: int


class KnowledgeUpload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    document_type: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1)
    product_id: UUID | None = None
