from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_knowledge_versions_increment_and_only_latest_ready_is_active(tmp_path: Path):
    from app.db.base import Base, import_models
    from app.rag.storage import InMemoryObjectStorage
    from app.services.knowledge import KnowledgeVersionService
    from app.models.knowledge import KnowledgeDocument, KnowledgeDocumentVersion

    import_models()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'versions.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        service = KnowledgeVersionService(session, InMemoryObjectStorage())
        first = service.create_version(source_key="returns.md", title="退换货", document_type="policy", content="7天".encode())
        service.activate_version(first.id)
        second = service.create_version(source_key="returns.md", title="退换货", document_type="policy", content="15天".encode())
        service.activate_version(second.id)
        documents = session.scalars(select(KnowledgeDocument)).all()
        versions = session.scalars(select(KnowledgeDocumentVersion).order_by(KnowledgeDocumentVersion.version)).all()

    assert len(documents) == 1
    assert [version.version for version in versions] == [1, 2]
    assert versions[0].status == "archived"
    assert versions[1].status == "ready"
    assert documents[0].active_version == 2
    assert versions[0].source_hash != versions[1].source_hash


def test_failed_version_does_not_deactivate_previous_ready_version(tmp_path: Path):
    from app.db.base import Base, import_models
    from app.rag.storage import InMemoryObjectStorage
    from app.services.knowledge import KnowledgeVersionService
    from app.models.knowledge import KnowledgeDocument

    import_models()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'failed.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        service = KnowledgeVersionService(session, InMemoryObjectStorage())
        first = service.create_version(source_key="faq.txt", title="FAQ", document_type="faq", content=b"ok")
        service.activate_version(first.id)
        failed = service.create_version(source_key="faq.txt", title="FAQ", document_type="faq", content=b"bad")
        service.fail_version(failed.id, "parse failed")
        document = session.scalar(select(KnowledgeDocument))

    assert document is not None
    assert document.active_version == 1
    assert failed.status == "failed"
    assert failed.parse_error == "parse failed"


def test_storage_put_get_delete():
    from app.rag.storage import InMemoryObjectStorage

    storage = InMemoryObjectStorage()
    storage.put("a.txt", b"hello", "text/plain")
    assert storage.get("a.txt") == b"hello"
    storage.delete("a.txt")
    assert storage.get("a.txt") is None
