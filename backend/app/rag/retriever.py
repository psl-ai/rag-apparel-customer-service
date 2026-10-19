from __future__ import annotations

import re
import math
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.schemas.rag import RetrievedChunk
from app.rag.embeddings import embed_text
from app.core.config import get_settings


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[\w\u4e00-\u9fff]+", value.lower()) if token}


def _cosine(left: list[float] | None, right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    return sum(x * y for x, y in zip(left, right, strict=False)) / denominator if denominator else 0.0


class KnowledgeRetriever:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query: str,
        *,
        document_type: str | None = None,
        product_id: UUID | None = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        statement: Select[tuple[KnowledgeChunk, KnowledgeDocument]] = (
            select(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.status.in_(["ready", "published"]))
            .where(
                (KnowledgeDocument.active_version.is_(None))
                | (KnowledgeChunk.document_version == KnowledgeDocument.active_version)
            )
        )
        if document_type:
            statement = statement.where(KnowledgeDocument.document_type == document_type)
        if product_id:
            statement = statement.where(KnowledgeChunk.product_id == product_id)
        query_tokens = _tokens(query)
        query_embedding = embed_text(query)
        ranked: list[RetrievedChunk] = []
        for chunk, document in self.session.execute(statement).all():
            content_tokens = _tokens(chunk.content)
            overlap = len(query_tokens & content_tokens)
            vector_score = _cosine(chunk.embedding, query_embedding)
            if overlap == 0 and vector_score <= 0 and query.strip():
                continue
            lexical_score = overlap / max(len(query_tokens), 1)
            score = max(0.0, 0.7 * lexical_score + 0.3 * max(vector_score, 0.0))
            ranked.append(
                RetrievedChunk(
                    document_id=document.id,
                    title=chunk.title or document.title,
                    section=chunk.section,
                    source_locator=chunk.source_locator,
                    snippet=chunk.content[:500],
                    score=score,
                    product_id=chunk.product_id or document.product_id,
                    document_type=document.document_type,
                    document_version=chunk.document_version,
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.document_version, item.title))
        return ranked[:top_k]


def get_knowledge_retriever(session: Session) -> KnowledgeRetriever:
    settings = get_settings()
    backend = settings.rag_retriever_backend
    if backend == "pgvector" or (backend == "auto" and settings.database_url.startswith("postgresql")):
        from app.rag.pgvector_retriever import PgVectorRetriever

        return PgVectorRetriever(session)
    return KnowledgeRetriever(session)
