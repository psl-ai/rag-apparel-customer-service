# RAG Agent Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a grounded FashionRAG shopping assistant vertical slice that ingests knowledge, retrieves cited evidence, calls typed commerce tools, persists traces, and streams safe Chinese answers using SQLite and mock models.

**Architecture:** Keep the modular monolith. Add focused `rag`, `agents`, `services`, and API modules over existing SQLAlchemy models. SQLite uses deterministic lexical/hash embeddings; a retriever interface leaves a pgvector adapter boundary. Chat orchestration builds authoritative relational evidence first, then composes deterministic answers and persists conversation, trace, tool calls, citations, feedback, and handoffs.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite for local tests, PostgreSQL/pgvector production adapter, pytest, SSE.

## Global Constraints

- Prices, inventory, SKU status, and order status are always read from relational tables.
- Uploaded documents are untrusted quoted evidence; embedded instructions never become agent instructions.
- Answers are Chinese, cite source title/section/page or row when knowledge is used, recommend at most five available published products, and refuse or hand off without reliable evidence.
- Tests must not call paid model providers; use deterministic mock embeddings and model adapters.
- Preserve the existing uniform response envelope, request IDs, RBAC, and ownership checks.

### Task 1: Schemas and deterministic knowledge pipeline

**Files:**
- Create: `backend/app/schemas/rag.py`, `backend/app/schemas/chat.py`
- Create: `backend/app/rag/parser.py`, `backend/app/rag/chunker.py`, `backend/app/rag/embeddings.py`
- Create: `backend/app/tests/test_rag_pipeline.py`

**Interfaces:** `parse_document(filename: str, content: bytes) -> ParsedDocument`; `chunk_document(parsed, document_id, version, product_id, document_type) -> list[ChunkRecord]`; `embed_text(text: str) -> list[float]`.

- [ ] Write tests for Markdown headings, TXT normalization, CSV row metadata, prompt-injection treated as plain content, and deterministic chunk metadata.
- [ ] Run `pytest app/tests/test_rag_pipeline.py -v` and confirm failure because modules are absent.
- [ ] Implement parser, chunker, and fixed-size deterministic embeddings with no network calls.
- [ ] Run the focused tests and then the existing suite.

### Task 2: Local retriever and knowledge service

**Files:**
- Create: `backend/app/rag/retriever.py`, `backend/app/services/knowledge.py`
- Modify: `backend/app/models/knowledge.py` only if source metadata fields are required.
- Create: `backend/app/tests/test_retriever.py`

**Interfaces:** `KnowledgeRetriever.search(query, *, document_type=None, product_id=None, top_k=5) -> list[RetrievedChunk]`; `KnowledgeService.ingest(...)` and `reindex(document_id)`.

- [ ] Write failing tests for active-version filtering, product/type filters, lexical ranking, and citation metadata.
- [ ] Verify red, implement SQLite retrieval and idempotent ingestion, verify green.

### Task 3: Typed tools and deterministic agent policy

**Files:**
- Create: `backend/app/agents/tools.py`, `backend/app/agents/policy.py`
- Create: `backend/app/tests/test_agent_tools.py`, `backend/app/tests/test_agent_policy.py`

**Interfaces:** Pydantic input/output models and functions `search_products`, `get_product_detail`, `query_inventory`, `recommend_size`, `retrieve_knowledge`, `compare_products`, `get_user_preferences`, `save_user_preference`, `get_order_status`, `get_shipping_status`, `check_return_policy`, `create_human_handoff`.

- [ ] Write failing tests for live inventory, size-chart evidence, policy citations, unavailable-product exclusion, ownership denial, malicious-document resistance, and missing-evidence handoff.
- [ ] Verify red, implement minimal typed tools and intent router/composer, verify green.

### Task 4: Conversations, traces, non-streaming chat

**Files:**
- Create: `backend/app/services/chat.py`
- Create: `backend/app/api/v1/chat.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/app/tests/test_chat_api.py`

**Interfaces:** `ChatService.handle(user_id, conversation_id, message) -> ChatResult`; `POST /api/v1/chat`; `GET /api/v1/conversations`; `GET /api/v1/conversations/{id}`.

- [ ] Write failing API tests for multi-turn persistence, citations, trace/tool-call persistence, and conversation ownership.
- [ ] Verify red, implement orchestration and persistence, verify green.

### Task 5: SSE, feedback, handoff, admin traces

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Create: `backend/app/api/v1/feedback.py`
- Modify: `backend/app/api/v1/admin.py`
- Create: `backend/app/tests/test_chat_stream.py`, `backend/app/tests/test_feedback_handoff.py`

- [ ] Write failing tests asserting event order `message_start`, `tool_call`, `citation`, `token`, `message_end` and feedback/handoff ownership.
- [ ] Verify red, implement SSE generator and endpoints, verify green.

### Task 6: Offline evaluation and frontend concierge

**Files:**
- Create: `backend/app/evals/test_grounded_agent.py`
- Create: `frontend/src/app/concierge/page.tsx`
- Modify: `frontend/src/lib/api-client.ts` and navigation links.

- [ ] Add evaluation fixtures for size, inventory, policy citation, refusal, and handoff.
- [ ] Add a responsive chat page consuming the non-streaming endpoint with citation/source rendering and loading/error states.
- [ ] Run backend tests and `npm run build`.

### Task 7: Production adapter and documentation

**Files:**
- Create: `backend/app/rag/pgvector_retriever.py`, `backend/app/agents/model_adapter.py`
- Modify: `.env.example`, `README.md`

- [ ] Document provider configuration, pgvector adapter contract, local mock mode, API examples, and deferred Docker verification.
- [ ] Run Ruff, mypy where available, backend tests, and frontend build.

## Self-review

- Coverage includes ingestion, retrieval filters, typed tools, grounded policy, SSE, persistence, ownership, feedback, handoff, frontend, and deployment boundary.
- No placeholder or unspecified interfaces remain; every task names files, APIs, tests, and verification commands.
- The retriever and model adapter interfaces keep SQLite/mock development behavior-compatible with future pgvector/OpenAI-compatible implementations.
