# Booking and Security Remediation Roadmap

This roadmap splits the audit findings into reviewable units. Each unit must preserve the existing API unless its scope explicitly includes a versioned contract change. Migrations are additive; deployed migration files must not be edited.

## Recommended first unit: A1 — concurrent hold invariant

**Scope:** Make creation of overlapping active booking intervals for one court impossible under PostgreSQL concurrency. Define active statuses and buffer semantics precisely. Convert expected contention into a stable 409 response.

**Likely files:** booking/availability services, Booking model, one new Alembic revision, PostgreSQL test fixtures, new concurrency tests.

**Migration:** Yes. Prefer a PostgreSQL range/exclusion invariant when variable intervals and buffers can be represented safely; otherwise use a court-scoped locking/advisory-lock design with a supporting overlap index. Preflight existing duplicate intervals before adding a constraint. Do not pretend SQLite provides the same guarantee.

**Tests:** Two simultaneous holds, 50-request final-slot burst, adjacent intervals, buffers, expired/cancelled/rejected rows, transaction retry/deadlock behavior, and migration upgrade/downgrade on PostgreSQL.

**Exit criteria:** Exactly one active overlap commits; loser receives documented 409; query plan uses intended index; SQLite functional suite and PostgreSQL integration suite pass; operational rollback documented.

**Risk:** High. Range semantics, time zones, buffer rules, and live duplicate data can make a constraint unsafe. Keep unit limited to hold creation; confirmation race comes next.

## Ordered units

| Unit | Scope | Likely changes / migration | Tests and exit criteria | Risk |
|---|---|---|---|---|
| A1 | Concurrent hold invariant | Booking/availability service; model; new migration | PostgreSQL races; one winner and stable conflict | High |
| A2 | Locked lifecycle transitions | Confirm, cancel, expire; row lock or optimistic version; possibly version column migration | Confirm-vs-expire/cancel races; deterministic idempotent retry | High |
| B1 | Cleanup transaction ownership | Cleanup service/endpoint/job boundary; no migration expected | Expirations persist in fresh session; failure rolls back | Medium |
| B2 | Cancellation/completion policy | Policy module/service, schemas, timestamps/events | Cutoff boundaries, end-time completion, actor matrix | Medium |
| B3 | Rescheduling decision | Design record first; later replacement workflow | Old/new slot atomicity and payment-delta cases | High; defer until payment model |
| C1 | Production auth configuration | Config/startup, deployment docs | Production refuses fallback secret/debug; rotation rehearsal | High |
| C2 | JWT/session hardening | Security/auth/cookie routes | iss/aud/exp/JTI, clock boundary, logout/revocation design | Medium |
| C3 | IDOR/schema consistency | Endpoint errors and write schemas | Cross-object matrix; unknown fields rejected; private data absent | Medium |
| D1 | Abuse-control foundation | Middleware/dependencies/config; likely rate-limit storage dependency only after design approval | IP/account limits, 429, proxy identity, bypass tests | Medium |
| D2 | Booking/match/review quotas | Domain services; optional quota/event tables | Active-hold and spam limits under concurrency | Medium |
| E1 | Availability query batching | Availability/pricing queries | Fixed query budget and result parity | Medium |
| E2 | PostgreSQL indexing | One measured migration | `EXPLAIN ANALYZE` on production-shaped datasets; no redundant index | Medium |
| F1 | Structured logging | Logging config/middleware/redaction | Request/booking/error IDs present; secrets/PII absent | Medium |
| F2 | Monitoring/alerts | Deployment configuration and runbooks | Synthetic alert tests and ownership acknowledged | Medium |
| G1 | Backup/restore operational gate | Platform configuration and operations docs; no app migration | Restore drill meets approved RPO/RTO | High |
| G2 | Historical retention | User/court deletion policy; new FK/soft-delete migration | Paid/history rows survive account/court lifecycle | High |
| H1 | Payment persistence | Payment attempts/events, idempotency and reconciliation migrations | Amount/currency, duplicate event, failure/timeout/refund cases | High |
| H2 | Verified payment state machine | Webhook/service/API/frontend contract | User cannot self-confirm; signature and replay tests | High |
| I1 | Transactional notification outbox | Outbox migration, event producer, worker | Commit/rollback atomicity, retry and deduplication | Medium |
| I2 | Notification channels/reminders | Worker adapters and scheduling | Preference, locale, retry, dead-letter tests | Medium |

## Delivery rules

- One unit per branch/PR where practical.
- Start every migration unit with production-shaped data preflight and backup confirmation.
- Require PostgreSQL CI for concurrency, partial-index, FK, and migration behavior.
- Preserve server-authoritative prices and object-level authorization.
- Add observability before payment rollout, not after incidents.
- Do not introduce rescheduling as an in-place time/court update.

## Release gates

**Before public launch:** A1, C1, D1/D2 minimum controls, plus P0 regression coverage.

**Before payments:** A2, B1/B2, F1/F2, G1/G2, H1/H2, and a successful restore drill.

**Later optimization:** E1/E2 after measurement and I2 channel expansion; accessibility and locale E2E remain required before claiming full production UX readiness.
