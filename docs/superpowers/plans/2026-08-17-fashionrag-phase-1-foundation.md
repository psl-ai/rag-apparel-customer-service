# FashionRAG Phase 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Docker-startable foundation with PostgreSQL/pgvector, Redis, MinIO, FastAPI, Next.js, Alembic, deterministic seed data, and automated health and migration tests.

**Architecture:** The FastAPI service owns the database schema and exposes versioned health endpoints. Compose manages local infrastructure and injects every external setting through `.env`. A minimal Next.js shell verifies frontend-to-backend connectivity without prebuilding the storefront. Initial migrations establish the full model baseline required by later domain phases, while behavior remains limited to health and seed operations.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL 16 with pgvector, Redis 7, MinIO, Celery, Next.js 15, TypeScript, Tailwind CSS, pytest, pytest-asyncio, httpx, Ruff, mypy, Docker Compose.

## Global Constraints

- Use a modular monolith; routes validate and authorize while services own domain workflows.
- Read model, embedding model, base URLs, and API keys from environment variables only; never commit secrets.
- Test only against mock LLM and embedding implementations; tests must not require external paid services.
- Use UTC timestamps, UUID primary keys, explicit database indexes, and transactional database sessions.
- Use a uniform API envelope: `request_id`, `code`, `message`, and `data`.
- Preserve business authority in PostgreSQL; future RAG documents provide evidence only.
- Keep Phase 1 limited to infrastructure, initial schema, health endpoints, and deterministic seed data.

---

## Planned File Structure

```text
.env.example                         Local configuration contract
docker-compose.yml                   Local service topology
README.md                            Startup and verification commands
backend/pyproject.toml               Python dependencies and tool configuration
backend/Dockerfile                   API/worker image
backend/alembic.ini                  Alembic command configuration
backend/alembic/env.py               Migration metadata and settings
backend/alembic/versions/0001_initial_schema.py
backend/app/main.py                  FastAPI application factory
backend/app/core/config.py           Typed settings
backend/app/core/errors.py           Error envelope and exception mapping
backend/app/core/logging.py          Structured logging configuration
backend/app/core/request_id.py       Correlation-ID middleware
backend/app/db/base.py               Declarative base and metadata imports
backend/app/db/session.py            Engine and unit-of-work dependency
backend/app/db/seed.py               Idempotent demonstration data
backend/app/models/*.py              Initial ORM model groups
backend/app/schemas/common.py        Common API response schemas
backend/app/api/v1/router.py         API v1 aggregation
backend/app/api/v1/health.py         Liveness/readiness endpoints
backend/app/tasks/celery_app.py      Celery application configuration
backend/app/tests/conftest.py        Isolated test database fixtures
backend/app/tests/test_health.py     Health contract tests
backend/app/tests/test_migrations.py Schema/extension verification
frontend/package.json                Next.js scripts and dependencies
frontend/Dockerfile                  Frontend image
frontend/src/app/layout.tsx          Root layout and providers
frontend/src/app/page.tsx            Minimal storefront shell
frontend/src/lib/api-client.ts       Typed health API client
frontend/src/lib/query-provider.tsx  TanStack Query provider
frontend/src/components/providers.tsx Client provider composition
```

### Task 1: Establish Backend Tooling and Settings Contract

**Files:**
- Create: `.env.example`, `backend/pyproject.toml`, `backend/Dockerfile`, `backend/app/core/config.py`, `backend/app/core/logging.py`
- Test: `backend/app/tests/test_config.py`

**Interfaces:**
- Produces `Settings`, loaded through `get_settings() -> Settings`.
- `Settings` exposes `database_url`, `redis_url`, `minio_endpoint`, `openai_base_url`, `openai_api_key`, `chat_model`, and `embedding_model`.

- [ ] **Step 1: Write the failing settings test**

```python
from app.core.config import Settings

def test_settings_reads_required_local_values(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@db:5432/fashionrag")
    settings = Settings()
    assert settings.database_url.host == "db"
    assert settings.chat_model == "mock-chat"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend; pytest app/tests/test_config.py -v`

Expected: FAIL because `app.core.config` does not exist.

- [ ] **Step 3: Implement typed settings and tooling configuration**

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: PostgresDsn
    redis_url: RedisDsn
    minio_endpoint: str
    openai_base_url: HttpUrl
    openai_api_key: SecretStr = SecretStr("mock-key")
    chat_model: str = "mock-chat"
    embedding_model: str = "mock-embedding"
```

Configure Ruff, mypy, pytest, Python 3.13, FastAPI, SQLAlchemy, Alembic, Celery, and test dependencies in `pyproject.toml`. Keep `.env.example` secret-free and give every setting a local Compose value.

- [ ] **Step 4: Run focused verification**

Run: `cd backend; pytest app/tests/test_config.py -v; ruff check .; mypy app/core`

Expected: PASS with no lint or type errors.

- [ ] **Step 5: Commit**

```bash
git add .env.example backend
git commit -m "chore: add backend settings and tooling"
```

### Task 2: Create Compose Topology and Service Images

**Files:**
- Create: `docker-compose.yml`, `frontend/Dockerfile`, `frontend/package.json`, `frontend/next.config.ts`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`
- Modify: `.env.example`, `README.md`
- Test: `backend/app/tests/test_compose_contract.py`

**Interfaces:**
- Consumes `DATABASE_URL`, `REDIS_URL`, and MinIO settings from Task 1.
- Produces Compose services `db`, `redis`, `minio`, `backend`, `worker`, and `frontend`.

- [ ] **Step 1: Write the failing Compose contract test**

```python
from pathlib import Path

def test_compose_declares_required_services():
    text = Path("../docker-compose.yml").read_text(encoding="utf-8")
    for service in ("db:", "redis:", "minio:", "backend:", "worker:", "frontend:"):
        assert service in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend; pytest app/tests/test_compose_contract.py -v`

Expected: FAIL because Compose does not exist.

- [ ] **Step 3: Implement service topology**

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
  redis:
    image: redis:7-alpine
  minio:
    image: minio/minio:latest
  backend:
    build: ./backend
  worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=INFO
  frontend:
    build: ./frontend
```

Use Compose health checks and `depends_on` conditions. Mount only named database/object-store volumes. Do not expose provider credentials in image layers.

- [ ] **Step 4: Run focused verification**

Run: `docker compose config; cd backend; pytest app/tests/test_compose_contract.py -v`

Expected: Compose configuration renders successfully and the test passes.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml frontend .env.example README.md backend/app/tests/test_compose_contract.py
git commit -m "chore: add local service topology"
```

### Task 3: Implement Application Factory, Error Envelope, and Health API

**Files:**
- Create: `backend/app/main.py`, `backend/app/core/errors.py`, `backend/app/core/request_id.py`, `backend/app/api/v1/router.py`, `backend/app/api/v1/health.py`, `backend/app/schemas/common.py`
- Test: `backend/app/tests/test_health.py`

**Interfaces:**
- Produces `create_app() -> FastAPI` and `GET /api/v1/health/live`.
- Successful responses use `ApiResponse[T]` with `request_id`, `code`, `message`, and `data`.

- [ ] **Step 1: Write the failing API test**

```python
from httpx import ASGITransport, AsyncClient
from app.main import create_app

async def test_live_health_returns_response_envelope():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok"}
    assert response.json()["request_id"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend; pytest app/tests/test_health.py -v`

Expected: FAIL because the application factory is absent.

- [ ] **Step 3: Implement the minimal API contract**

```python
@router.get("/live", response_model=ApiResponse[HealthStatus])
async def live_health(request: Request) -> ApiResponse[HealthStatus]:
    return ApiResponse.ok(request_id=request.state.request_id, data=HealthStatus(status="ok"))
```

Install request-ID middleware before routes, set an `X-Request-ID` response header, and map validation and application exceptions into the same envelope.

- [ ] **Step 4: Run focused verification**

Run: `cd backend; pytest app/tests/test_health.py -v; ruff check app; mypy app`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app
git commit -m "feat: add versioned health API"
```

### Task 4: Define ORM Metadata, Session Lifecycle, and Initial Models

**Files:**
- Create: `backend/app/db/base.py`, `backend/app/db/session.py`, `backend/app/models/base.py`, `backend/app/models/user.py`, `backend/app/models/catalog.py`, `backend/app/models/commerce.py`, `backend/app/models/conversation.py`, `backend/app/models/knowledge.py`, `backend/app/models/audit.py`
- Test: `backend/app/tests/test_models.py`

**Interfaces:**
- Produces `Base`, `get_db_session() -> AsyncIterator[AsyncSession]`, and importable ORM models from the approved design.
- All entity identifiers are `UUID`; inventory is one-to-one with `ProductSku`; `KnowledgeChunk.embedding` uses pgvector.

- [ ] **Step 1: Write the failing model metadata tests**

```python
from app.db.base import Base

def test_initial_metadata_contains_core_tables():
    names = set(Base.metadata.tables)
    assert {"users", "products", "product_skus", "inventories", "orders", "knowledge_chunks", "agent_traces"} <= names

def test_product_sku_code_is_indexed():
    sku = Base.metadata.tables["product_skus"]
    assert any(index.name == "ix_product_skus_code" for index in sku.indexes)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend; pytest app/tests/test_models.py -v`

Expected: FAIL because metadata and models do not exist.

- [ ] **Step 3: Implement model groups and session lifecycle**

```python
class TimestampedUuidModel(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

Define every approved entity with explicit foreign keys and indexes. Avoid service methods and domain behavior in this task. Configure an async SQLAlchemy engine with `pool_pre_ping=True` and a transaction-scoped `AsyncSession` dependency.

- [ ] **Step 4: Run focused verification**

Run: `cd backend; pytest app/tests/test_models.py -v; ruff check app/models app/db; mypy app/models app/db`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db backend/app/models backend/app/tests/test_models.py
git commit -m "feat: add initial domain schema models"
```

### Task 5: Create and Verify the Initial Alembic Migration

**Files:**
- Create: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_initial_schema.py`
- Test: `backend/app/tests/test_migrations.py`

**Interfaces:**
- Consumes `Base.metadata` from Task 4.
- Produces a migration that enables `vector` and creates all initial tables and indexes.

- [ ] **Step 1: Write the failing migration test**

```python
async def test_initial_migration_enables_vector_and_creates_products(db_connection):
    extensions = await db_connection.execute(text("SELECT extname FROM pg_extension"))
    assert "vector" in set(extensions.scalars())
    tables = await db_connection.execute(text("SELECT to_regclass('public.products')"))
    assert tables.scalar_one() == "products"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend; pytest app/tests/test_migrations.py -v`

Expected: FAIL because the migration has not been applied.

- [ ] **Step 3: Implement Alembic integration and migration**

```python
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("products", ...)
```

Generate table DDL from Task 4 metadata, review it for names and indexes, and explicitly enable `pgcrypto` only if a database-side UUID default is used. Make downgrade drop tables in foreign-key-safe reverse order.

- [ ] **Step 4: Run focused verification**

Run: `docker compose up -d db; cd backend; alembic upgrade head; pytest app/tests/test_migrations.py -v`

Expected: migration succeeds and the test passes against pgvector.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic backend/app/tests/test_migrations.py
git commit -m "feat: add initial database migration"
```

### Task 6: Add Readiness Checks, Celery Configuration, and Seed Data

**Files:**
- Create: `backend/app/tasks/celery_app.py`, `backend/app/db/seed.py`
- Modify: `backend/app/api/v1/health.py`, `backend/app/main.py`
- Test: `backend/app/tests/test_readiness.py`, `backend/app/tests/test_seed.py`

**Interfaces:**
- Produces `GET /api/v1/health/ready`, `celery_app`, and `seed_database(session: AsyncSession) -> None`.
- Readiness returns `503` if PostgreSQL or Redis is unreachable.

- [ ] **Step 1: Write the failing readiness and idempotent-seed tests**

```python
async def test_seed_database_is_idempotent(session):
    await seed_database(session)
    await seed_database(session)
    result = await session.execute(select(func.count()).select_from(Product))
    assert result.scalar_one() == 3

async def test_ready_health_reports_dependencies(client):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["data"]["database"] == "ok"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend; pytest app/tests/test_readiness.py app/tests/test_seed.py -v`

Expected: FAIL because the readiness endpoint and seed function are absent.

- [ ] **Step 3: Implement dependency checks and deterministic catalog data**

```python
async def seed_database(session: AsyncSession) -> None:
    if await session.scalar(select(Product.id).limit(1)) is not None:
        return
    session.add_all([brand_category, three_products, sku_rows, inventory_rows, policy_document])
    await session.commit()
```

Seed exactly three published apparel products with color, size, SKU, inventory, a size chart, and one return-policy knowledge document. Readiness must ping PostgreSQL and Redis with bounded timeouts. Configure Celery using the Redis broker URL and JSON serialization.

- [ ] **Step 4: Run focused verification**

Run: `cd backend; pytest app/tests/test_readiness.py app/tests/test_seed.py -v; ruff check app; mypy app`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/tasks backend/app/db/seed.py backend/app/api/v1/health.py backend/app/tests
git commit -m "feat: add readiness checks and demo seed data"
```

### Task 7: Add the Minimal Next.js Application Shell

**Files:**
- Create: `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/lib/api-client.ts`, `frontend/src/lib/query-provider.tsx`, `frontend/src/components/providers.tsx`
- Test: `frontend/src/app/page.test.tsx`

**Interfaces:**
- Produces a responsive page at `/` and `getLiveHealth(): Promise<HealthData>`.
- Uses `NEXT_PUBLIC_API_BASE_URL` as the only frontend API base configuration.

- [ ] **Step 1: Write the failing page test**

```tsx
it("renders the FashionRAG service name", () => {
  render(<Home />);
  expect(screen.getByRole("heading", { name: "FashionRAG" })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend; npm test -- --run src/app/page.test.tsx`

Expected: FAIL because the page module does not exist.

- [ ] **Step 3: Implement the minimal shell and API client**

```ts
export async function getLiveHealth(): Promise<HealthData> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/health/live`);
  if (!response.ok) throw new Error("Health request failed");
  return (await response.json()).data;
}
```

Render only a responsive service shell with a live-status loading, success, and error state. Add TanStack Query at the root. Do not build catalog UI in Phase 1.

- [ ] **Step 4: Run focused verification**

Run: `cd frontend; npm test -- --run src/app/page.test.tsx; npm run lint; npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add frontend application shell"
```

### Task 8: Document and Verify Fresh Local Startup

**Files:**
- Modify: `README.md`, `docs/architecture.md`, `docs/er-diagram.md`, `docs/agent-rag-flow.md`
- Test: `backend/app/tests/test_startup_contract.py`

**Interfaces:**
- Produces reproducible local commands for configuration, Compose startup, migration, seeding, tests, linting, and teardown.

- [ ] **Step 1: Write the failing startup documentation test**

```python
from pathlib import Path

def test_readme_contains_fresh_startup_command():
    readme = Path("../README.md").read_text(encoding="utf-8")
    assert "docker compose up --build" in readme
    assert "alembic upgrade head" in readme
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend; pytest app/tests/test_startup_contract.py -v`

Expected: FAIL because README does not document the commands.

- [ ] **Step 3: Document and run the clean-start sequence**

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

Document backend and frontend URLs, health endpoint, test commands, mock-model guarantee, architecture diagram, ER diagram, and Agent/RAG flow. Verify Compose health, migration, seed command, `/api/v1/health/live`, and frontend loading state.

- [ ] **Step 4: Run full Phase 1 verification**

Run: `docker compose up --build -d; docker compose exec backend alembic upgrade head; docker compose exec backend pytest app/tests -v; docker compose exec backend ruff check .; docker compose exec backend mypy app; docker compose exec frontend npm test -- --run; docker compose exec frontend npm run build`

Expected: all commands exit successfully; the live endpoint returns the uniform response envelope.

- [ ] **Step 5: Commit**

```bash
git add README.md docs backend/app/tests/test_startup_contract.py
git commit -m "docs: document phase one local deployment"
```

## Plan Self-Review

Coverage: the plan implements the approved Phase 1 scope, including Compose infrastructure, typed configuration, backend/API foundation, full baseline ORM model surface, migration, async task configuration, seed data, frontend health shell, and startup documentation. Authentication, catalog workflows, commerce workflows, knowledge ingestion behavior, Agent behavior, and operations UI intentionally remain in later delivery plans.

Consistency: `Settings`, `ApiResponse`, `create_app`, `Base`, `get_db_session`, `seed_database`, `celery_app`, and `getLiveHealth` are each introduced before use. The model migration follows ORM metadata. API and frontend tests target the response contract introduced by Task 3.

Completeness scan: no unresolved markers, deferred task instructions, or undefined cross-task interfaces remain.
