from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion
from app.rag.chunker import chunk_document
from app.rag.embeddings import embed_text
from app.rag.parser import parse_document
from app.rag.storage import ObjectStorage
from app.services.knowledge import KnowledgeVersionService


class KnowledgeIndexer:
    def __init__(self, session: Session, storage: ObjectStorage) -> None:
        self.session = session
        self.storage = storage

    def index_version(self, version_id):
        version = self.session.get(KnowledgeDocumentVersion, version_id)
        if version is None:
            raise ValueError("knowledge version not found")
        document = self.session.get(KnowledgeDocument, version.document_id)
        if document is None:
            raise ValueError("knowledge document not found")
        source = self.storage.get(version.object_key)
        if source is None:
            KnowledgeVersionService(self.session, self.storage).fail_version(version.id, "source object not found")
            return 0
        try:
            parsed = parse_document(document.source_key, source)
            records = chunk_document(parsed, document_id=document.id, version=version.version, product_id=document.product_id, document_type=document.document_type)
            self.session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_version_id == version.id))
            self.session.add_all([
                KnowledgeChunk(
                    document_id=record.document_id,
                    document_version_id=version.id,
                    document_version=record.document_version,
                    product_id=record.product_id,
                    chunk_index=record.chunk_index,
                    title=record.title,
                    section=record.section,
                    source_locator=record.source_locator,
                    content=record.content,
                    embedding=embed_text(record.content),
                )
                for record in records
            ])
            self.session.commit()
            KnowledgeVersionService(self.session, self.storage).activate_version(version.id)
            return len(records)
        except Exception as exc:
            self.session.rollback()
            KnowledgeVersionService(self.session, self.storage).fail_version(version.id, str(exc))
            return 0
