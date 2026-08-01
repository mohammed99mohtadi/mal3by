# FM1 product route foundation

Source of truth: `src/lib/product-routes.ts`. Locale prefixes `/ar` and `/en` apply to every pattern below. Dynamic `:id` patterns require real IDs.

Registry total: **45** route patterns — **13 LIVE**, **12 PARTIAL**, **20 SHELL**, **0 DEFERRED**. Localized error, loading, and not-found boundaries support these routes but are not product destinations.

Classifications: **LIVE** uses current backend data; **PARTIAL** has real backend support but incomplete UI; **SHELL** is non-functional foundation with no API request or simulated activity; **DEFERRED** stays outside navigation.

| Route area | Routes | Classification | Backend dependency | Navigation | Next polish |
|---|---|---|---|---|---|
| Core | `/`, `/courts`, `/courts/:courtId`, `/bookings`, `/bookings/:bookingId`, `/login`, `/register`, `/profile` | LIVE | Courts, bookings, auth, users | Primary/secondary | Production review |
| Community | `/community`, `/matches`, `/matches/:matchId`, `/matches/new`, `/matches/me`, `/matches/requests` | LIVE/PARTIAL | Current match endpoints | Primary + community hub | Forms, filters, roster |
| Players/teams | `/players/:playerId`, `/teams`, `/teams/:teamId` | SHELL | Missing | Hub links only | Backend design |
| Tournaments | `/tournaments`, `/tournaments/:tournamentId` | SHELL | Missing | Not primary | Backend design |
| Reviews | `/reviews` | PARTIAL | Current review endpoints | Account surface | Review management |
| Owner | `/owner`, `/owner/courts`, `/owner/bookings`, `/owner/calendar`, `/owner/pricing`, `/owner/reviews` | PARTIAL | Current owner endpoints | Authorized dashboard | Owner operations |
| Owner analytics | `/owner/analytics` | SHELL | Missing analytics | Authorized dashboard | Analytics backend |
| Admin | `/admin`, `/admin/users`, `/admin/courts`, `/admin/bookings`, `/admin/matches`, `/admin/moderation` | SHELL | Partial admin backend | Authorized dashboard only | Admin contracts |
| Account | `/notifications`, `/settings`, `/settings/security` | SHELL | Missing | Secondary account menu | Backend support |
| Payments | `/payments`, `/payments/:paymentId` | SHELL | Missing verified payment history | Hidden | Payment integration |
| Support/legal | `/help`, `/privacy`, `/terms` | SHELL | None | Footer | Support channels/legal approval |

Shell guarantees: bilingual copy, no product fetch, no fake users/teams/rankings/metrics/payments, no mutation control, clear availability label. Unknown routes use localized not-found boundary.
