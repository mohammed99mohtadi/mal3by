# Target Identity Domain Model

## Design rules

- `User` is the source of truth for authentication, account state, and one canonical role.
- `Profile` is the source of truth for editable presentation/preferences and has a strict one-to-one relation with User.
- A user has exactly one effective role in MVP: player, owner, or admin. Remove `is_admin` after a compatibility migration; until then, reject inconsistent values and treat role as canonical.
- `OwnerApplication` records the request and decision. Owner role assignment may occur only through an approved application service or an explicitly audited admin emergency action.
- `AuditEvent` is append-only administrative evidence, not an application log.
- Do not create parallel identity/account models for each role.

## Proposed entities

### User (extend)

Keep: `id`, normalized unique `email`, `hashed_password`, canonical `role`, `created_at`.

Add incrementally: `status` (`active`, `suspended`, later `pending_verification`, `closed`), `updated_at`, `email_verified_at` nullable, `password_changed_at` nullable. During migration, map `is_active=false` to `suspended` only after confirming existing data semantics. Do not add deletion until retention behavior exists.

Deprecate: `is_admin`. Keep a temporary read compatibility field only while callers migrate.

### Profile

| Field | MVP | Notes |
|---|---:|---|
| `user_id` PK/FK | yes | one-to-one; unique; use RESTRICT for accidental user deletion |
| `display_name` | yes | initialized from `full_name`; 2–100 chars |
| `phone_number` | yes | migrate from User; private; normalized unique if business-required |
| `avatar_url` | optional | managed URL/reference; validate scheme/host policy |
| `country_code` | optional | ISO code |
| `city` / `area` | optional | bounded text |
| `preferred_locale` | yes | `ar` or `en`; default chosen explicitly |
| `bio` | optional | bounded plain text |
| `skill_level` | optional | controlled enum if globally meaningful |
| `profile_visibility` | later/MVP if public profiles ship | `private`/`members`/`public` |
| `date_of_birth` | no | defer until a demonstrated age/legal requirement |

Preferred sports should use a `profile_preferred_sports(profile_id,sport_id)` association with a unique composite key. Player positions should be sport-aware, not one global string.

### OwnerApplication

Fields: `id`, `user_id`, `status` (`pending`,`approved`,`rejected`,`withdrawn`), bounded business/contact/application details, `submitted_at`, `reviewed_at`, `reviewed_by_user_id`, `decision_reason`, `created_at`, `updated_at`. Enforce at most one pending application per user. Reviewer uses `SET NULL` to preserve history; applicant uses `RESTRICT`. Approval transaction locks application/user, changes status and role, and writes AuditEvent atomically. Suspension is an account/owner authorization concern, not application status.

### AuditEvent

Fields: `id`, `actor_user_id` nullable for system, `subject_user_id` nullable, `event_type`, `occurred_at`, `request_id`, `reason`, and a JSON metadata allowlist containing identifiers and before/after non-secret state. Use `SET NULL` FKs or durable subject identifiers so history survives closure. Never store passwords, tokens, full request bodies, or unnecessary IP data. Append-only service; admin read access only.

## Relationships and retention

| Relation today | FK policy | Finding / target |
|---|---|---|
| User → courts | court owner `CASCADE`; ORM delete-orphan | dangerous; use RESTRICT or ownership transfer/closed-owner retention |
| User → bookings | booking user `CASCADE`; ORM delete-orphan | P0 retention risk; use RESTRICT/anonymized closed user |
| User → created matches | `RESTRICT` | preserves history; retain |
| User → participants/join requests | `RESTRICT`; reviewer SET NULL | broadly appropriate; add missing backrefs only if useful |
| User → reviews | reviewer/moderator `RESTRICT` | preserves provenance; moderator may eventually use SET NULL depending closure policy |
| User → pricing/closures creator | `SET NULL` | appropriate historical record |
| Profile | absent | add one-to-one, preferably RESTRICT |
| Notifications | absent | future recipient relation; retention/purge policy required |
| OwnerApplication | absent | applicant RESTRICT; reviewer SET NULL |
| AuditEvent | absent | actor/subject SET NULL plus durable IDs |

Current indexed identity-adjacent FKs are generally good. User list needs indexes for `(role,status,created_at)` and normalized email search. ORM loading should be explicit for admin detail; avoid loading every booking/match/review in list endpoints. Use paginated counts or separate detail tabs to prevent N+1 and oversized responses.

## Schemas and API boundaries

- `PublicProfileResponse`: public ID, display name, avatar, selected sports/position/skill only when visibility permits. Never email, phone, status, moderation, or booking history.
- `PrivateProfileResponse/Update`: current user's account-safe fields and editable profile fields.
- `AdminUserSummary/Detail`: email, phone where operationally justified, canonical role/status, timestamps; related activity via paginated endpoints.
- `AuthUserResponse`: minimal post-auth identity needed by navigation; avoid duplicating full admin/private schemas.
- `OwnerApplicationCreate/OwnResponse/AdminResponse/Decision`: separate accepted/returned fields.
- `AuditEventResponse`: admin-only, redacted metadata.

Future verification should add a single-use hashed token table with purpose and expiry; never store raw tokens. Email changes should remain pending until verified and should invalidate/reconcile sessions by policy.
