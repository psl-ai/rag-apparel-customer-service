"""add immutable knowledge document versions

Revision ID: 20260901_01
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_documents", sa.Column("source_key", sa.String(length=512), nullable=True))
    op.add_column("knowledge_documents", sa.Column("active_version", sa.Integer(), nullable=True))
    op.create_index("ix_knowledge_documents_source_key", "knowledge_documents", ["source_key"])
    op.create_index("ix_knowledge_documents_active_version", "knowledge_documents", ["active_version"])
    op.create_table(
        "knowledge_document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version", name="uq_knowledge_document_versions_document_version"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index("ix_knowledge_document_versions_document_id", "knowledge_document_versions", ["document_id"])
    op.create_index("ix_knowledge_document_versions_source_hash", "knowledge_document_versions", ["source_hash"])
    op.create_index("ix_knowledge_document_versions_status", "knowledge_document_versions", ["status"])
    op.add_column("knowledge_chunks", sa.Column("document_version_id", sa.Uuid(), nullable=True))
    op.add_column("knowledge_chunks", sa.Column("source_locator", sa.String(length=64), nullable=True))
    op.create_foreign_key("fk_knowledge_chunks_document_version", "knowledge_chunks", "knowledge_document_versions", ["document_version_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_knowledge_chunks_document_version_id", "knowledge_chunks", ["document_version_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_document_version_id", table_name="knowledge_chunks")
    op.drop_constraint("fk_knowledge_chunks_document_version", "knowledge_chunks", type_="foreignkey")
    op.drop_column("knowledge_chunks", "source_locator")
    op.drop_column("knowledge_chunks", "document_version_id")
    op.drop_index("ix_knowledge_document_versions_status", table_name="knowledge_document_versions")
    op.drop_index("ix_knowledge_document_versions_source_hash", table_name="knowledge_document_versions")
    op.drop_index("ix_knowledge_document_versions_document_id", table_name="knowledge_document_versions")
    op.drop_table("knowledge_document_versions")
    op.drop_index("ix_knowledge_documents_active_version", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_source_key", table_name="knowledge_documents")
    op.drop_column("knowledge_documents", "active_version")
    op.drop_column("knowledge_documents", "source_key")
