# FashionRAG Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen FashionRAG with database-backed RBAC, configurable CORS, idempotent order creation, a real OpenAI-compatible tool-calling adapter, measurable RAG evaluation, stable automated tests, and interview-ready documentation.

**Architecture:** Keep the modular monolith and existing SQLite/Mock development path. Add narrow services for authorization, idempotency, agent execution, and evaluation; PostgreSQL/Redis/OpenAI-compatible integrations remain environment-selected and the Mock implementations remain deterministic for tests.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite/PostgreSQL, Redis/Celery, httpx, pytest, Next.js/TypeScript, Mermaid.

## Global Constraints

- Prices, inventory, SKU availability, order ownership, and policy evidence remain database-backed.
- No API key or password is written to logs, traces, or documentation.
- Mock LLM and Mock Embedding remain the default test path; no test calls a paid model.
- Every new production behavior has a failing test before implementation.
- Docker/PostgreSQL validation is documented honestly when the local daemon is unavailable.

---

### Task 1: Database-backed RBAC and configurable CORS

**Files:**
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/services/auth.py`
- Modify: `backend/app/core/rbac.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/db/seed.py`
- Test: `backend/app/tests/test_rbac.py`, `backend/app/tests/test_auth_api.py`, `backend/app/tests/test_config.py`

**Interfaces:**
- `AuthService.login` reads role associations from `user_roles` and emits a role claim.
- `require_roles(*roles)` rejects claims whose role is not allowed.
- `Settings.cors_origins` exposes configured origins parsed from `CORS_ORIGINS`.

- [ ] Write tests proving admin access comes from role association, a customer gets 403, and configured origins are accepted.
- [ ] Run the focused tests and observe failure against email-special-case behavior.
- [ ] Seed role associations for demo and admin accounts, update login to resolve roles, and configure CORS from environment.
- [ ] Run focused tests, then all auth/RBAC tests.

### Task 2: Idempotent order creation

**Files:**
- Create: `backend/app/models/idempotency.py`
- Modify: `backend/app/models/__init__.py`, `backend/app/api/v1/commerce.py`, `backend/app/services/orders.py`, `backend/app/schemas/orders.py`
- Test: `backend/app/tests/test_order_idempotency.py`, `backend/app/tests/test_order_service.py`

**Interfaces:**
- `POST /api/v1/orders` accepts the `Idempotency-Key` header.
- `OrderService.checkout(..., idempotency_key: str | None)` returns the original order for the same user/key and rejects reuse with a different request payload.

- [ ] Write tests for same-key replay, same-key different payload, and no-key backward compatibility.
- [ ] Run them to verify the missing idempotency behavior.
- [ ] Add a unique `(user_id, key, endpoint)` record with request hash and serialized response, wrapping order creation in one transaction.
- [ ] Run order, inventory, and commerce tests.

### Task 3: Real OpenAI-compatible Agent tool calling

**Files:**
- Modify: `backend/app/agents/model_adapter.py`
- Create: `backend/app/agents/runner.py`
- Modify: `backend/app/services/chat.py`, `backend/app/api/v1/chat.py`, `backend/app/core/config.py`
- Test: `backend/app/tests/test_agent_runner.py`, `backend/app/tests/test_agent_tools.py`, `backend/app/tests/test_chat_api.py`

**Interfaces:**
- `ChatModelAdapter.complete(messages, tools) -> ModelTurn` supports `MockChatModel` and `OpenAICompatibleChatModel`.
- `AgentRunner.run(session, user_id, request) -> ChatResult` performs bounded structured tool calls and records `AgentTrace`/`ToolCall`.

- [ ] Write tests using a fake adapter that requests a tool, then returns a grounded answer, plus a max-round refusal.
- [ ] Run tests to verify the runner is absent.
- [ ] Implement the protocol, OpenAI-compatible HTTP adapter, tool registry, argument validation, timeout, and deterministic fallback.
- [ ] Route chat through the runner while preserving SSE event contracts.
- [ ] Run all Agent/chat/RAG tests without network access.

### Task 4: RAG evaluation metrics

**Files:**
- Modify: `backend/app/evals/grounded.py`, `backend/app/api/v1/admin.py`
- Create: `backend/app/evals/metrics.py`
- Test: `backend/app/tests/test_rag_evaluation.py`

**Interfaces:**
- `recall_at_k(relevant, retrieved, k) -> float`
- `mean_reciprocal_rank(relevant, retrieved) -> float`
- `citation_precision(answer_citations, supported_citations) -> float`
- `groundedness(answer, evidence) -> float`
- `build_evaluation_summary(cases) -> dict[str, object]`

- [ ] Write deterministic metric tests with exact expected scores.
- [ ] Run them to verify the functions are missing.
- [ ] Implement metrics and expose them in `/api/v1/admin/rag/evaluations` with case details.
- [ ] Run evaluation and admin tests.

### Task 5: Full test stabilization and end-to-end coverage

**Files:**
- Modify: `backend/app/tests/conftest.py` or add shared fixture utilities as needed
- Create: `backend/app/tests/test_e2e_core_flows.py`
- Create: `frontend/src/lib/__tests__/api-client.test.ts` when test setup supports it
- Modify: `frontend/package.json` only if a deterministic test command is missing

**Interfaces:**
- Backend test command: `pytest -q`.
- Frontend checks: `npx tsc --noEmit`, `npm run build`, and Vitest tests.

- [ ] Run the full backend suite and record each failure category separately.
- [ ] Add coverage for registration/search/cart/order, size/policy chat, upload/index, and handoff.
- [ ] Fix only test-environment issues or production regressions proven by failures.
- [ ] Run backend and frontend checks from clean, non-conflicting processes.

### Task 6: README and diagrams

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/diagrams/fashionrag-architecture.mmd`
- Create: `docs/diagrams/order-checkout-sequence.mmd`
- Create: `docs/diagrams/agent-rag-sequence.mmd`

**Interfaces:**
- README documents local SQLite/Mock startup, Docker production-like startup, demo accounts, API examples, environment variables, test commands, and known Docker limitations.
- Mermaid diagrams describe module boundaries and critical request flows.

- [ ] Write documentation sections and diagrams from the implemented interfaces.
- [ ] Check every command/path against the repository and remove stale claims.
- [ ] Run a README command/path audit and include verification status honestly.
