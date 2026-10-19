# FashionRAG Design

## Scope

FashionRAG is a single-brand apparel commerce system with customer storefront, operations console, knowledge retrieval, and an auditable AI shopping assistant. Delivery is staged: the first executable release is a single-brand MVP, while the architecture retains boundaries for the full domain.

The MVP includes authentication, RBAC, product and SKU management, real-time inventory, cart, mock checkout, knowledge ingestion, size and inventory consultation, and basic administration. Coupons, reviews, shipping detail, human takeover workflows, and full analytics are completed in later phases.

## Architecture

The system uses a modular monolith with a separate Next.js 15 frontend and FastAPI backend. PostgreSQL 16 with pgvector is the system of record. Redis provides cache, rate limiting, and Celery broker support. MinIO stores product images and uploaded knowledge source files. Celery workers parse, chunk, embed, and index documents.

All model endpoints are OpenAI-compatible and configured solely through environment variables. Tests use mock chat and embedding implementations, so no paid model dependency exists in the test suite.

Business facts are authoritative only when obtained from relational tables: prices, SKU availability, inventory, order state, and user-owned records. Knowledge documents supply evidence and citations but never overwrite system state.

## Frontend

The Next.js application uses route groups for the customer storefront and the operations console. TanStack Query owns server state and cache invalidation. Zustand is limited to client interaction state, such as the session shell and cart UX. React Hook Form and Zod validate forms. The application provides responsive layouts for desktop, tablet, and mobile.

Customer routes cover home, product listing, product detail, cart, checkout, orders, account settings, and an SSE-enabled concierge page. Administration routes cover dashboard, catalog, inventory, orders, users, knowledge, conversations, agent traces, and configuration.

## Backend Modules

The backend is organized into API, core, database, models, schemas, repositories, services, integrations, tasks, RAG, and agents. Route handlers perform request validation and authorization only. Domain services coordinate transactions and write audit records. Repositories encapsulate persistence queries.

Domain services are: auth, users, catalog, inventory, cart, orders, payment, shipping, coupons, favorites, reviews, conversations, knowledge, agent, analytics, and audit.

## Data Model

Identity uses User, Role, Permission, UserAddress, and UserPreference. Catalog uses ProductCategory, Product, ProductImage, ProductTag, ProductSku, Color, Size, SizeChart, Inventory, and InventoryTransaction. Commerce uses Cart, CartItem, Order, OrderItem, Payment, Shipment, Coupon, and UserCoupon. Engagement uses ProductFavorite and ProductReview.

AI and knowledge use Conversation, Message, KnowledgeDocument, KnowledgeChunk, AgentTrace, ToolCall, CustomerFeedback, and HumanHandoff. AuditLog records privileged, inventory, order, refund, and knowledge operations.

Indexes include order number, user ID, product status, SKU code, available inventory, knowledge document version, common list filters, and pgvector nearest-neighbor search over KnowledgeChunk embeddings.

## RAG and Agent

Knowledge files are uploaded to MinIO, parsed, cleaned, semantically chunked by heading, paragraph, policy clause, and product context, embedded, and persisted with document version, source title, section, page, type, and optional product ID. Reindexing and deletion are asynchronous and synchronize document metadata with vectors.

At runtime the assistant identifies intent and entities, invokes strictly typed tools for live data, retrieves keyword and vector evidence with product/type/version filters, optionally reranks results, and composes a bounded model context. It replies in Chinese with citations where evidence exists. It must not expose prompts, secrets, or hidden reasoning.

Tools are search_products, get_product_detail, query_inventory, recommend_size, retrieve_knowledge, compare_products, get_user_preferences, save_user_preference, get_order_status, get_shipping_status, check_return_policy, and create_human_handoff.

If evidence is missing, the assistant asks a focused follow-up or clearly states that it cannot confirm the answer. When appropriate it creates a human handoff. Each retrieval and tool invocation is persisted as AgentTrace and ToolCall data.

## Security and Reliability

JWT access and refresh tokens protect authenticated operations. RBAC protects administration and service workflows. Resource ownership checks protect addresses, orders, conversations, and user data. Chat endpoints use rate limiting. Uploads validate content type and size. Logs mask passwords, tokens, and provider keys.

All mutating inventory, order, refund, and administrative operations emit audit logs. Checkout uses a payment provider interface backed by a mock implementation. Inventory mutations use database transactions and row-level locking to avoid overselling.

## Delivery Plan

1. Infrastructure and database: Compose, settings, migrations, response/error conventions, audit base, and seed data.
2. Identity: registration, login, refresh tokens, RBAC, profile, and addresses.
3. Catalog and inventory: products, SKUs, size charts, publishing, stock transactions, and tests.
4. Commerce: cart, coupons, checkout, inventory reservation, mock payment, cancellation, and refund.
5. Customer UI: storefront, filters, product detail, cart, checkout, order, and account workflows.
6. Knowledge and RAG: file ingestion, chunking, mock embeddings, retrieval, and citations.
7. Agent: SSE chat, conversation context, typed tools, tracing, feedback, and handoff.
8. Administration UI and analytics: operational workflows, retrieval observability, and dashboards.
9. Delivery: Docker verification, linting, type checks, test coverage, OpenAPI examples, and deployment documentation.

Every phase runs its focused automated tests before the next phase begins. The final verification runs the complete backend, frontend, and end-to-end suites against mock AI providers.

## Phase One File Set

Phase One creates the root environment and Compose files; backend Docker, package, Alembic, application entrypoint, configuration, errors, request IDs, logging, database base/session/seed modules, initial ORM modules, common schemas, API router and health endpoint, Celery configuration, and migration/health tests. It also creates frontend Docker and initial Next.js provider and API-client files, plus architecture, ER, and agent-flow documentation.

## Acceptance Criteria

The finished system supports customer registration, catalog browsing and filtering, SKU selection, cart and mock checkout. Administrators can manage catalog, SKUs, inventory, orders, and knowledge documents. The assistant maintains multi-turn conversation context and uses live product, inventory, order, and knowledge tools. Product recommendations are published and sellable; inventory and pricing are live database values; size answers are grounded in size charts; policy answers cite knowledge sources; unsupported claims are declined or escalated. Docker Compose starts the full local system independently.
