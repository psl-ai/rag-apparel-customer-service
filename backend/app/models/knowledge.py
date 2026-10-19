from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUuidModel


class KnowledgeDocument(TimestampedUuidModel):
    __tablename__ = "knowledge_documents"
    __table_args__ = (UniqueConstraint("source_key", name="uq_knowledge_documents_source_key"),)
    title: Mapped[str] = mapped_column(String(255), index=True)
    document_type: Mapped[str] = mapped_column(String(64), index=True)
    source_key: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    version: Mapped[int] = mapped_column(Integer, default=1, index=True)
    active_version: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class KnowledgeDocumentVersion(TimestampedUuidModel):
    __tablename__ = "knowledge_document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version", name="uq_knowledge_document_versions_document_version"),)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class KnowledgeChunk(TimestampedUuidModel):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (Index("ix_knowledge_chunks_document_version", "document_id", "document_version"),)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    document_version: Mapped[int] = mapped_column(Integer)
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_locator: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
