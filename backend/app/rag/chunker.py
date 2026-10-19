from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.rag.parser import ParsedDocument


@dataclass(frozen=True)
class ChunkRecord:
    document_id: UUID
    document_version: int
    product_id: UUID | None
    document_type: str
    chunk_index: int
    title: str
    section: str | None
    source_locator: str
    content: str


def chunk_document(
    parsed: ParsedDocument,
    *,
    document_id: UUID,
    version: int,
    product_id: UUID | None,
    document_type: str,
    max_chars: int = 1200,
) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    for section in parsed.sections:
        text = section.text
        if len(text) <= max_chars:
            parts = [text]
        else:
            parts = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
        for part in parts:
            chunks.append(
                ChunkRecord(
                    document_id=document_id,
                    document_version=version,
                    product_id=product_id,
                    document_type=document_type,
                    chunk_index=len(chunks),
                    title=parsed.title,
                    section=section.heading,
                    source_locator=section.source_locator,
                    content=part,
                )
            )
    return chunks
