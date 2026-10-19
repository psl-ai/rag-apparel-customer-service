# FashionRAG RAG Productionization Design

## Scope

This increment upgrades the existing offline RAG vertical slice into a deployable retrieval subsystem without expanding customer commerce or administration UI. It fixes knowledge-document versioning, supports asynchronous indexing, provides compatible SQLite and PostgreSQL/pgvector retrievers, and adds deterministic evaluation metrics.

## Goals

- A document has a stable logical key and multiple immutable versions.
- Exactly one version per logical document is active; retrieval reads active, indexed versions only.
- Upload writes source bytes through an object-storage abstraction, then creates an indexing job.
- SQLite runs the job inline for local development and tests; Celery runs the same job in Docker deployments.
- SQLite retrieval combines lexical overlap and deterministic embedding cosine similarity. PostgreSQL uses the same filters and result schema with pgvector cosine distance.
- Evaluation tests report retrieval and grounded-answer pass/fail results without a paid model.

## Data Model

`KnowledgeDocument` becomes the logical document record with a unique `source_key`, title, type, optional product association, and `active_version`.

`KnowledgeDocumentVersion` holds immutable version metadata: `document_id`, sequential `version`, object key, status (`uploaded`, `indexing`, `ready`, `failed`, `archived`), source hash, parse error, and timestamps. `KnowledgeChunk` references `document_version_id`; its document version number remains denormalized for filtering and citations.

For backward compatibility with the existing schema, the first Alembic migration creates the version table and migrates existing document rows into active version records. SQLite local initialization creates the same schema from ORM metadata.

## Indexing Flow

```text
authenticated upload
  -> validate extension and size
  -> ObjectStorage.put(source bytes)
  -> create logical document/version(status=uploaded)
  -> enqueue index_document_version(version_id)
  -> parser -> chunker -> embedding adapter
  -> replace chunks for version atomically
  -> mark ready and make version active
```

Failure retains the source file and a `failed` version with a sanitized error message. A failed reindex must not deactivate the last ready version. Delete removes chunks, version metadata, and the object-store key through the same storage abstraction.

## Retrieval

`KnowledgeRetriever` is selected by settings: `sqlite` for local URLs and `pgvector` for PostgreSQL URLs. Its public contract remains:

```python
search(query: str, *, document_type: str | None, product_id: UUID | None, top_k: int) -> list[RetrievedChunk]
```

SQLite scores a weighted lexical token score plus cosine similarity from deterministic embeddings. PostgreSQL applies active-ready/version/type/product filters and orders by `embedding.cosine_distance(query_embedding)`, with a lexical tie breaker. Both return citation title, section, source locator, document version, and score.

Knowledge text is always untrusted evidence. It never controls tool selection, system instructions, authorization, or model configuration.

## Agent and Observability

The chat service persists selected retriever metadata, source version IDs, elapsed retrieval time, and sanitized tool inputs/outputs. The response retains the existing citation contract. Missing retrieval evidence produces a refusal or handoff, never a fabricated policy claim.

An evaluation service supplies deterministic scenarios: policy source retrieval, product-filtered size retrieval, archived-version exclusion, malicious instruction resistance, missing-evidence refusal, live inventory precedence, and unavailable-product exclusion. It calculates `passed`, `total`, and `pass_rate` for dashboard/API exposure.

## APIs

- `POST /api/v1/knowledge/documents`: creates a version and schedules indexing.
- `GET /api/v1/knowledge/documents`: lists documents with active/indexing status.
- `POST /api/v1/knowledge/documents/{id}/reindex`: creates a new version from the stored source.
- `DELETE /api/v1/knowledge/documents/{id}`: deletes logical document, versions, chunks, and source objects.
- `GET /api/v1/admin/rag/evaluations`: executes/read deterministic evaluation summary for authorized operators.

## Tests and Acceptance

Tests use a temporary SQLite database and in-memory object store. They verify version sequencing, failed-index rollback, old-version exclusion, retrieval ranking and filters, delete synchronization, Celery task delegation boundary, citation version metadata, and evaluation pass rate.

The increment is accepted when local SQLite tests pass without Docker, PostgreSQL code paths compile against pgvector, and `docker compose up` can run the worker path once Docker Desktop is available.

## Deliberate Deferrals

PDF/DOCX OCR, production cross-encoder reranking, semantic query rewriting with a paid model, and the management UI are deferred to later phases. Their API boundaries are preserved, but they are not simulated as completed work.

## Self-Review

- Scope is limited to the RAG subsystem and does not overlap with the later transaction or dashboard phases.
- Version lifecycle, active-version behavior, asynchronous failure semantics, retriever contract, and tests are explicit.
- SQLite remains supported for local development while PostgreSQL/pgvector is the production implementation.
