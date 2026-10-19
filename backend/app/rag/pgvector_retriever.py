"""Production adapter boundary for pgvector retrieval.

The SQLite retriever remains the default local implementation. A deployment can
subclass this adapter and replace the lexical query with cosine distance while
keeping the same metadata filters and return model.
"""

from uuid import UUID

from sqlalchemy import select

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.rag.embeddings import embed_text
from app.rag.retriever import KnowledgeRetriever
from app.schemas.rag import RetrievedChunk


class PgVectorRetriever(KnowledgeRetriever):
    """pgvector cosine retrieval with the same public return contract."""

    def search(
        self,
        query: str,
        *,
        document_type: str | None = None,
        product_id: UUID | None = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        embedding = embed_text(query)
        distance = KnowledgeChunk.embedding.cosine_distance(embedding)
        statement = (
            select(KnowledgeChunk, KnowledgeDocument, distance.label("distance"))
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.status.in_(["ready", "published"]))
            .where((KnowledgeDocument.active_version.is_(None)) | (KnowledgeChunk.document_version == KnowledgeDocument.active_version))
        )
        if document_type:
            statement = statement.where(KnowledgeDocument.document_type == document_type)
        if product_id:
            statement = statement.where(KnowledgeChunk.product_id == product_id)
        rows = self.session.execute(statement.order_by(distance, KnowledgeChunk.chunk_index).limit(top_k)).all()
        return [
            RetrievedChunk(
                document_id=document.id,
                title=chunk.title or document.title,
                section=chunk.section,
                source_locator=chunk.source_locator,
                snippet=chunk.content[:500],
                score=max(0.0, 1 - float(row_distance)),
                product_id=chunk.product_id or document.product_id,
                document_type=document.document_type,
                document_version=chunk.document_version,
            )
            for chunk, document, row_distance in rows
        ]
