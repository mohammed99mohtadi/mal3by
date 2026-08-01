# Booking and Security Hardening Audit

Audit date: 2026-08-01

Repository baseline: `main` at `a7415ae`

Scope: read-only repository audit; documentation is the only output.

## Executive summary

The existing functional baseline is healthy: the backend suite passes and Alembic has one head. Authorization checks are generally explicit, booking prices are calculated server-side and snapshotted, private-match visibility has dedicated tests, and the frontend stores the access token in an HttpOnly cookie rather than browser storage.

At audit baseline, availability was checked in application code before an unconstrained insert, so concurrent requests could hold the same court interval. A1 now implements a PostgreSQL exclusion constraint and safe conflict mapping, but isolated PostgreSQL validation remains pending. The booking path is therefore not cleared for public concurrent traffic yet. Separately, an authenticated booking owner can call `confirm-payment` and create a confirmed booking without evidence from a payment provider. Production configuration also has unsafe fallbacks, abuse controls are absent, and no verified backup/restore process is documented.

Severity totals: **Critical 0, High 5, Medium 8, Low 4, Informational 2**.

## A1 implementation update — 2026-08-01

Status: **implemented, PostgreSQL validation pending**.

- New head: `c3d4e5f6a7b8`, parent `b8c9d0e1f2a3`.
- PostgreSQL extension: `btree_gist`, created with `IF NOT EXISTS`.
- Constraint: `excl_bookings_active_court_time_overlap`.
- Invariant: equal `court_id` plus overlapping `tstzrange(start_time, end_time, '[)')` is rejected when status is `pending`, `pending_payment`, or `confirmed`.
- Adjacent intervals remain valid. Same interval on different courts remains valid. `cancelled`, `expired`, `rejected`, `refunded`, and `completed` do not participate.
- Existing service availability/buffer validation remains for friendly early rejection. Database constraint is final protection for true interval overlap; buffer-only concurrency remains service-enforced.
- PostgreSQL exclusion violation is recognized only by exact constraint name, rolled back, and mapped to existing safe HTTP 409 detail. Other integrity failures retain generic HTTP 400 handling. SQL and constraint names are not returned.
- Server-authoritative price calculation and one hold insert/commit transaction remain unchanged.
- SQLite service tests cover safe error mapping. Opt-in PostgreSQL tests cover active/inactive statuses, courts, adjacency, and two-session concurrency, but were skipped because no isolated PostgreSQL database was confirmed.

### Production preflight — do not run until target is confirmed

First persist expiration cleanup so stale `pending`/`pending_payment` rows have status `expired`. Then run this read-only query. Migration must stop if it returns rows:

```sql
SELECT
    first_booking.id AS first_booking_id,
    second_booking.id AS second_booking_id,
    first_booking.court_id,
    first_booking.status AS first_status,
    second_booking.status AS second_status,
    tstzrange(first_booking.start_time, first_booking.end_time, '[)') AS first_interval,
    tstzrange(second_booking.start_time, second_booking.end_time, '[)') AS second_interval
FROM bookings AS first_booking
JOIN bookings AS second_booking
  ON first_booking.court_id = second_booking.court_id
 AND first_booking.id < second_booking.id
 AND tstzrange(first_booking.start_time, first_booking.end_time, '[)')
     && tstzrange(second_booking.start_time, second_booking.end_time, '[)')
WHERE first_booking.status IN ('pending', 'pending_payment', 'confirmed')
  AND second_booking.status IN ('pending', 'pending_payment', 'confirmed')
ORDER BY first_booking.court_id, first_booking.start_time, second_booking.start_time;
```

Deployment order: confirm backup and restore readiness; persist expired-hold cleanup; run preflight; verify permission to create `btree_gist`; deploy compatible service error mapping; migrate to `c3d4e5f6a7b8`; run invariant smoke tests and monitor 409/DB lock rates. Constraint creation scans and locks `bookings`, so schedule based on measured table size and lock tolerance.

Rollback: stop booking writes if correctness is uncertain; downgrade one revision to drop only the exclusion constraint; keep shared `btree_gist`; roll back application if needed. Downgrade restores prior race risk and does not repair data, so use only with explicit approval.

## Baseline and environment safety

| Check | Result |
|---|---|
| Initial worktree | Clean |
| Recent history | `a7415ae` at audit baseline |
| Backend tests | **222 passed, 1 skipped, 21 warnings** in 416.59s |
| Alembic heads | One: `b8c9d0e1f2a3` |
| Test database | SQLite, created by test fixtures; SQLite foreign-key behavior differs from PostgreSQL |
| Application default database | Local SQLite fallback; production URL is environment-loaded |
| Production access | None performed; no migration upgrade/downgrade was run |
| JWT settings | Pydantic settings load environment / `.env`; secret value not reproduced here |
| CORS | No FastAPI `CORSMiddleware` configuration found |

The test run used a temporary virtual environment because the repository virtual environment was stale. No command used production credentials or changed a database. The warnings are deprecations in Starlette/httpx and HTTP 422 constants plus a pytest cache warning.

## Booking lifecycle

Active conflict statuses are `pending`, `pending_payment`, and `confirmed`. Terminal/non-blocking statuses include `cancelled`, `expired`, `rejected`, `completed`, and `refunded` as applicable.

| Transition | Actor and preconditions | Writes / transaction | Existing coverage | Gap |
|---|---|---|---|---|
| create → `pending_payment` | Authenticated user; active court; timezone, future, duration, hours, closure, buffer, overlap rules pass | Price snapshot, hold expiry and timestamps inserted; service commits | Valid hold, validation, price snapshot, sequential overlap | No concurrency lock/constraint; public backend schema permits client-selected 1–60 minute hold |
| `pending(_payment)` → `confirmed` | Booking user, court owner, or admin; hold not expired | Status and confirmation timestamps; service commits | Success, expired/cancelled rejection | No payment proof, row lock, idempotency, or amount verification |
| `pending(_payment)` → `cancelled` | Booking user, court owner, or admin | Status, reason, timestamp; service commits | Own/other-user checks and lifecycle success | Repeated cancellation is an error; no stable event/audit record |
| `confirmed` → `cancelled` | Booking user, court owner, or admin | Same writes; service commits | Permission and transition tests | No cancellation cutoff, refund coordination, race protection, or notification |
| `pending(_payment)` → `expired` | Lazy reads/availability cleanup, admin cleanup, or owner/admin status patch | Status and expiry timestamps; cleanup only flushes unless caller later commits | Expired availability, hold status, admin authorization | Cleanup endpoint does not commit; expiry/confirmation race is unlocked |
| `pending(_payment)` → `rejected` | Court owner/admin through status update | Status and timestamp; service commits | General transition/permission coverage | No reason/event/notification requirement |
| `confirmed` → `completed` | Court owner/admin through status update | Status and completed timestamp; service commits | Transition matrix coverage | No enforced end-time precondition found in booking service |
| `confirmed`/`completed` → `refunded` | Court owner/admin through status update | Status and refunded timestamp; service commits | Transition matrix only | No provider refund, amount, reference, or reconciliation record |

Invalid transitions return HTTP 400. Status changes are mutable fields on one booking row; there is no append-only booking status history.

Rescheduling and changing court/time are unsupported. Keep them unsupported until payment semantics exist. The safe future design is an atomic replacement workflow: validate and reserve the new interval, link old/new bookings, handle price/payment delta, then cancel the old booking. A plain update would reopen the overlap race. For an early MVP without payments, cancel-and-create may be acceptable if clearly non-atomic.

## Double-booking analysis

At audit time protection was **service-enforced only**. A1 now adds the PostgreSQL exclusion constraint described above while preserving the early service check. The overlap query still reads all active bookings for a court and checks times in Python. Booking confirmation/lifecycle updates still do not use `FOR UPDATE`; those races remain A2 scope.

| Race | Current protection | Classification | Outcome |
|---|---|---|---|
| Two users hold same slot | Both run a read before either insert | Missing | Both can commit |
| Two pending holds both confirm | Status/expiry checked independently | Missing | Both can become confirmed |
| Expiry during confirmation | Wall-clock check, then unlocked write | Service-enforced | Last writer can win |
| Cancellation vs confirmation | Independent read-modify-commit | Missing | Last commit can overwrite intent |
| Closure vs hold creation | Separate unlocked transactions | Missing | Closure and hold may coexist |
| Price changes between availability and hold | Hold recalculates and snapshots current server price | Database snapshot + service enforcement | Integrity is acceptable; displayed quote may change |
| Concurrent final-slot requests | Same as simultaneous holds | Missing | Capacity/slot guarantee absent |

SQLite tests prove sequential business rules only. They cannot prove PostgreSQL row locks, range exclusion constraints, isolation behavior, deadlock handling, or concurrent transaction retry. PostgreSQL integration tests are required.

## Cancellation, payment, and notification readiness

Cancellation exists for users, court owners, and admins on pending or confirmed bookings. There is no cutoff, fee/refund policy, immutable audit trail, idempotent response, notification hook, or payment coordination. Cancellation reason is optional free text. Modification/rescheduling does not exist.

The current lifecycle lacks payment intent ID, provider, authoritative payment status, idempotency key, verified webhook event IDs, captured/refunded amounts, failure details, and reconciliation state. The accepted `payment_reference` input is ignored. Before a provider integration, add normalized payment attempt/event records, currency/amount checks against the booking snapshot, signed webhook verification, unique provider event and idempotency constraints, transactional state transitions, timeout handling, refunds, and reconciliation jobs. Provider selection is intentionally out of scope.

No notification service, event table, outbox, queue, or worker was found. Booking confirmation/cancellation/expiration, join-request decisions, match cancellation, and reminders need durable events. Safest MVP: write an outbox row in the same transaction as the domain change, then let an idempotent background worker deliver and retry. Inline external calls must not control transaction success.

## Database relationships and query safety

| Area | Evidence and assessment |
|---|---|
| User → Court → Booking | User/court ORM relationships use delete-orphan and database FKs use `CASCADE`; deleting a user, sport, or court can erase booking history. Unsafe for disputes, accounting, and payments. Prefer deactivation/anonymization and `RESTRICT` for historical records. |
| Court configuration | Availability, working hours, closures, pricing rules, and date overrides cascade with the court. Appropriate for configuration, but only after historical booking snapshots are independent. Creator FKs generally use `SET NULL`. |
| Booking → Match/Review | Match and review use `RESTRICT`, preserving linked history. Booking deletion can therefore fail when linked, while unlinked history can disappear: inconsistent retention policy. |
| Match graph | Creator/court/booking/participants/requirements/join requests use `RESTRICT`; pending join requests have a PostgreSQL partial unique index. This is stronger historical retention. |
| Uniqueness | Working hours `(court_id, weekday)`, match booking, participants `(match_id,user_id)`, requirement `(match_id,position_code)`, review booking, response review, and pending join request are constrained. Booking interval exclusivity is absent. |
| Booking indexes | Individual court, status, start and end indexes exist. The critical overlap/list queries need composite/partial PostgreSQL indexes, e.g. court + status + time range, validated with `EXPLAIN`. |
| Redundancy | Several unique columns also have explicit indexes, and primary keys use `index=True`; PostgreSQL may receive redundant indexes. Confirm catalog output before changing. |
| Sources of truth | Booking start/end are authoritative for booking; match copies start/end while linking a booking, creating drift potential. Price snapshots are intentionally historical, not duplication to remove. |
| N+1/load risk | Booking detail/list eager-loads court/sport. Slot generation performs closure, booking, and pricing queries per candidate slot; overlap loads all active court bookings into Python. Match/review aggregate queries need load tests. |
| Nullable/orphan risk | Audit actor fields with `SET NULL` preserve rows but lose actor linkage after deletion. This is acceptable only with a separate immutable audit identity snapshot. |

## Alembic audit

Chain is linear: `5de7dc1ae0b4 → ba64a5d872fe → 89bf7f864362 → 70e32c8bda52 → ae676d58b47b → c1a8f4d2e9b0 → d4b7e1c9a2f6 → f1b2c3d4e5f6 → b8c9d0e1f2a3`.

| Revision | Risk | Severity | Evidence / recommended action |
|---|---|---|---|
| `5de7dc1ae0b4` | Destructive cascades begin in baseline | Medium | User/sport deletion cascades courts; establish retention policy in a new migration, never edit baseline |
| `ba64a5d872fe` | No overlap invariant; booking FKs cascade | High | Add a new PostgreSQL-safe concurrency migration after data preflight |
| `89bf7f864362` | Configuration cascades; separate time indexes | Low | Accept cascade; measure composite date/range indexes |
| `70e32c8bda52` | Server defaults and numeric backfill need staging validation | Medium | Test upgrade on production-shaped PostgreSQL snapshot and verify precision/default removal policy |
| `ae676d58b47b` | Lifecycle columns added without concurrency invariant | High | Add constraints/indexes in a later revision; validate old rows before constraints |
| `c1a8f4d2e9b0` | String-backed enums and copied match times can drift | Medium | Add DB checks and invariant tests through new migrations/services |
| `d4b7e1c9a2f6` | Review history intentionally restricts deletion | Low | Document operational deletion/anonymization procedure |
| `f1b2c3d4e5f6` | Compact migration; constraint behavior differs by DB | Low | Exercise upgrade/downgrade on PostgreSQL |
| `b8c9d0e1f2a3` | PostgreSQL partial index is not fully represented by SQLite tests | Medium | Add PostgreSQL duplicate-pending and downgrade tests |

Constraint/index naming is mostly explicit in newer migrations but older autogenerated names vary. Enums are stored as strings, avoiding PostgreSQL enum teardown issues but relying on application validation and selected checks. Boolean defaults should be checked in a staging schema. The suite asserts a single head, not a hard-coded old head. Git history was inspected, but repository state alone cannot prove whether an old deployed migration was edited; compare deployed checksums/manifest before release. Never run a downgrade against live data without a restore point and loss review.

## Authentication and frontend session handling

- Passwords use bcrypt and are never put in JWTs. JWT decoding restricts the configured algorithm and validates expiration.
- JWT payload contains user ID (`sub`) and email. No password, hash, phone, or secret is present; email is still PII and is unnecessary because the user is reloaded from the database.
- Algorithm is HS256. This is acceptable with a strong, rotated secret, but configuration includes a usable fallback secret and `debug=True` fallback. A deployment missing environment values risks token forgery and debug exposure.
- Access tokens last seven days. There are no issuer/audience claims, token ID, refresh tokens, revocation list, rotation, or logout-side invalidation. Role and active state are reloaded per request, which limits stale authorization.
- Registration enforces a minimum eight-character password but no breached/common-password or strength controls. Login is generic; registration distinguishes duplicate email and phone, enabling account enumeration.
- No login/registration throttling or lockout/backoff exists.
- Frontend token cookie is HttpOnly, `Secure` in production, `SameSite=Lax`, path `/`, and seven-day expiry. No token use in `localStorage`/`sessionStorage` was found. Logout expires the cookie. `safeReturnPath` confines redirects to the selected locale and rejects protocol/host forms.
- Frontend server proxies whitelist booking operations and payload keys. The client submits court/time only, and the backend calculates price. Confirmation UI displays success only after a successful backend response, but the backend operation itself is not a real payment confirmation.
- Errors in booking confirmation are generic. Auth forms display backend `detail`, which can expose registration enumeration messages but not stack traces in reviewed paths.
- AR/EN routes and RTL/LTR foundations exist. Booking component tests cover loading, disabled/inactive state, exact payload and safe failure. No evidence of comprehensive Arabic copy, real-device mobile touch-target, screen-reader, or end-to-end locale coverage was found.

No CORS middleware is configured. Same-origin frontend proxying reduces browser need for CORS; if direct browser API access is intended, use an explicit allowlist. Do not enable wildcard origins with credentials.

## Authorization and IDOR review

| Endpoint group | Current control | Gap / conclusion |
|---|---|---|
| Users/admin | `/me` authenticated; role mutation admin-only; final-admin demotion protected | Good tested baseline; registration enumeration remains |
| Courts/owner | Owner role plus per-court ownership; admin override in services | Cross-owner tests exist; deletion semantics threaten history |
| Pricing/availability writes | Authenticated owner of court or admin | Cross-owner/player tests exist; concurrent closure/hold remains |
| Bookings | Object read/cancel/confirm: booking user, court owner, admin; status writes court owner/admin | Guessed IDs yield 403 and disclose existence; more importantly user self-confirms payment |
| Matches/private data | Auth required; private view requires manager, active/pending participant, or invite path | Private visibility tests exist; numeric-ID stranger and invite flows covered |
| Join requests | Request owner can withdraw; creator/admin manages; expected match ID checked; private creation guarded | Strong service tests, including relationship revalidation and lock sequence |
| Reviews | Reviewer manages own review; court owner manages response; admin moderates | Cross-owner and own-booking tests exist; spam throttling absent |

No broad model-to-dict mass assignment was found. Public registration cannot assign roles, and tests verify server-owned booking/match/review fields are ignored or rejected. However, Pydantic defaults often ignore unknown fields; security-critical schemas should explicitly use `extra="forbid"` for consistent failure and telemetry. Numeric IDs appear in responses by design; authorization must remain object-level. Private match endpoints correctly prefer non-disclosing 404 behavior; booking endpoints use 403 after lookup, which leaks the existence of a booking ID but not its details.

Timezone-aware inputs, ordering, duration, advance windows, enum parsing, free-text lengths, and server-side price calculation are present. Some service errors interpolate object IDs/status values, but no raw exception or stack trace response was found. The `/health` response claims the database is connected without executing a database check; it is a liveness response mislabeled as readiness.

## Rate limiting and abuse controls

No rate limiter, per-user active-hold quota, CAPTCHA/challenge, or generalized abuse middleware was found.

| Action | Suggested starting limit | Launch class |
|---|---|---|
| Login | 5/min/account and 20/min/IP; exponential backoff | Required before public launch |
| Registration | 3/hour/IP plus verified contact workflow | Required before public launch |
| Hold creation | 5/min/user, 20/hour; maximum 2 active holds/user; server-fixed short TTL | Required before public launch |
| Join by code | 10/min/user and IP; uniform failure | Required before public launch |
| Join requests | 10/hour/user and 5/day/match | Required before public launch |
| Reviews | 5/day/user plus one-per-booking DB invariant already present | Required before public launch |
| Payment/webhooks | Idempotency plus provider/IP controls; webhook event uniqueness | Required before payments |
| Admin writes/cleanup | Low burst limit, audit log, stronger session policy | Required before payments |
| Public availability/search | 60/min/IP, caching, result/date bounds | Later optimization unless load testing shows need |

Limits are starting policy values, not capacity measurements. Return stable 429 responses and avoid logging credentials, tokens, invite codes, or full PII.

## Performance and scale

Primary hotspot: `generate_available_slots()` loops candidate intervals and repeatedly queries closures, active bookings, and pricing. `check_booking_overlap_with_buffer()` retrieves every active booking for a court without a SQL time-overlap predicate. Under peak traffic this becomes query amplification and Python-side scanning. Preload closures/bookings/pricing once per court/day, filter overlaps in SQL, and add measured composite/partial indexes.

Booking lists are paginated to 100 and eager-load court/sport. Owner lists are paginated. Public availability inputs are bounded. Court, match discovery, participant, and review endpoints have many single-column indexes, but composite indexes must follow observed PostgreSQL query plans. Rating aggregates and match roster loading need dataset tests rather than speculative indexes.

Recommended PostgreSQL performance/concurrency gates:

- 50 concurrent transactions for one final slot: exactly one active hold commits; losers receive stable 409; no deadlocks escape.
- 20 concurrent confirmations/cancellations on one hold: one valid transition wins; retries are idempotent.
- 1,000 courts, 1,000,000 bookings, 100 active bookings/court: one-day availability p95 < 300 ms and bounded query count (target ≤ 8).
- 100,000 matches with 50 participants each: paginated discovery p95 < 300 ms; detail query count constant.
- 1,000,000 reviews across 10,000 courts: rating summary p95 < 250 ms with correct soft-delete filters.

## Logging, monitoring, backup, and recovery

Application structured logging, request/correlation IDs, security audit events, metrics, error monitoring, secret-redaction policy, and alert rules were not found. Alembic has conventional logging only. See the dedicated monitoring plan.

No repository evidence establishes automated PostgreSQL backups, retention, RPO/RTO, pre-migration snapshots, restore instructions, or scheduled test restores. This blocks accepting real payments until verified with the hosting platform and a restore drill. See the dedicated checklist.

## Findings register

| ID | Severity | Title | Affected files | Failure/impact | Fix and required tests | Blocks new features? |
|---|---|---|---|---|---|---|
| BSH-001 | High | Active interval overlap invariant implemented; PostgreSQL validation pending | booking service and `c3d4e5f6a7b8` migration | Constraint design prevents concurrent active overlaps, but isolated PostgreSQL execution is not yet proven | Run opt-in PostgreSQL upgrade/concurrency/downgrade/upgrade tests; keep A2 lifecycle races separate | Yes until PostgreSQL validation passes |
| BSH-002 | High | User can self-confirm “payment” | booking endpoint/service/schema; frontend confirm | Any booking owner can mark unpaid hold confirmed | Remove public trust path; provider-verified, idempotent state machine; forged/duplicate/webhook tests | Yes: payments |
| BSH-003 | High | Unsafe production configuration fallbacks | `core/config.py` | Missing env may activate known fallback signing secret and debug mode | Fail closed outside test/dev; secret strength/rotation checks; startup configuration tests | Yes: public launch |
| BSH-004 | High | No rate limits or active-hold quota | auth, bookings, matches, reviews | Credential attacks, inventory denial, spam and expensive-query abuse | Layered IP/account limits, server TTL, quota, 429 tests | Yes: public launch |
| BSH-005 | High | Backup and restore readiness unverified | operations/deployment docs absent | Data loss cannot be bounded or recovered confidently | Verify automated backups, retention, RPO/RTO and test restore | Yes: real payments |
| BSH-006 | Medium | Cleanup endpoint flushes but does not commit | availability service, booking endpoint | Reports expirations that session close can roll back | Make transaction ownership explicit; persistence/rollback tests | No, but fix early |
| BSH-007 | Medium | Booking history can cascade-delete | user/court/booking models and early migrations | Account/court deletion removes unlinked historical bookings | Soft-delete/anonymize; `RESTRICT`; migration preflight and retention tests | Yes: payments |
| BSH-008 | Medium | Lifecycle updates are unlocked and non-idempotent | booking service | Expiry/cancel/confirm races and retry ambiguity | Row lock/versioning, stable idempotency behavior, race tests | Yes: payments |
| BSH-009 | Medium | Cancellation/completion/refund rules incomplete | booking service/model | No cutoff, end-time enforcement, refund proof, or audit history | Policy service + append-only events; boundary/permission/idempotency tests | Yes: payments |
| BSH-010 | Medium | JWT session posture lacks production claims/revocation | security/config/auth/frontend cookie routes | Seven-day replay window; no audience/issuer/JTI or server logout revocation | Short access token, claims, rotation/revocation strategy; token tests | No, but before scale |
| BSH-011 | Medium | Availability query amplification | availability/pricing services | Per-slot queries and all-active-booking scan degrade at peak | Batch queries, SQL overlap predicate, measured indexes; query-count/load tests | No |
| BSH-012 | Medium | Monitoring and audit telemetry absent | application-wide | Incidents, abuse and booking failures are hard to detect/reconstruct | Structured redacted events, request IDs, metrics and alerts | Yes: payments |
| BSH-013 | Medium | Durable notification delivery absent | booking/match services | State changes produce no reliable customer/owner notification | Transactional outbox + idempotent worker; rollback/retry tests | No |
| BSH-014 | Low | Registration enables account enumeration | auth service/schemas | Duplicate email vs phone responses disclose registered identifiers | Uniform public response/error; retain internal reason; tests | No |
| BSH-015 | Low | JWT contains email PII | auth endpoint/security | Token disclosure exposes email unnecessarily | Keep stable opaque subject only; payload test | No |
| BSH-016 | Low | Unknown schema fields are often ignored | Pydantic schemas | Client mistakes/attack probes are silent and inconsistent | `extra="forbid"` on write schemas; contract tests | No |
| BSH-017 | Low | Possible redundant indexes | models/migrations | Extra write/storage overhead | Inspect PostgreSQL catalog and plans before removal; migration tests | No |
| BSH-018 | Informational | CORS is not explicitly configured | `main.py` | Fine for same-origin proxy; direct browser API would fail or tempt unsafe wildcard | Document topology; add exact allowlist only if needed | No |
| BSH-019 | Informational | Health endpoint is liveness, not DB readiness | `main.py` | Deploy health can report healthy while DB is unavailable | Split liveness/readiness with safe timeout; tests | No |

## Testing gaps

Current tests cover sequential overlap, lifecycle transitions, cancellation authorization, expired holds, price snapshots, booking IDOR, owner isolation, private matches, join requests, reviews, and a single Alembic head. Frontend unit tests cover core EN booking interactions and redirect safety. No true concurrent/PostgreSQL behavior is proven.

### P0 tests

| Scenario | Expected result | Target | Database |
|---|---|---|---|
| Two simultaneous holds for same interval | Exactly one active hold; other stable 409 | new `test_booking_concurrency_postgres.py` | PostgreSQL required |
| Last-slot burst | One winner across 25–50 workers; no leaked DB errors | same | PostgreSQL required |
| Hold expires during confirm | Exactly one terminal state under defined ordering | same | PostgreSQL required |
| Cancel and confirm race | Defined winner; no lost update; retry deterministic | same | PostgreSQL required |
| Closure and hold race | Domain invariant selects one permitted outcome, never conflicting active rows | same | PostgreSQL required |
| Untrusted payment confirmation | User cannot confirm without verified payment event | booking/payment API tests | SQLite sufficient for authorization; PostgreSQL for transaction race |
| Cleanup persistence | Cleanup remains committed in a new session; rollback behavior explicit | `test_booking_lifecycle.py` | SQLite sufficient, repeat on PostgreSQL |
| Production config fail-closed | Missing/weak secret or debug production config stops startup | new config/security tests | SQLite irrelevant |
| Booking retention | User/court lifecycle cannot silently delete historical paid booking | model/migration tests | PostgreSQL required for deployed FK behavior |

P1: cancellation cutoff/end-time/completion/refund policy, duplicate webhook/idempotency, token issuer/audience/expiry boundaries, registration/login throttling, active-hold quotas, query-count/load fixtures, and PostgreSQL upgrade/downgrade tests. P2: full AR/EN end-to-end parity, real-device mobile accessibility/touch targets, screen-reader flows, long-running aggregate benchmarks, and chaos/retry exercises.

## Release conclusion

Normal non-booking feature development can continue if it does not deepen these risks. Public booking launch should wait for PostgreSQL validation of BSH-001 plus BSH-003 and BSH-004. Real payment acceptance should additionally wait for BSH-002, BSH-005, BSH-007 through BSH-009, and BSH-012. After A1 validation, next booking correctness unit is A2 locked lifecycle transitions.
