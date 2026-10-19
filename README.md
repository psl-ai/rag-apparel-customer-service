# FashionRAG

基于 RAG 的服装商品智能客服与个性化导购系统。

## 当前可运行范围

- FastAPI 健康检查、统一响应和请求 ID
- 用户注册、登录、刷新 Token、RBAC
- 商品分类、公开商品搜索/详情、运营商品编辑与发布
- SKU、库存调整与库存不足保护
- 购物车、模拟支付下单、订单列表
- Next.js 15 前端壳与服务状态页

## 本地开发

后端：

```powershell
cd backend
python -m pip install -e ".[dev]"
$env:DATABASE_URL = "postgresql+psycopg://fashionrag:fashionrag@localhost:5432/fashionrag"
uvicorn app.main:create_app --factory --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

Docker Desktop 启动后可执行 `docker compose up --build`。PostgreSQL/pgvector 迁移和 Celery 集成验证需要 Docker 守护进程可用；当前业务单元测试可使用 SQLite。

## API

- `GET /api/v1/health/live`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/categories`
- `GET /api/v1/products`
- `GET /api/v1/products/{id}`
- `POST /api/v1/cart/items`
- `POST /api/v1/orders`

所有响应包含 `request_id`、`code`、`message` 和 `data`。
# FashionRAG

基于 RAG 的单品牌服装商品智能客服与个性化导购系统。当前仓库提供可离线运行的 SQLite + Mock 模型纵向切片，便于开发和秋招演示；生产环境可切换 PostgreSQL/pgvector、Redis、MinIO 和 OpenAI-compatible 服务。

## 本地启动

后端：

```powershell
cd backend
uvicorn app.main:create_app --factory --reload --port 8000
```

前端：

```powershell
cd frontend
npm run dev
```

打开 <http://localhost:3000/>，商品页位于 `/products`，AI 导购位于 `/concierge`，API 文档位于 <http://localhost:8000/docs>。

顾客完整演示路径：访问 `/register` 注册并自动登录，进入 `/products` 选择规格加入购物车，再从 `/cart` 前往 `/checkout` 模拟下单，最后在 `/orders` 或 `/account` 查看订单。已有账号可直接访问 `/login`。演示用户：`demo@example.com` / `Demo-123!`；运营后台演示账号：`admin@example.com` / `Admin-123!`。

## RAG/Agent 本地能力

- `POST /api/v1/chat`：中文非流式对话，自动持久化会话、消息、AgentTrace 和 ToolCall。
- `POST /api/v1/chat/stream`：SSE 事件顺序为 `message_start`、`tool_call`、`citation`、`token`、`message_end`。
- 管理员可通过 `POST /api/v1/knowledge/documents` 上传 Markdown/TXT/CSV，再调用 `/api/v1/knowledge/reindex/{document_id}`。
- 价格、商品上下架、SKU 和库存始终来自关系数据库；政策/尺码回答引用知识分块来源；证据不足时拒答并转人工。

## 配置

复制 `.env.example` 为 `.env`，设置 `DATABASE_URL`、`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`CHAT_MODEL` 和 `EMBEDDING_MODEL`。未配置时自动使用 `fashionrag.db` 和确定性 Mock embedding，不会调用付费模型。

Docker Desktop 未启动时，Alembic/pgvector 集成验证会暂缓；SQLite 本地测试不依赖 Docker。

## RAG 版本与评测

知识文档按 `source_key` 管理不可变版本，只有索引成功的版本会成为检索活动版本。默认 `RAG_RETRIEVER_BACKEND=auto`：SQLite 使用本地混合检索，PostgreSQL 自动使用 pgvector 余弦检索；可以显式设为 `sqlite` 或 `pgvector`。

管理员可调用 `GET /api/v1/admin/rag/evaluations` 查看离线评测摘要。知识上传、重建索引和删除均位于 `/api/v1/knowledge/documents`，生产环境由 Celery worker 承担索引任务；本地 SQLite 以同一索引器同步执行。

个人资料 API 位于 `/api/v1/profile`，收藏和评价 API 位于 `/api/v1/products/{id}/favorite` 与 `/api/v1/products/{id}/reviews`，均要求登录并执行用户隔离。

## 秋招演示流程

1. 启动后端：`cd backend; uvicorn app.main:create_app --factory --reload --port 8000`
2. 启动前端：`cd frontend; npm run dev -- --port 3001`
3. 打开 `http://localhost:3001/register`，或使用演示账号 `demo@example.com / Demo-123!`。
4. 进入 `/products` 搜索“风衣”，打开详情，选择 SKU 后加入购物车。
5. 在 `/checkout` 填写地址并提交模拟支付；使用 `Idempotency-Key` 重试同一请求只会得到原订单。
6. 在 `/concierge` 依次询问“这个商品穿什么尺码”“现在有库存吗”“退换货政策是什么”，观察尺码表、实时库存和政策引用。
7. 使用 `admin@example.com / Admin-123!` 进入 `/admin`，查看订单、库存、知识库和 Agent Trace。
8. 知识库上传支持 Markdown/TXT/CSV；生产环境通过 Celery、Redis、MinIO 和 PostgreSQL/pgvector 执行异步索引。

## 质量与安全说明

- JWT 的角色来自数据库 `user_roles` 关联，不依赖邮箱名称；刷新令牌会重新读取角色。
- CORS 由 `CORS_ORIGINS` 配置，默认允许本地 3000/3001 端口，部署时应收紧为实际前端域名。
- 订单接口支持 `Idempotency-Key` 请求头，重复请求安全返回首次创建的订单。
- RAG 评测接口 `/api/v1/admin/rag/evaluations` 返回 `Recall@5`、MRR、引用准确率和 groundedness 示例指标。
- Mock Chat/Embedding 是默认离线实现；配置 `OPENAI_BASE_URL`、`OPENAI_API_KEY` 和 `CHAT_MODEL` 后可切换 OpenAI-compatible Chat Completions。

## 测试

```powershell
cd backend
pytest -q
cd ..\frontend
npx tsc --noEmit
npm run build
```

Docker Desktop 未启动时，SQLite 本地模式仍可运行；Compose 的 PostgreSQL/pgvector 验证需要先启动 Docker 守护进程。

架构和关键时序图见 [`docs/architecture.md`](docs/architecture.md) 以及 [`docs/diagrams`](docs/diagrams)。
