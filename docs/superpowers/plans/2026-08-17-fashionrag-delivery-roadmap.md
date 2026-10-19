# FashionRAG Delivery Roadmap

## Delivery Order

1. Foundation: Compose environment, FastAPI and Next.js scaffolding, database schema baseline, migrations, settings, health checks, seed data, lint/type/test tooling.
2. Identity: registration, credential login, token refresh/rotation, RBAC, profile, and addresses.
3. Catalog: categories, product lifecycle, images, tags, SKU, color, size charts, inventory, and audit records.
4. Commerce: cart, coupon redemption, stock reservations, order lifecycle, mock payment, cancellation, refund, shipment model, and customer order APIs.
5. Storefront: public catalog/search/filter/detail pages; protected cart, checkout, order, and account workflows.
6. Knowledge: MinIO upload, parsing, document versioning, chunking, mock embeddings, pgvector retrieval, citations, reindexing, and deletion.
7. Concierge: conversation persistence, SSE response protocol, structured tools, safe answer policy, feedback, traces, and human handoff.
8. Operations: product, stock, order, user, knowledge, conversation, and trace administration; dashboard data endpoints and UI.
9. Release: acceptance E2E suite, model-provider integration tests behind opt-in settings, Docker deployment validation, OpenAPI examples, and operations documentation.

Each delivery step has its own detailed implementation plan and must pass focused tests before the next step starts. Phase 1 is specified in `2026-08-17-fashionrag-phase-1-foundation.md`.
