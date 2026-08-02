# Identity Privacy Classification

This classification defines target exposure; it does not claim current public-profile APIs exist.

## Public profile

Safe only when visibility permits: opaque/public user identifier, display name, approved avatar, selected preferred sports, sport-specific position, broad skill level, and optional bounded bio/city. Do not expose contact data or account/moderation state. Current match/review schemas already expose internal numeric user IDs and full names; reassess before public player profiles.

## Private account

User and authorized administrators only: email, phone, preferred locale, full profile preferences, account timestamps/status, booking history, match/join-request history, reviews, and verification state. Related histories need paginated, purpose-specific endpoints rather than embedding in `/users/me`.

## Sensitive — never returned

Password/hash, raw JWT/refresh/reset/verification tokens, signing secrets, credential metadata, unrestricted IP addresses, internal security decisions, and raw audit metadata. Current `hashed_password` is correctly excluded. The JWT is necessarily returned by backend login to the trusted frontend proxy but must never appear in user/profile JSON or logs.

## Administrative

Role/status, suspension/decision reasons, owner applications, moderation history, audit events, and limited login/security metadata. Admin access must be backend-enforced, purpose-limited, auditable, and redacted. Avoid exposing password hash even to admins.

## Current exposure findings

- `UserResponse` combines registration, `/users/me`, and admin role-change output. It includes email, phone, internal ID, role, active/admin flags, and created time. This is acceptable for self/admin operations but unsuitable as a public profile schema.
- `is_admin` exposes redundant internal authorization state and should be removed with compatibility planning.
- JWT includes email although authorization only needs `sub`; remove email in a future token-version change.
- Duplicate email/phone registration messages disclose account existence.
- Owner booking responses may include joined User data through `BookingRead`; keep owner-visible fields to operational minimum.
- Audit events must not record full payloads, tokens, password material, or unnecessary IP/user-agent data.

## Retention principles

- Preserve transactional bookings, match participation, reviews, moderation, owner decisions, and audit evidence for defined legal/operational periods.
- Close/anonymize accounts instead of cascading historical records.
- Store explicit retention periods in policy/configuration; apply deletion jobs only after legal review.
- If IP addresses become necessary for security, truncate/hash where useful, restrict access, and use short retention.
