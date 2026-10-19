from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_indexer_replaces_chunks_and_activates_version(tmp_path: Path):
    from app.db.base import Base, import_models
    from app.models.knowledge import KnowledgeChunk
    from app.rag.indexer import KnowledgeIndexer
    from app.rag.storage import InMemoryObjectStorage
    from app.services.knowledge import KnowledgeVersionService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'index.db'}"); Base.metadata.create_all(engine)
    storage = InMemoryObjectStorage()
    with Session(engine) as session:
        version = KnowledgeVersionService(session, storage).create_version(source_key="policy.md", title="政策", document_type="policy", content="# 退换货\n7天".encode())
        assert KnowledgeIndexer(session, storage).index_version(version.id) == 1
        chunks = session.scalars(select(KnowledgeChunk).where(KnowledgeChunk.document_version_id == version.id)).all()
        session.refresh(version)
    assert len(chunks) == 1
    assert version.status == "ready"


def test_indexer_marks_missing_source_failed(tmp_path: Path):
    from app.db.base import Base, import_models
    from app.models.knowledge import KnowledgeDocumentVersion
    from app.rag.indexer import KnowledgeIndexer
    from app.rag.storage import InMemoryObjectStorage
    from app.services.knowledge import KnowledgeVersionService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'missing.db'}"); Base.metadata.create_all(engine)
    storage = InMemoryObjectStorage()
    with Session(engine) as session:
        version = KnowledgeVersionService(session, storage).create_version(source_key="missing.txt", title="FAQ", document_type="faq", content=b"ok")
        storage.delete(version.object_key)
        assert KnowledgeIndexer(session, storage).index_version(version.id) == 0
        refreshed = session.get(KnowledgeDocumentVersion, version.id)
    assert refreshed is not None
    assert refreshed.status == "failed"
