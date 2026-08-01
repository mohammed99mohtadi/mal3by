# Booking and Security Remediation Roadmap

This roadmap splits the audit findings into reviewable units. Each unit must preserve the existing API unless its scope explicitly includes a versioned contract change. Migrations are additive; deployed migration files must not be edited.

## Recommended first unit: A1 — concurrent hold invariant

**Implementation status (2026-08-01): IMPLEMENTED, POSTGRESQL VALIDATION PENDING.** Revision `c3d4e5f6a7b8` follows `b8c9d0e1f2a3`. It creates `btree_gist` safely and adds `excl_bookings_active_court_time_overlap` over equal court IDs and half-open `[start,end)` ranges for `pending`, `pending_payment`, and `confirmed`. Exact-name `IntegrityError` handling rolls back and returns existing safe 409 response. SQLite mapping tests pass; opt-in PostgreSQL invariant/concurrency tests exist but remain skipped without an explicitly confirmed isolated database.

**Scope:** Make creation of overlapping active booking intervals for one court impossible under PostgreSQL concurrency. Define active statuses and buffer semantics precisely. Convert expected contention into a stable 409 response.

**Likely files:** booking/availability services, Booking model, one new Alembic revision, PostgreSQL test fixtures, new concurrency tests.

**Migration:** Yes. Prefer a PostgreSQL range/exclusion invariant when variable intervals and buffers can be represented safely; otherwise use a court-scoped locking/advisory-lock design with a supporting overlap index. Preflight existing duplicate intervals before adding a constraint. Do not pretend SQLite provides the same guarantee.

**Tests:** Two simultaneous holds, 50-request final-slot burst, adjacent intervals, buffers, expired/cancelled/rejected rows, transaction retry/deadlock behavior, and migration upgrade/downgrade on PostgreSQL.

**Exit criteria:** Exactly one active overlap commits; loser receives documented 409; query plan uses intended index; SQLite functional suite and PostgreSQL integration suite pass; operational rollback documented.

**Risk:** High. Range semantics, time zones, buffer rules, and live duplicate data can make a constraint unsafe. Keep unit limited to hold creation; confirmation race comes next.

**Deployment:** Confirm backup; persist expired-hold cleanup; run preflight overlap SQL from hardening audit; resolve every returned pair; verify extension privilege; deploy compatible error mapping; migrate; smoke-test adjacency, different courts, inactive statuses, and concurrent collision. Constraint creation may lock/scan `bookings`. No extra overlap index is added because exclusion constraint already creates its GiST support structure. Under contention PostgreSQL serializes conflicting GiST checks; one commit succeeds and loser receives 409, at cost of lock wait.

**Rollback:** Stop booking writes, downgrade one revision to remove constraint, retain shared `btree_gist`, then restore app only if needed. This reopens race; never treat downgrade as data repair.

## A2 — secure booking confirmation

**Implementation status (2026-08-01): IMPLEMENTED.** Public `confirm-payment` requests cannot mutate booking state: anonymous callers receive 401 and authenticated callers receive 403, including booking owners. Existing court-owner/admin status workflows remain supported. Privileged confirmation and internal `confirm_booking_after_verified_payment()` use one strict lifecycle validator and safe database error mapping. No payment provider or webhook is implemented.

**Future payment integration:** A verified webhook/service must authenticate provider messages, validate amount and currency against booking snapshot, reject replays through durable unique event/idempotency records, and call internal confirmation transactionally. Until then, no normal user path can confirm.

**Remaining concurrency work:** Confirmation authority is hardened, but confirm/cancel/expire row locking or optimistic versioning and PostgreSQL race tests remain required before payments. No migration was needed for this unit.

## Ordered units

| Unit | Scope | Likely changes / migration | Tests and exit criteria | Risk |
|---|---|---|---|---|
| A1 | Concurrent hold invariant — implemented, PostgreSQL validation pending | Booking service; migration `c3d4e5f6a7b8`; opt-in tests | Static upgrade/downgrade valid; isolated PostgreSQL race run still required | High |
| A2 | Secure booking confirmation — implemented; concurrency follow-up remains | Public confirmation denial; shared privileged/internal validator; no migration | Owner/anonymous/other denial; privileged/internal success; invalid-state rejection | High |
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
