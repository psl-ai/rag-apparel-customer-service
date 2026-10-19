# Identity Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; unavailable in this workspace) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the customer identity and personal-center workflow from registration through profile, addresses, preferences, favorites, reviews, cart and order reuse.

**Architecture:** Keep JWT authentication and modular services. Add typed profile/engagement schemas and APIs with user-scoped queries. Add a small Zustand session store and a single API client that refreshes tokens once on 401.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x, Next.js 15, Zustand, TanStack Query, Vitest.

## Global Constraints

- Private resources are always filtered by authenticated user ID.
- Existing response envelope and request IDs remain unchanged.
- No plaintext passwords or tokens are logged.
- Tests use SQLite and mocked fetch only.

### Task 1: Typed profile and engagement backend

**Files:**
- Create: `backend/app/schemas/profile.py`, `backend/app/schemas/engagement.py`
- Create: `backend/app/services/engagement.py`
- Modify: `backend/app/services/profile.py`
- Create: `backend/app/tests/test_profile_engagement.py`

**Interfaces:** `ProfileService.update_user`, `upsert_preferences`, `EngagementService.toggle_favorite`, `list_favorites`, `create_review`, `list_reviews`.

- [ ] Write failing tests for typed profile updates, default address switching, preference upsert, favorite idempotency, review creation, and cross-user denial.
- [ ] Run focused tests and verify missing methods/models behavior.
- [ ] Implement schemas and minimal service methods with ownership checks.
- [ ] Run focused tests and existing service tests.

### Task 2: Profile and engagement APIs

**Files:**
- Modify: `backend/app/api/v1/profile.py`
- Create: `backend/app/api/v1/engagement.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/app/tests/test_profile_api.py`

- [ ] Write failing API tests for profile read/update, address CRUD, preferences, favorite toggle/list, review create/list, authentication and ownership.
- [ ] Verify red, implement endpoints and uniform responses, verify green.

### Task 3: Session store and refresh-aware API client

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/lib/session-store.ts`
- Modify: `frontend/src/lib/api-client.ts`
- Create: `frontend/src/lib/session-store.test.ts`

- [ ] Write failing Vitest tests for localStorage hydration, logout cleanup and one-shot refresh retry.
- [ ] Verify red, implement Zustand store and API helper, verify green.

### Task 4: Login/register/account frontend

**Files:**
- Create: `frontend/src/app/login/page.tsx`, `frontend/src/app/register/page.tsx`, `frontend/src/app/account/page.tsx`
- Modify: `frontend/src/app/layout.tsx`, `frontend/src/app/globals.css`
- Modify: `frontend/src/lib/api-client.ts`

- [ ] Add form states, error states, authenticated redirects, address/preference/favorite/review views, and responsive navigation.
- [ ] Run `npm run build` and frontend tests.

### Task 5: Integrate existing customer pages and documentation

**Files:**
- Modify: `frontend/src/app/products/[id]/page.tsx`, `frontend/src/app/cart/page.tsx`, `frontend/src/app/checkout/page.tsx`, `frontend/src/app/orders/page.tsx`, `frontend/src/app/concierge/page.tsx`
- Modify: `README.md`

- [ ] Replace disabled add-to-cart action with selected SKU + session-aware mutation.
- [ ] Add login/account links and unauthenticated redirects/messages.
- [ ] Run backend focused tests, full frontend build, and document demo credentials/flow.

## Self-review

- The plan is limited to identity/profile and engagement; admin and production security hardening remain separate.
- All new interfaces have named tests and explicit ownership requirements.
- Existing cart/order/chat APIs can reuse the same session client without response changes.
