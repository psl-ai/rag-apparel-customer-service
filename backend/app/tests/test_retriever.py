from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_retriever_filters_inactive_versions_and_returns_citation(tmp_path):
    from app.db.base import Base, import_models
    from app.rag.retriever import KnowledgeRetriever
    from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

    import_models()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'rag.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        old = KnowledgeDocument(title="æ¿ç­", document_type="policy", object_key="p-v1", version=1, status="archived")
        active = KnowledgeDocument(title="æ¿ç­", document_type="policy", object_key="p-v2", version=2, status="ready")
        session.add_all([old, active])
        session.flush()
        session.add_all([
            KnowledgeChunk(document_id=old.id, document_version=1, chunk_index=0, title="æ¿ç­", content="èæ¿ç­ä¸éç¨"),
            KnowledgeChunk(document_id=active.id, document_version=2, chunk_index=0, title="æ¿ç­", content="7å¤©æ çç±éæ¢"),
        ])
        session.commit()

        results = KnowledgeRetriever(session).search("éæ¢", document_type="policy")

    assert len(results) == 1
    assert results[0].document_version == 2
    assert "7å¤©" in results[0].snippet


def test_retriever_can_filter_by_product(tmp_path):
    from app.db.base import Base, import_models
    from app.rag.retriever import KnowledgeRetriever
    from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

    import_models()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'rag-product.db'}")
    Base.metadata.create_all(engine)
    product_id = uuid4()
    with Session(engine) as session:
        doc = KnowledgeDocument(title="å°ºç ", document_type="size", object_key="s-v1", version=1, status="ready", product_id=product_id)
        session.add(doc)
        session.flush()
        session.add(KnowledgeChunk(document_id=doc.id, document_version=1, product_id=product_id, chunk_index=0, title="å°ºç ", content="M è¸å´ 96"))
        session.commit()
        assert KnowledgeRetriever(session).search("è¸å´", product_id=product_id)[0].product_id == product_id
