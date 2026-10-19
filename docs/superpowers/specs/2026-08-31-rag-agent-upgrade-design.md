# FashionRAG RAG Agent Upgrade Design

## Goal

Turn FashionRAG into an interview-ready, grounded AI shopping assistant. The assistant answers in Chinese, uses real product and inventory data through typed tools, cites knowledge sources, records each retrieval and tool call, streams replies through SSE, and refuses or escalates when evidence is insufficient.

## Scope

This increment delivers a vertical slice rather than a broad unfinished AI surface:

1. Knowledge document ingestion for Markdown, TXT, and CSV.
2. Deterministic text parsing, normalization, section-aware chunking, and source metadata.
3. Mock embeddings and hybrid lexical/vector-like ranking suitable for SQLite development.
4. Retrieval filtered by document type, product ID, and active document version.
5. Structured business tools for products, inventory, size data, knowledge, and handoff.
6. Deterministic agent policy for common intents plus a replaceable OpenAI-compatible model adapter.
7. Conversation storage, SSE streaming, citations, feedback, AgentTrace, ToolCall, and HumanHandoff records.
8. An offline evaluation suite covering grounded answers, real-time data, lack-of-evidence behavior, and prompt-injection resistance.

The release deliberately excludes PDF OCR, DOCX parsing, production reranking, a real human-agent UI, and paid-model test dependencies. These are follow-up extensions after the core grounded-answer contract is stable.

## Architecture

```text
Chat request
  -> intent/entity classifier
  -> typed tool plan
  -> real-time catalog/inventory/size tools + knowledge retrieval
  -> evidence validator
  -> answer composer / optional model adapter
  -> citation formatter + SSE events
  -> conversation, trace, tool-call, feedback persistence
```

The domain data remains authoritative: prices, sellable status, SKU details, inventory, and order state are only read from relational tables. Knowledge chunks provide material, sizing, policy, and brand evidence. They cannot alter business facts or system instructions.

## Persistence

`KnowledgeDocument` stores source metadata, version, type, status, product association, object key, title, and parse failure details. `KnowledgeChunk` stores normalized content, section, page/row source, document version, product association, chunk sequence, and embedding.

`Conversation` and `Message` preserve user and assistant turns. `AgentTrace` records intent, model identity, retrieval context, timing, and outcome. `ToolCall` stores sanitized structured input and output. `CustomerFeedback` stores ratings and comments. `HumanHandoff` records unanswered or escalated conversations.

SQLite development uses deterministic mock embeddings and similarity ranking. PostgreSQL deployment replaces this implementation with pgvector while preserving the retriever interface and metadata filter contract.

## Knowledge Pipeline

Upload validation accepts Markdown, TXT, and CSV with configurable size limits. The parser produces normalized plain text and source locations. Chunking preserves title, headings, row number, product ID, document type, version, and source reference. The task path is designed to be asynchronous through Celery, while local development can execute the same pipeline synchronously.

Documents are treated as untrusted content. Instructions contained inside uploaded material are never interpreted as system directives. Retrieval returns text only as a quoted source, not executable authority.

## Tools and Agent Policy

Tools receive Pydantic request models and return Pydantic result models:

- `search_products`
- `get_product_detail`
- `query_inventory`
- `recommend_size`
- `retrieve_knowledge`
- `compare_products`
- `get_user_preferences`
- `save_user_preference`
- `get_order_status`
- `get_shipping_status`
- `check_return_policy`
- `create_human_handoff`

The first implementation uses deterministic routing for product search, inventory, size, and policy intents so behavior is testable. A model adapter may select or refine an answer only after evidence is assembled. The assistant recommends at most five published, active-SKU products with available inventory. It does not reveal prompts, keys, chain-of-thought, or internal traces.

If inventory or price is requested, a live tool result is required. If a policy or material claim is requested, a retrieved source is required. If evidence is missing, the response explicitly says it cannot confirm the claim and either asks a focused follow-up or creates a handoff.

## SSE Contract

`POST /api/v1/chat/stream` returns `text/event-stream` events in this sequence:

```text
event: message_start
event: tool_call
event: citation
event: token
event: message_end
```

Each event includes a request ID, conversation ID, and a typed JSON payload. The non-streaming endpoint returns the equivalent final message payload for simpler clients and tests.

## Security and Observability

Conversation and order tools enforce user ownership. Agent traces redact secrets, passwords, tokens, and sensitive user fields. Chat endpoints apply configurable rate limiting. Files are validated before ingestion. The agent never passes raw knowledge text to an instruction parser.

The admin trace API exposes intent, elapsed time, retrieval source identifiers, tool calls, final status, and feedback. It does not expose model reasoning or hidden prompts.

## Evaluation

The repository includes deterministic fixtures and automated cases for:

- policy answer includes a source citation;
- real-time inventory answer matches the database;
- size answer cites the product size chart;
- unavailable products are not recommended;
- malicious document content does not override assistant policy;
- missing evidence produces refusal or handoff;
- unauthorized conversation/order access is denied;
- streaming protocol emits the required event sequence.

Evaluation output records pass rate and failed assertion details. It does not require a network model provider.

## Delivery Order

1. Define document, retrieval, tool, chat, and trace schemas plus test fixtures.
2. Implement parsing, chunking, local embedding, retrieval, and source citations.
3. Implement typed tools and deterministic agent policy.
4. Add conversation persistence, non-streaming chat, and trace storage.
5. Add SSE endpoint, feedback, and handoff.
6. Add evaluation tests and admin trace read API.
7. Add knowledge and concierge frontend pages after backend contracts are stable.
8. Add pgvector adapter and Docker integration verification when Docker is available.

## Acceptance Criteria

Users can ask an inventory question and receive a live stock-grounded answer. They can ask a size or return-policy question and receive a cited answer from a product size chart or knowledge document. Unsupported questions produce a clear uncertainty response or handoff. Every chat request records a conversation message, trace, retrieval sources, and tool calls. The complete path works with SQLite and mock embeddings without a paid model.
