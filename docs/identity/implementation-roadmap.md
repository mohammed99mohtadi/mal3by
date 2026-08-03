# Identity Implementation Roadmap

Each unit must preserve current API behavior unless its contract change is explicitly versioned and tested.

## AUTH-2A — User/Profile persistence (recommended first)

- Scope: add Profile one-to-one; backfill display name/phone/preferred locale; add User `updated_at`; establish canonical-role consistency without removing compatibility yet.
- Likely files: user/profile models, schemas, Alembic migration, model exports, seed/test factories.
- APIs: none required in this unit.
- Tests: migration upgrade/backfill/downgrade policy, uniqueness/nullability, registration creates profile atomically, role/is_admin consistency guard.
- Risks: existing user data, phone uniqueness, SQLite/Postgres parity, registration transaction.
- Exit: one head; every user has one profile; registration is atomic; full regressions pass; no new public exposure.

## AUTH-2B — Profile API

- Scope: private self read/update and distinct public schema only if public profiles are approved.
- Likely files: users/profile endpoints, service, schemas, frontend API types later.
- Migration: none beyond 2A unless fields are revised.
- APIs: `GET/PATCH /users/me/profile`; optional privacy-aware public read.
- Tests: ownership, field validation, normalization, extra-field rejection, privacy, inactive denial.
- Exit: safe editable fields only; password/role/status/contact cannot be mass-assigned.

## AUTH-3A — Role hardening

- Scope: one canonical role; central authorization helpers; fail-safe secret configuration; inactive login denial; prepare transition policy.
- Migration: reconcile/drop `is_admin` only after compatibility rollout; DB role constraint.
- APIs: retain current admin role endpoint temporarily with stricter transition service.
- Tests: inconsistent legacy state, only-admin protection, secret startup, token claims, every role boundary.
- Exit: one authorization source; no default production secret; direct player→owner transition can be disabled for 3B/3C.

## AUTH-3B — Owner application persistence

- Scope: OwnerApplication model/statuses, submission/withdraw service, no approval yet.
- Migration: table, pending uniqueness, reviewer/application indexes.
- APIs: player submit/read/withdraw.
- Tests: one pending request, duplicate/retry behavior, owner/admin constraints, validation.
- Exit: player can submit exactly one valid pending application; role unchanged.

## AUTH-3C — Owner approval service/API

- Scope: admin list/detail/approve/reject; atomic application decision + role assignment + audit event.
- Migration: AuditEvent may be introduced here if not 4C; never approve without it.
- Tests: concurrency/idempotency, non-admin denial, decision transitions, audit, rollback.
- Exit: public registration remains player; owner role is granted only by approved, audited workflow.

## AUTH-4A — Admin users list/detail

- Scope: paginated list, search, role/status filters, detail and related-resource summaries.
- APIs: `/admin/users`, `/admin/users/{id}`, separate paginated bookings/matches/audit tabs.
- Tests: new-user visibility, filters, pagination, sensitive exclusion, query counts/N+1.
- Exit: newly registered player is discoverable; no password/token/public overexposure.

## AUTH-4B — Suspend/reactivate

- Scope: canonical status, reason, transition service, session denial, owner operational safeguards.
- Migration: status/timestamps if not already in 2A.
- Tests: immediate token denial, reactivation, only-admin guard, owner/admin edge cases, audit.
- Exit: reversible, audited state transitions with preserved history.

## AUTH-4C — Audit events

- Scope: append-only model/service, admin read endpoint, retention/redaction policy; move earlier to 3C if needed.
- Tests: immutability, authorization, actor/subject retention, metadata redaction, pagination.
- Exit: role, owner decision, suspension/reactivation changes are atomically recorded.

## AUTH-5 — Frontend identity experience

- Scope: editable profile, owner application/status, live owner/admin navigation and admin user/application views.
- Likely files: locale routes/components/API proxies/types/copy/tests; replace shell routes only where backend is live.
- Tests: AR/EN, RTL/mobile/a11y, unauthorized/forbidden/loading/error/empty, no role flash, end-to-end transitions.
- Exit: UI exposes only supported workflows and backend remains authoritative.

## AUTH-6 — Email verification and password reset

- Scope: hashed single-use purpose tokens, expiry/replay protection, delivery abstraction, email/password changes, session invalidation.
- Migration/API/tests: token tables and full enumeration/replay/expiry coverage.
- Exit: no raw token storage/logging; safe generic responses; verified transitions.

## AUTH-7 — Rate limiting and final security review

- Scope: register/login/reset throttling, abuse telemetry, cookie/session policy, revocation/versioning decision, final threat review.
- Tests: limit dimensions, recovery, proxy/IP trust, no account enumeration.
- Exit: documented production configuration and operational monitoring.

## Why AUTH-2A first

It creates the missing identity boundary without prematurely exposing APIs. It makes later profile, owner application, privacy, and admin work consistent; it also forces an early decision on backfill and transaction safety. Do not begin frontend AUTH-5 first.

## AUTH-2A delivery status

Implemented: UserProfile model/metadata, unique one-to-one relationship, bounded optional fields, atomic registration, existing-user backfill migration, rollback/relationship/constraint/static migration tests, and no API exposure.

Deliberately deferred: User column/role cleanup, phone migration, profile API, public visibility, avatar URL trust checks, and sport/position/skill persistence until a normalized taxonomy exists. AUTH-2B is next and must define separate private/public schemas before exposing data.
