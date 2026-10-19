# FashionRAG Identity and Profile Design

## Scope

This increment completes the customer identity and personal-center path. It adds typed profile APIs, a browser session store with refresh-token recovery, login/register pages, account data views, favorites, reviews, and navigation links used by the existing cart/order/concierge pages.

## Backend

Pydantic schemas validate profile updates, address fields, preference payloads, favorites and reviews. `ProfileService` owns user-scoped profile/address/preference queries. `EngagementService` owns idempotent favorite toggles and review creation/listing. Every query includes the authenticated user ID for private resources; product reviews are public only after being created by an authenticated user.

Refresh tokens remain JWT-based for this increment. The frontend stores access/refresh tokens in localStorage and retries one request after a 401 by calling `/auth/refresh`; logout removes both tokens. Production can later add server-side token rotation without changing UI contracts.

## Frontend

Routes:

- `/login`: email/password login, error and loading states.
- `/register`: email/password/display-name registration followed by login.
- `/account`: profile, addresses, body/style preferences, favorites and recent orders.

The Zustand `useSessionStore` exposes `user`, `accessToken`, `refreshToken`, `setSession`, `logout`, and `hydrate`. API helpers use one authenticated request path with refresh retry. Navigation shows account/cart/concierge links and keeps mobile layouts usable.

## Tests

Backend tests verify typed validation, refresh token issuance, address ownership, default-address behavior, preference upsert, favorite idempotency, review creation, and private resource denial. Frontend tests verify session persistence/logout and form submission/error states using mocked fetch; no paid services are used.

## Acceptance

A new user can register, log in, reload the page without losing session, open `/account`, create/delete an address, save preferences, favorite a published product, and submit a review. Cart, checkout, orders and concierge requests automatically reuse the session token. Invalid or cross-user resource IDs return the existing uniform error envelope.

## Deferrals

Email verification, password reset, OAuth, MFA, server-side refresh-token revocation, and admin user management remain later hardening work.
