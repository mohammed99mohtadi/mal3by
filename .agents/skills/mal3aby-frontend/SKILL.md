---
name: mal3aby-frontend
description: Implement and review MAL3ABY's Next.js 16, React 19, and TypeScript frontend while preserving localized routes, server/client boundaries, API contracts, authentication, shared components, forms, states, performance, and tests. Use for changes under frontend/.
---

# MAL3ABY Frontend

- Read `frontend/AGENTS.md` and relevant local Next.js docs under `node_modules/next/dist/docs`; this repository uses Next.js 16.2.12.
- Inspect the affected route, component, `lib/api.ts`, `lib/copy.ts`, route inventory, tests, and matching backend contract.
- Keep `/ar/*` and `/en/*` in the `[locale]` App Router tree; `proxy.ts` normalizes locale. Preserve document `lang`, `dir`, and font class.
- Use Server Components by default. Add `use client` only for interaction/browser state and keep serialized props small.
- Read protected data server-side through the HttpOnly `mal3by_session` cookie. Never expose tokens to client JavaScript.
- Keep Next API routes narrow same-origin adapters. Shape safe payloads and preserve FastAPI status/contract semantics.
- Treat backend schemas/services as business authority. Visual redesigns must preserve working logic and cannot invent endpoints or fields.
- Preserve safe `returnTo`; UI role checks guide navigation but backend authorization grants access.
- Reuse UI primitives, shared states, navigation models, localized copy, types, and focused domain helpers.
- Model loading, empty, 401/403/404, retryable failure, mutation pending/success/error, and stale/conflict states.
- Use typed forms with immediate client feedback and authoritative backend validation; focus an error summary or first invalid field.
- Avoid `any`, duplicated fetch logic, unlocalized raw errors, broad rewrites, and oversized page components.
- Apply React performance guidance: start independent work together, avoid waterfalls, direct-import, minimize client bundles, and prevent needless rerenders.
- Use TDD and Vitest/Testing Library. For substantial work run lint, typecheck, test:run, and build from `frontend`.
