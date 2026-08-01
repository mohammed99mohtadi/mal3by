# Frontend route inventory

Audit date: 2026-08-01. Scope: current Next.js app, frontend route handlers, components, copy, tests, assets, and current FastAPI routes. “Backend support” means endpoint exists now; frontend proxy support may still be missing. Localized routes represent both `/ar` and `/en`.

## Counts

34 route surfaces audited: 1 Complete, 7 Needs polish, 5 Needs redesign, 15 Missing but backend-supported, 3 Blocked by missing backend, and 3 Deferred. Root redirect is counted as Complete. API handlers are integration infrastructure, not product screens.

## Inventory

| Route | Purpose | Status | Backend support | UI completeness | UX problems | Mobile problems | RTL problems | Accessibility problems | Test coverage | Sprint |
|---|---|---|---|---|---|---|---|---|---|---|
| `/` | Default-locale entry | Complete | N/A | Redirects to `/ar` | Locale preference not remembered | None material | None | Redirect only | Redirect unit test | F9 |
| `/[locale]` | Landing/discovery | Needs polish | `GET /courts` | Real featured courts; all major sections | No retry; generic production copy/assets | Hero density; no device visual tests | Eyebrow letter-spacing and mixed brand direction need review | No skip link; landmark/footer copy weak | Section units only; no route/error test | F2, F7 |
| `/[locale]/login` | Session login | Needs redesign | `POST /auth/login` | Works through secure cookie proxy | No register link; raw backend errors; no network catch; English-only | Brand panel disappears; form spacing/basic | Entire screen/form English | Labels wrap fields awkwardly; focus after error absent; autocomplete absent | Component happy/error basics | F3 |
| `/[locale]/register` | Account creation | Needs redesign | `POST /auth/register` | Core fields work | No login link; no terms/help; raw errors; register does not establish session | Same as login | Entire screen/form English | Missing autocomplete/input modes; focus/error summary | Component basics only | F3 |
| `/[locale]/profile` | Account identity/session | Needs redesign | `GET /users/me` | Read-only identity | Any API failure treated as auth failure; `-` placeholder; owner entry absent | Card usable, action hierarchy weak | All labels/actions English | Logo contrast/context; no page error/retry | None | F3, F6 |
| `/[locale]/courts` | Browse courts | Needs polish | `GET /courts` | Real list/empty/error | No filters, images, price, rating, retry, pagination | Cards okay; long names/areas untested | Long Arabic and mixed values untested | Error not announced; no loading route | No route test | F4 |
| `/[locale]/courts/[courtId]` | Court details, availability, reviews | Needs redesign | `GET /courts/{id}`, slots, reviews, rating summary | Details + slots; reviews/rating/image/price/capacity absent | All fetch errors shown as not found; no retry; incomplete decision info | Sticky converts safely, but slot grid narrow | Address/time/number bidi unhandled | No semantic error distinction; date constraints unclear | Availability component only | F4, F5 |
| `/[locale]/bookings` | User booking history | Needs polish | `GET /bookings/me` | Real list/empty/error | No status/date grouping, cancel entry, retry | Two-column cards collapse; long content untested | Date/currency/IDs lack bidi isolation | Error not live; timestamps lack `<time>` | No route test | F4 |
| `/[locale]/bookings/new` | Validate slot and create hold | Needs polish | court detail, slots, `POST /bookings/hold` | Real revalidation + hold | No loading route; court errors collapsed; price quote unused | Compact and usable; query/date overflow untested | Dates/numbers mixed direction | Error focus absent; progress is prose | Booking form unit tests | F4 |
| `/[locale]/bookings/[bookingId]` | Booking detail/actions | Needs redesign | `GET`, `POST /cancel`, hold status/cancel-hold | Read-only detail | Supported cancellation missing; no retry; all failures “not found” | Definition grid okay; action area absent | Time range/currency bidi | Missing `<time>`; no confirm dialog/focus flow | No route test | F4 |
| `/[locale]/bookings/[bookingId]/confirm` | Confirm held booking | Needs polish | `POST /confirm-payment` | Real confirmation | No live hold countdown/expiry recovery; action visible for invalid states | Basic card usable | Time/currency bidi | Failure focus absent; no expiry announcement | Component tests | F4 |
| `/[locale]/bookings/[bookingId]/success` | Booking outcome | Needs polish | `GET /bookings/{id}` | Real status/details | “Success” can display non-success state; no receipt semantics | Three actions can crowd | Mixed IDs/dates | No status announcement or autofocus | No route test | F4 |
| `/[locale]/matches/[matchId]` | Match details, join/leave, request review | Needs polish | Detail/join/leave/join requests | Strongest state coverage; real mutations | Back points to courts, no match hub; request-list load failure hidden as empty | Action rows can crowd; long titles untested | Dynamic title/sport and numeric phrases need bidi checks | Good focus-on-action-error; SVGs elsewhere lack titles but hidden context adequate | Broad component tests | F5 |
| `/[locale]/matches` | Discover public matches | Missing but backend-supported | `GET /matches` filters | Missing | No discovery entry point | Missing | Missing | Missing | None | F5 |
| `/[locale]/matches/new` | Create match | Missing but backend-supported | `POST /matches` | Missing | Must use real booking/court fields only | Missing | Missing | Missing | None | F5 |
| `/[locale]/matches/me` | Created/joined/requested matches | Missing but backend-supported | `GET /matches/me/created`, `/joined`, `/join-requests` | Missing | No management hub | Missing | Missing | Missing | None | F5 |
| `/[locale]/matches/join` | Join private match by code | Missing but backend-supported | `POST /matches/join-by-code` | Missing | No invite-code entry | Missing | Missing | Missing | None | F5 |
| `/[locale]/owner` | Owner dashboard | Missing but backend-supported | `GET /owner/dashboard` | Missing | Owner role has no landing page | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/courts` | Owner court list | Missing but backend-supported | `GET /owner/courts`, toggle/delete | Missing | No owner inventory management | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/courts/new` | Create court | Missing but backend-supported | `POST /owner/courts` | Missing | Must use real sports endpoint/options | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/courts/[courtId]` | Edit/toggle court | Missing but backend-supported | owner court GET/PATCH/toggle/delete | Missing | Destructive flows need confirmation | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/courts/[courtId]/availability` | Working hours, rules, closures | Missing but backend-supported | Owner working-hours/rules/closures CRUD | Missing | Complex schedule editor absent | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/courts/[courtId]/pricing` | Pricing rules/overrides | Missing but backend-supported | Owner pricing CRUD; price quote | Missing | Complex money/date editor absent | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/bookings` | Owner booking queue | Missing but backend-supported | Per-court booking list | Missing | Needs court selector because endpoint is court-scoped | Missing | Missing | Missing | None | F6 |
| `/[locale]/owner/courts/[courtId]/bookings/[bookingId]` | Owner booking decision | Missing but backend-supported | GET/PATCH status | Missing | Role/status transitions must mirror backend | Missing | Missing | Missing | None | F6 |
| `/[locale]/courts/[courtId]/reviews/new` | Submit verified review | Missing but backend-supported | `POST /reviews` | Missing | Eligibility/error rules must come from API | Missing | Missing | Missing | None | F5 |
| `/[locale]/reviews` | Manage own reviews | Missing but backend-supported | `GET /reviews/me`, DELETE | Missing | No review history | Missing | Missing | Missing | None | F5 |
| `/[locale]/reviews/[reviewId]/edit` | Edit own review | Missing but backend-supported | GET/PATCH review | Missing | No edit flow | Missing | Missing | Missing | None | F5 |
| `/[locale]/forgot-password` | Request password reset | Blocked by missing backend | None | Missing | Cannot safely invent workflow | Missing | Missing | Missing | None | Blocked |
| `/[locale]/reset-password` | Complete password reset | Blocked by missing backend | None | Missing | Cannot safely invent workflow | Missing | Missing | Missing | None | Blocked |
| `/[locale]/profile/edit` | Edit profile | Blocked by missing backend | Only `GET /users/me` | Missing | No update endpoint | Missing | Missing | Missing | None | Blocked |
| `/[locale]/admin/users` | Role administration | Deferred | `PATCH /admin/users/{id}/role`; no user-list endpoint | Partial backend only | Listing blocked; internal/admin scope | N/A | N/A | N/A | None | Deferred |
| `/[locale]/admin/reviews` | Review moderation | Deferred | Admin moderation endpoints | No product requirement/navigation | Internal/admin scope | N/A | N/A | N/A | None | Deferred |
| `/[locale]/admin/sports` | Sport catalog admin | Deferred | Sports create/list/detail | No product requirement/navigation | Internal/admin scope | N/A | N/A | N/A | None | Deferred |

## Cross-route state finding

Only match detail owns `loading.tsx`. No localized global `loading.tsx`, `error.tsx`, or `not-found.tsx`. Court and booking not-found files contain English-only hardcoded copy and are not reached because pages catch all errors. Unauthorized behavior varies: redirect on booking/profile, inline state on match. No route has an explicit retry boundary. Existing screens use no fake records; homepage explanatory copy is static marketing content, not data. Default Next/Vercel SVG assets are unused placeholder production assets.
