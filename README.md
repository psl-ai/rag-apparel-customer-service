# 智衣购 RAG｜服装智能导购与客服平台

面向服装电商场景，构建集商品检索、智能问答、个性化导购、库存管理、购物车和订单交易于一体的全栈系统，核心是基于 RAG 的 AI 导购客服能力。

## 功能特性

- **RAG 知识库全流程**：文档上传、解析、分块、向量化、混合检索、知识版本管理及异步索引
- **智能客服 Agent**：意图识别、商品/库存/尺码/售后工具调用、答案生成、引用溯源、拒答及人工转接，支持 SSE 流式对话
- **完整电商闭环**：用户认证、RBAC 权限、商品与 SKU 管理、库存扣减、购物车、订单、模拟支付、退款
- **前后端分离**：Next.js + TypeScript 商品目录、AI 导购、购物车、结算、订单及运营管理页面
- **离线可运行**：默认 SQLite + Mock 模型，无需配置大模型 API 即可本地演示；生产环境可切换 PostgreSQL/pgvector、Redis、MinIO

## 技术栈

| 层级 | 技术选型 |
|---|---|
| 后端 | Python、FastAPI、SQLAlchemy |
| 数据库 | SQLite（开发）、PostgreSQL + pgvector（生产） |
| 缓存与异步 | Redis、Celery |
| RAG | 文档解析、分块、Embedding、混合检索、引用溯源 |
| Agent | 意图识别、工具调用、SSE 流式输出、Agent Trace |
| 前端 | Next.js、TypeScript |
| 部署 | Docker、Docker Compose |
| 测试 | pytest |

## 快速开始

### 后端

```bash
cd backend
python -m pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:3000/products 查看商品页，http://localhost:3000/concierge 体验 AI 导购，API 文档位于 http://localhost:8000/docs。

### Docker 一键启动

```bash
docker compose up --build
```

## 演示账号

| 角色 | 账号 | 密码 |
|---|---|---|
| 普通用户 | demo@example.com | Demo-123! |
| 管理员 | admin@example.com | Admin-123! |

## RAG / Agent 核心能力

- `POST /api/v1/chat`：中文对话，自动持久化会话、消息、AgentTrace 和 ToolCall
- `POST /api/v1/chat/stream`：SSE 流式输出，事件顺序为 `message_start` → `tool_call` → `citation` → `token` → `message_end`
- 知识库上传 Markdown/TXT/CSV，支持版本管理和重建索引
- 价格、库存来自关系数据库；政策/尺码回答引用知识分块来源；证据不足时拒答并转人工
- 内置离线评测接口，输出 Recall@5、MRR、引用准确率等指标

## 配置

复制 `.env.example` 为 `.env`，配置 `DATABASE_URL`、`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`CHAT_MODEL` 和 `EMBEDDING_MODEL`。未配置时自动使用 SQLite 和 Mock embedding，不会调用付费模型。

## 测试

```bash
cd backend
pytest -q

cd ../frontend
npx tsc --noEmit
npm run build
```

## 项目结构

```
RAG Apparel Intelligent Customer Service & Shopping Guide/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # API 路由
│   │   ├── agents/       # RAG Agent 与工具调用
│   │   ├── rag/          # 知识库、检索、Embedding
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑
│   │   └── tasks/        # Celery 异步任务
│   └── tests/            # 单元测试
├── frontend/             # Next.js 前端
├── docs/                 # 架构文档与时序图
└── docker-compose.yml
```
