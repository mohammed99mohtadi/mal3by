# AUTH-1 Identity Architecture Audit

Date: 2026-08-02. Scope: repository state at `fad4c68`. This is an evidence-only audit; no runtime, API, migration, dependency, or production change was made.

## Baseline

| Check | Result |
|---|---|
| Git | `main`, clean, synchronized with `origin/main` |
| Alembic | one head: `c3d4e5f6a7b8` |
| Backend | 249 collected; 232 passed, 17 skipped, 21 warnings |
| Frontend tests | 33 files, 195 tests passed |
| Frontend lint/typecheck/build | passed; all routes built |
| Production | not accessed; backend used `DEBUG=false`, local configured test database |

The first root-level Alembic invocation lacked `script_location`; rerunning from `backend/` succeeded. The first backend run was interrupted by the command timeout at 51% with no failures; a complete rerun passed.

## Current user domain

Evidence: `backend/app/models/user.py`, `schemas/user.py`, `services/auth_service.py`, and the baseline user migration.

| Field | Storage | Null | Client input | Returned by `UserResponse` | Finding |
|---|---|---:|---:|---:|---|
| `id` | integer PK, indexed | no | no | yes | Internal identifier exposed to the account/admin role response |
| `full_name` | varchar(100) | no | register/update schema | yes | Serves as both account name and display name |
| `email` | varchar(255), unique/indexed | no | register/login | yes | Private data currently returned by `/users/me`, registration, and role update |
| `hashed_password` | varchar(255) | no | derived only | no | Correctly excluded from response schemas |
| `phone_number` | varchar(20), unique | yes | register/update schema | yes | Private; format is not normalized or strongly validated |
| `role` | varchar(20) | no | admin role schema only | yes | Python enum, but database has no check constraint |
| `is_active` | boolean | no | no public input | yes | Only active/inactive state exists |
| `is_admin` | boolean | no | no public input | yes | Duplicates `role=admin`, creating two authorization sources |
| `created_at` | datetime | no | no | yes | No `updated_at`, last-login, suspension, deletion, or verification timestamps |

`UserCreate` ignores extra fields, so public `role`/`is_admin` injection does not work; the service also explicitly sets `PLAYER` and `False`. `UserUpdate` exists but no endpoint uses it. There is no user service separate from the auth service.

## Profile support

Profile data is stored only as `User.full_name` and optional `phone_number`; there is no Profile model and no frontend-only persisted profile data.

| Capability | Classification | Evidence |
|---|---|---|
| Display name | supported | `full_name`; rendered by profile and match/review summaries |
| Profile editing | partial | `UserUpdate` schema exists; no route/service/UI |
| Avatar, country, city/area, preferred language, preferred sports, position, skill level, DOB, bio, privacy | missing | no columns, schemas, or endpoints |
| Date of birth | unsuitable for initial MVP unless age/legal requirement exists | adds sensitive data without a current product need |

Preferred sports and position should be normalized relations/enums if added, not free-form columns. Avatar should store a managed asset reference/URL, not bytes. Privacy needs explicit public schema rules before public player pages.

## Registration and admin visibility trace

Current flow:

`POST /auth/register` → duplicate email/phone checks → bcrypt hash → `User(role=player,is_admin=false,is_active=true)` → commit → `UserResponse`.

It does **not** create a Profile, issue a session, verify email, or create an audit event. Frontend registration sends name/email/optional phone/password, then redirects to login; login separately obtains JWT and sets the HTTP-only cookie. After login, server-rendered navigation resolves `/users/me` and shows account links. Players can book and join matches. A new user does not appear in an admin list because no admin list/detail endpoint exists; an admin can only change a known numeric user ID's role.

Duplicate email and phone return specific 400 messages, enabling registration account enumeration. Creation is one user insert/commit; there is no multi-record transaction requirement today.

## Owner and admin findings

Today an owner is created by direct database/test manipulation or `PATCH /admin/users/{id}/role`. There is no application, review, approval, rejection, suspension, or owner-status history. Public registration cannot become owner. Owner endpoints correctly require owner/admin and generally enforce court ownership; admins override ownership. Owner capabilities include court CRUD/activation, availability, closures, pricing, court bookings/status, dashboard, and review responses. Court deletion cascades from owner deletion and is unsafe for historical retention.

Admin user management supports only role change, with protection against demoting the last active admin. Missing: list/search/filter users, detail, activate/suspend/reactivate, owner applications, related bookings/matches, and audit events. Admin frontend routes are authorized shells; owner routes are partial shells. Review moderation endpoints are real, but not identity administration.

## Authentication and security

Positive controls: bcrypt with generated salts; generic login failure text; JWT signature/expiry validation; `sub` required and converted to user ID; inactive users rejected on authenticated requests; HTTP-only, SameSite=Lax cookie; `secure` in production; safe local return-path validation; last-admin demotion guard; backend authorization is authoritative.

P0 risks:

1. A hard-coded default JWT secret exists in `core/config.py`. A missing production secret could produce predictable tokens. Startup must fail outside explicit local/test mode.
2. Direct role promotion is the only owner path and bypasses application/approval evidence and audit history.
3. Deleting a user cascades bookings and owned courts while match/review FKs restrict deletion. This is both inconsistent and destructive to financial/operational history; no account deletion endpoint currently triggers it, but the model policy is unsafe.
4. No audit record exists for role changes or future suspension/approval decisions.

P1 risks:

- Tokens last seven days, contain `sub`, `email`, and `exp`, and cannot be revoked; email is unnecessary stale personal data in the token.
- Logout clears only the browser cookie; JWT remains valid. No refresh-token/session registry exists.
- Login does not reject inactive users before issuing a token; enforcement happens on later protected requests.
- No rate limiting, lockout, credential throttling, or password-reset/email-verification controls.
- Password policy is length-only (8–100); no compromised-password protection.
- Registration reveals duplicate email/phone; timing may also distinguish login paths despite generic output.
- `role` plus `is_admin` duplicates authority and is checked repeatedly in backend/frontend.
- Cookie lacks an explicit centralized domain/prefix/CSRF strategy; SameSite=Lax is helpful but not a complete mutation policy.

## Frontend findings

- Login/register/profile are live. Profile is read-only and receives all `UserResponse` account fields.
- Registration is not automatic login. Login cookie duration mirrors backend token duration.
- Middleware only normalizes locale; it is not an auth guard. Individual server pages and catch-all route resolve cookie/API state.
- Privileged links depend on server-resolved `role`/`is_admin`; backend still enforces access. No client-side role flash was found in the server-rendered path.
- Owner/admin/settings/notifications are route-catalog shells or partial views. User menu links to settings/notifications despite missing backend.
- No owner-application UI and no live admin-users UI.

## Test gaps

Existing coverage includes registration, duplicates, validation, login success/failure, `/users/me`, sensitive password exclusion, client-controlled role defense, admin role changes, non-admin denial, last-admin protection, owner route/ownership checks, and broad bookings/matches/reviews authorization.

P0 missing tests:

| Scenario | Expected | Target file | Database |
|---|---|---|---|
| Production-like startup without a supplied secret | startup/config validation fails | `tests/test_security.py` | none |
| Inactive account login | no token; safe denial | `tests/test_auth.py` | user row toggled inactive |
| Owner promotion requires approved application (after AUTH-3) | direct invalid transition rejected; approved transition atomic | `tests/test_owner_application.py` | users + owner applications + audit events |
| Role/owner/suspension mutation audit | immutable event with actor, subject, action, time | `tests/test_audit_events.py` | users + audit events |
| Account retention policy | historical booking/match/review survives account closure/anonymization | `tests/test_account_lifecycle.py` | complete linked graph |
| Admin newly registered user visibility (after AUTH-4) | list/detail returns safe admin schema, never hash | `tests/test_admin_users.py` | admin + new player |

P1: logout/revocation behavior, enumeration-safe registration, rate limits, profile ownership/update validation, owner suspension, admin filters/pagination, dual role/is_admin consistency, token payload without email. P2: public-profile privacy permutations, avatar lifecycle, preferred-sport performance, audit retention jobs.

## Decision

The current authentication is a sound small-account foundation, not a complete identity system. AUTH-1 documents the smallest safe extension: retain `User` as credential/account source, add one-to-one `Profile`, single canonical role, `OwnerApplication`, and immutable `AuditEvent`. Recommended first implementation is **AUTH-2A User/Profile persistence**; see the roadmap.
