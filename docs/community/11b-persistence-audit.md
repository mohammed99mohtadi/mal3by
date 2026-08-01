# 11B.1 Read-Only Persistence Audit

## Safety
`backend/.env.example` uses `sqlite:///./mal3ab.db`; `app/db/session.py` creates its engine solely from `settings.database_url`. Tests use the repository test configuration/SQLite; no migration command was run. The actual `.env` URL and all credentials were not printed or used. Alembic must not run until the active URL is verified as isolated local/test.

## Inventory
| Area | File | Current persistence | 11B reuse |
|---|---|---|---|
| Match | `backend/app/models/match.py` | booking, creator, court, visibility, policy, status, skill, capacity and dates | Reuse aggregate |
| Participant | same | unique match/user, pending/approved/rejected/left timestamps | Reuse as current request/roster record |
| Booking link | `backend/app/models/booking.py`, match model | non-null unique booking FK | Already one booking/one match |
| Service | `backend/app/services/match_service.py` | manager checks, capacity refresh, lock-enabled lookup | Extend transaction only |
| API | `backend/app/api/v1/endpoints/matches.py` | existing match API | Do not change in 11B |

### Match fields
`id` PK/index; `creator_id`, `court_id`, `booking_id` non-null RESTRICT FKs/indexed; `booking_id` unique; `title`, `sport_type`, `min_players`, `max_players`, `start_time`, `end_time` non-null; optional description/invite code/cancelled/completed times. Visibility, join policy, status and skill are string-backed Python enums. Constraints enforce min >=2, max >= min, max <=100 and end > start. Discovery indexes exist on sport, visibility, status, skill and start time.

### Participant fields
`id`; non-null RESTRICT `match_id`/`user_id` indexed FKs; string-backed status; joined/approved/rejected/left timestamps; created/updated timestamps. `uq_match_participants_match_user` provides history retention and blocks a second request after leaving.

## Migration history
`5de7dc1ae0b4` baseline; `ba64a5d872fe` bookings; `ae676d58b47b` lifecycle; `c1a8f4d2e9b0` match system; `d4b7e1c9a2f6` reviews/current head. Project uses integer IDs, timezone-aware timestamps, string enum values and SQL check/unique constraints. Baseline booleans use PostgreSQL `true`/`false` text defaults.

## Gap analysis
Already implemented: host ownership (`creator_id`), confirmed-booking service validation, one booking/one match, capacity, public/private, skill, lifecycle cancellation/completion, participant uniqueness, lock-capable `get_match(lock=True)`.

Partial: `start_time/end_time` duplicate booking schedule and must be made derived/validated rather than replaced abruptly; participant pending state is effectively a join request but cannot preserve repeated request history; no requested position, reviewer or review timestamp.

Missing: relational position requirements, requested/selected position, explicit join-request history and stable domain error codes. Deferred: profiles, teams, results, ratings, notifications.

## Minimal schema delta
**Required next:** add nullable `requested_position` to existing participant only if API compatibility permits; otherwise add `match_join_requests` with match/user/status/reviewer/timestamps and a partial active-request unique index (PostgreSQL). Add `match_position_requirements(match_id, position_code, required_count CHECK >0, UNIQUE(match_id,position_code))`.

**Reject now:** host field (creator is host), capacity/visibility/skill/status/booking uniqueness (already present), profile/team/result/rating/notification tables.

Existing rows need no backfill; new nullable position data is safe. Downgrade drops only new tables/indexes/columns.

## Join request decision
Add `MatchJoinRequest`, retaining `MatchParticipant` for roster. The current unique participant record cannot represent withdrawn/rejected history plus a new pending request. Approval writes a participant only once, while requests remain historical. A partial unique active-request index is PostgreSQL-only; SQLite tests need service checks too.

## Transaction design
```text
begin transaction
request = load pending request
match = SELECT match FOR UPDATE
validate open/full policy, eligible confirmed booking, pending request
assert no approved participant for user
count approved participants; if >= max_players => MATCH_FULL
insert approved participant; mark request approved/reviewer/time
set full when count reaches capacity; commit
on integrity/validation error rollback and return 409/domain error
```
Repository needs lock/query/count methods; service owns all transitions. Unique `(match_id,user_id)` and active request index are final safeguards.

## Migration/deployment sequence
11B.2 add position requirements (backward compatible). 11B.3 add join requests and indexes. 11B.4 deploy service transaction, then optional constraints after production verification. Render: backup/check head, migrate isolated staging, deploy compatible app, verify, rollback app then downgrade only if no new data.

## Test plan
Add `tests/test_match_persistence.py`: requirement positive/unique; request active uniqueness/history; booking uniqueness; participant uniqueness. Add `tests/test_match_service.py`: lock approval, full race, duplicate participant, cancellation blocks approval. SQLite sufficient for checks/basic service; PostgreSQL required for partial index and concurrent final-slot sessions. API regressions stay in `tests/test_matches.py`.

## Recommended split
**11B.2 only:** relational position requirements plus migration/model tests. Files: model registry, one migration, targeted tests. Exit: upgrade/downgrade on isolated DB and full suite. Risk low. 11B.3 join requests; 11B.4 locked approval; 11B.5 PostgreSQL concurrency verification.

## Blocking questions
Whether repeat requests after withdrawal are allowed; whether positions are free text or sport vocabulary; whether legacy Match dates can be removed later. None blocks 11B.2.

## 11B.2 Implementation Status
Implemented `MatchPositionRequirement` (`match_position_requirements`) with a `RESTRICT` match FK, unique `(match_id, position_code)`, positive `required_count`, and trimmed non-empty position-code checks. The Match relationship is metadata-registered. Migration `f1b2c3d4e5f6` follows `d4b7e1c9a2f6`; migration execution was deliberately deferred because no isolated migration database was confirmed. SQLite-focused tests plus full regression passed: **155 passed, 16 warnings**. PostgreSQL validation remains required for migration execution and PostgreSQL-specific constraint behaviour.

## 11B.3 — Match Join Request Persistence
Status: **complete**.

`MatchJoinRequest` persists to `match_join_requests`. Fields are `id`, `match_id`, `user_id`, string-backed `status`, nullable `requested_position_code`, nullable `reviewed_by_user_id`, nullable `reviewed_at`, `created_at`, and `updated_at`. Stored statuses are `pending`, `approved`, `rejected`, `withdrawn`, and `expired`. `Match.join_requests` links requests to their match; each request exposes its match, requester, and optional reviewer. `MatchParticipant` remains the confirmed roster.

Foreign-key deletion policy is `RESTRICT` for match and requester, and `SET NULL` for reviewer. Requested positions are nullable; supplied values must be trimmed and non-empty. Lookup indexes cover match, requester, status, reviewer, `(match_id, status)`, and `(user_id, status)`. Partial unique index `uq_match_join_requests_pending_match_user` permits only one pending request per match/user while retaining non-pending history.

Migration `b8c9d0e1f2a3` follows parent `f1b2c3d4e5f6` and is the sole Alembic head. Static validation confirmed model/migration column types and nullability, status and position checks, FK targets and deletion policies, index metadata, pending-only predicate, and downgrade ordering. Migration upgrade/downgrade was not executed because no positively confirmed disposable database was used.

Validation results: model tests **14 passed, 1 skipped**; join-request service tests **31 passed**; related match and position-requirement tests **23 passed**; full backend regression **222 passed, 1 skipped, 21 warnings**. SQLite covers persistence, checks, relationships, and its partial-index behavior; shared-fixture FK enforcement remains disabled, so one FK-deletion test is skipped. PostgreSQL partial-index behavior, migration execution, and concurrency validation remain pending.

Existing join APIs and services remain the active implementation. This persistence closure changes no API, service, dependency, or frontend code.
