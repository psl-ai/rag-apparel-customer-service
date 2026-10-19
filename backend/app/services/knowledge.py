from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion
from app.rag.chunker import chunk_document
from app.rag.embeddings import embed_text
from app.rag.parser import parse_document
from app.rag.retriever import get_knowledge_retriever
from app.rag.storage import ObjectStorage, get_object_storage


class KnowledgeVersionService:
    def __init__(self, session: Session, storage: ObjectStorage) -> None:
        self.session = session
        self.storage = storage

    def create_version(
        self,
        *,
        source_key: str,
        title: str,
        document_type: str,
        content: bytes,
        product_id: UUID | None = None,
    ) -> KnowledgeDocumentVersion:
        document = self.session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.source_key == source_key))
        if document is None:
            document = KnowledgeDocument(
                source_key=source_key,
                object_key=f"legacy/{uuid4().hex}",
                title=title,
                document_type=document_type,
                product_id=product_id,
                status="uploaded",
            )
            self.session.add(document)
            self.session.flush()
        else:
            document.title = title
            document.document_type = document_type
            document.product_id = product_id
        latest = self.session.scalar(
            select(KnowledgeDocumentVersion.version)
            .where(KnowledgeDocumentVersion.document_id == document.id)
            .order_by(KnowledgeDocumentVersion.version.desc())
            .limit(1)
        )
        version_number = (latest or 0) + 1
        object_key = f"knowledge/{document.id}/{version_number}-{uuid4().hex}.source"
        self.storage.put(object_key, content, "application/octet-stream")
        version = KnowledgeDocumentVersion(
            document_id=document.id,
            version=version_number,
            object_key=object_key,
            source_hash=hashlib.sha256(content).hexdigest(),
            status="uploaded",
        )
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return version

    def activate_version(self, version_id: UUID) -> KnowledgeDocumentVersion:
        version = self.session.get(KnowledgeDocumentVersion, version_id)
        if version is None:
            raise AppError("KNOWLEDGE_VERSION_NOT_FOUND", "知识文档版本不存在", 404)
        document = self.session.get(KnowledgeDocument, version.document_id)
        if document is None:
            raise AppError("KNOWLEDGE_NOT_FOUND", "知识文档不存在", 404)
        old_versions = self.session.scalars(
            select(KnowledgeDocumentVersion).where(
                KnowledgeDocumentVersion.document_id == document.id,
                KnowledgeDocumentVersion.status == "ready",
                KnowledgeDocumentVersion.id != version.id,
            )
        ).all()
        for old in old_versions:
            old.status = "archived"
        version.status = "ready"
        version.parse_error = None
        document.active_version = version.version
        document.status = "ready"
        document.version = version.version
        document.object_key = version.object_key
        self.session.commit()
        self.session.refresh(version)
        return version

    def fail_version(self, version_id: UUID, error: str) -> KnowledgeDocumentVersion:
        version = self.session.get(KnowledgeDocumentVersion, version_id)
        if version is None:
            raise AppError("KNOWLEDGE_VERSION_NOT_FOUND", "知识文档版本不存在", 404)
        version.status = "failed"
        version.parse_error = error[:1000]
        self.session.commit()
        self.session.refresh(version)
        return version


class KnowledgeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ingest(
        self,
        *,
        title: str,
        document_type: str,
        filename: str,
        content: bytes,
        product_id: UUID | None = None,
    ) -> KnowledgeDocument:
        storage = get_object_storage()
        version = KnowledgeVersionService(self.session, storage).create_version(
            source_key=filename,
            title=title,
            document_type=document_type,
            content=content,
            product_id=product_id,
        )
        from app.rag.indexer import KnowledgeIndexer

        KnowledgeIndexer(self.session, storage).index_version(version.id)
        document = self.session.get(KnowledgeDocument, version.document_id)
        if document is None:
            raise AppError("KNOWLEDGE_NOT_FOUND", "知识文档不存在", 404)
        return document

    def reindex(self, document_id: UUID) -> int:
        document = self.session.get(KnowledgeDocument, document_id)
        if document is None:
            raise AppError("KNOWLEDGE_NOT_FOUND", "知识文档不存在", 404)
        chunks = self.session.scalars(select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)).all()
        for chunk in chunks:
            chunk.embedding = embed_text(chunk.content)
        self.session.commit()
        return len(chunks)

    def search(self, query: str, **filters: object):
        return get_knowledge_retriever(self.session).search(query, **filters)
