# Account Lifecycle

## Current lifecycle

| Capability | Status | Evidence / behavior |
|---|---|---|
| Register | implemented | creates active player; returns user; no session |
| Login | implemented | JWT containing `sub`, `email`, `exp`; inactive checked only on subsequent authenticated request |
| Logout | partial | frontend deletes cookie; token remains valid until expiry |
| `/users/me` | implemented | active-user dependency; returns private account fields |
| Inactive account | partial | `is_active=false` blocks protected APIs with 400; no admin operation/UI or reason/history |
| Suspended account | missing | no distinct state/reason/timestamps |
| Deleted/closed account | missing | no endpoint; FK cascades/restricts conflict |
| Password change/reset | missing | no endpoint/token/session invalidation |
| Email verification | missing | account active immediately |
| Email change | missing | no pending/verification workflow |
| Role change | partial | admin can directly replace single role; no audit/application |
| Owner approval | missing | no application or decision |

## Current sequence

1. Frontend registration sends `full_name`, `email`, optional `phone_number`, and password.
2. Backend ignores extra fields, checks duplicate email/phone, hashes password, and commits an active player.
3. Frontend redirects to login; there is no automatic session.
4. Login creates a seven-day JWT; Next route stores it in an HTTP-only, SameSite=Lax cookie, Secure in production.
5. Server components call `/users/me`; navbar/profile use returned role/account fields.
6. `get_current_user` re-reads User each request and blocks inactive rows, so status changes take effect despite stateless JWT.

## Recommended MVP states

- `active`: normal access according to role.
- `suspended`: authentication/session use denied; preserve all history; store administrative reason separately/audit it.
- `closed`: login denied and personal data minimized according to retention policy; historical records preserved.
- `pending_verification`: defer until email verification is implemented; do not add a dormant state without behavior.

Do not use `deleted` as a hard-delete transition. Do not overload owner application state onto account status.

## Target lifecycle

`register → active player → optional owner application pending → approved owner OR rejected/withdrawn player`.

Any active account may become suspended and later reactivated. Closure requires a dedicated retention/anonymization design. Role and state transitions must be service-owned, transactional, authorized, and audited. Existing tokens must be rejected through the database status check; password/email changes should also invalidate sessions once a session/version mechanism exists.

## Unsupported transitions to reject

- Public registration directly to owner/admin.
- Player self-promotion.
- Owner approval without a pending application.
- Suspending/demoting the only active admin.
- Demoting an owner while owned courts or unresolved operational obligations lack a transfer policy.
- Hard-deleting a user and cascading bookings/courts.
