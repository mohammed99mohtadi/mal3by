# Identity Permissions Matrix

Backend enforcement is authoritative. Frontend checks only hide navigation or render friendly denial.

| Action / route | Player | Owner | Admin | Current enforcement | Gap |
|---|---:|---:|---:|---|---|
| Register/login, browse courts | yes | yes | yes | public/auth service | no rate limiting or verification |
| `GET /users/me` | self | self | self | JWT + active-user check | read-only; broad account schema |
| Edit own profile | no | no | no | absent | unused `UserUpdate` schema |
| Create/list own bookings | yes | yes | yes | authenticated + object checks | role-independent by design |
| Create/join/manage own matches | yes | yes | yes | creator/participant checks | role-independent by design |
| Create/edit own verified review | yes | yes | yes | booking/reviewer checks | public/private schema split needed |
| Create owner application | no | no | no | absent | required player → owner entry |
| Manage courts/availability/pricing/bookings | no | own only | all | `require_owner` + court ownership | core checks good; admin logic duplicated |
| Respond to owned-court reviews | no | own only | override | service ownership checks | frontend partial |
| Review owner applications | no | no | no | absent | required |
| Change user role | no | no | yes | `require_admin`; last-admin guard | known ID only; no application/audit |
| List/search/filter/view users | no | no | no | absent | admin API/UI required |
| Suspend/reactivate user | no | no | no | absent | raw `is_active` only |
| Moderate reviews | no | no | yes | backend admin check | frontend shell |
| View audit history | no | no | no | absent | required |

## Current backend permissions

- Player/account: `/users/me`; self-scoped `/bookings/*`; match actions controlled by creator, participant, join policy, and status; review actions controlled by completed booking/reviewer.
- Owner: all player actions plus `/owner/dashboard`, owned-court CRUD/activation, working hours, availability rules, closures, pricing, court bookings/status, and owner review responses.
- Admin: player actions; owner endpoints with global override; `/admin/users/{id}/role`; review moderation; existing sport administration.

Backend role and object checks are real and tested. Cross-owner access is denied. Admin override is intentional. Missing capabilities are not safely emulated by frontend.

## Authorization weaknesses

`role=admin` and `is_admin=true` are parallel authority sources. Dependencies, owner helpers, frontend catch-all routing, and user menu repeatedly implement `role OR is_admin`. This permits inconsistent records and expands the review surface. Make `role` canonical, centralize checks, migrate callers, then remove `is_admin`.

Frontend route guards are server-rendered convenience only. The locale proxy does no authentication. Every new privileged API must use backend dependencies plus object-level checks.

## Target transitions

| From | To | Rule |
|---|---|---|
| none | player | public registration only |
| player | owner | admin approval of a pending OwnerApplication; atomic audit |
| owner | player | admin only after owned-court/obligation policy; audited |
| active | suspended | admin with reason; audited; all existing tokens denied by DB status check |
| suspended | active prior role | admin with reason; audited |
| player/owner | admin | tightly controlled admin action; audited |
| admin | non-admin | another active admin must remain; audited |

One user has one role today and should keep one canonical role for MVP. Do not model multi-role behavior through the legacy boolean.
