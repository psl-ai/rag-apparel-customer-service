from __future__ import annotations

from uuid import UUID

from app.db.session import get_sync_db_session
from app.rag.indexer import KnowledgeIndexer
from app.rag.storage import get_object_storage
from app.tasks.celery_app import celery_app


@celery_app.task(name="fashionrag.index_knowledge_version")
def index_knowledge_version(version_id: str) -> int:
    session = next(get_sync_db_session())
    try:
        return KnowledgeIndexer(session, get_object_storage()).index_version(UUID(version_id))
    finally:
        session.close()
