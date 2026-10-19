# RAG Productionization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade FashionRAG knowledge ingestion and retrieval from a local demo into a versioned, asynchronously indexable, pgvector-compatible and measurable subsystem.

**Architecture:** Keep the modular monolith and preserve the existing `KnowledgeRetriever.search` contract. Add immutable document versions, an object-storage protocol with an in-memory/local implementation, a shared indexing service used inline or by Celery, weighted SQLite retrieval, PostgreSQL/pgvector retrieval, and deterministic evaluation scenarios.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.x, pgvector, Celery/Redis, pytest, SQLite test fixtures.

## Global Constraints

- Prices, inventory, SKU status, and order status remain relational facts and are not sourced from documents.
- Uploaded files are untrusted evidence; document text cannot alter prompts, tool selection, authorization, or configuration.
- Existing APIs and citation schemas remain backward compatible unless an explicit versioning field is added.
- No paid model or embedding provider is called by tests.

### Task 1: Immutable document versions and storage abstraction

**Files:**
- Modify: `backend/app/models/knowledge.py`
- Create: `backend/app/rag/storage.py`
- Create: `backend/app/tests/test_knowledge_versions.py`
- Modify: `backend/app/db/local.py`

**Interfaces:** `ObjectStorage.put(key, content, content_type)`, `get(key)`, `delete(key)`; `KnowledgeVersionService.create_version`, `activate_version`, `fail_version`.

- [ ] Write tests for same-source version increments, one active version, source hash, and failed-version preservation.
- [ ] Run focused tests and observe missing version/storage interfaces.
- [ ] Add `KnowledgeDocumentVersion`, `source_key`, active-version relation, and in-memory storage; keep old rows readable.
- [ ] Run focused tests and all existing model/local database tests.

### Task 2: Shared indexing service and Celery task

**Files:**
- Create: `backend/app/rag/indexer.py`
- Modify: `backend/app/services/knowledge.py`
- Modify: `backend/app/tasks/celery_app.py`
- Create: `backend/app/tasks/knowledge.py`
- Create: `backend/app/tests/test_knowledge_indexer.py`

**Interfaces:** `KnowledgeIndexer.index_version(version_id) -> int`; Celery task `index_knowledge_version(version_id: str) -> int`.

- [ ] Write tests for atomic chunk replacement, ready status, and failed parse/index without deactivating the previous ready version.
- [ ] Verify red, implement shared indexer and task wrapper, verify green.

### Task 3: Weighted SQLite retrieval and pgvector adapter

**Files:**
- Modify: `backend/app/rag/retriever.py`
- Modify: `backend/app/rag/pgvector_retriever.py`
- Modify: `backend/app/core/config.py`
- Create: `backend/app/tests/test_retrieval_ranking.py`

- [ ] Write tests for lexical/vector weighted ordering, active-version/type/product filters, top-k, and citation version metadata.
- [ ] Verify red, implement deterministic cosine scoring for SQLite and a real SQLAlchemy pgvector query builder for PostgreSQL.
- [ ] Verify focused tests and import/compile checks without requiring a running PostgreSQL server.

### Task 4: Version-aware knowledge APIs

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`
- Create: `backend/app/schemas/knowledge.py`
- Create: `backend/app/tests/test_knowledge_api.py`

- [ ] Write tests for upload, list, reindex, delete, extension/size validation, RBAC and source cleanup.
- [ ] Verify red, implement APIs with inline indexing for SQLite and Celery dispatch for production settings, verify green.

### Task 5: Offline evaluation suite and metrics endpoint

**Files:**
- Create: `backend/app/evals/grounded.py`
- Create: `backend/app/evals/__init__.py`
- Modify: `backend/app/api/v1/admin.py`
- Create: `backend/app/tests/test_rag_evaluation.py`

- [ ] Write deterministic evaluation scenarios for citation, size/product filter, archived-version exclusion, malicious document, missing evidence, inventory precedence, and unavailable products.
- [ ] Verify red, implement evaluator and authorized summary endpoint, verify green.

### Task 6: Documentation and migration boundary

**Files:**
- Create: `backend/alembic/versions/20260901_01_knowledge_versions.py`
- Modify: `.env.example`, `README.md`, `docker-compose.yml`

- [ ] Document `RAG_RETRIEVER_BACKEND`, object storage settings, worker command, evaluation endpoint, and migration behavior.
- [ ] Add migration operations for new version/source fields without claiming Docker verification.
- [ ] Run backend tests, frontend build, Ruff/mypy where writable caches permit.

## Self-review

- Every task has named files, interfaces, tests, and verification commands.
- No PDF/DOCX, paid model, or management UI work is hidden in this plan.
- The existing SQLite mode stays usable while the pgvector path is explicit and compile-testable.
