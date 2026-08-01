# F0 frontend completion audit

Audit date: 2026-08-01. Evidence read: all files under `frontend/src/app`, `components`, `lib`, `src/proxy.ts`, `public`, frontend tests/config; FastAPI router and endpoint declarations where needed. No runtime or backend edits made.

## Executive result

Frontend has sound bilingual layout primitives and working core booking/match-detail integrations, but is not feature-complete against current backend. Biggest omissions: all owner UI, match discovery/create/mine/code flows, review UI, booking cancellation/hold recovery, and consistent localized route states. Existing auth/profile screens are English-hardcoded. Only match detail has route skeleton. Public assets remain framework placeholders.

Classification across 34 route surfaces: Complete 1; Needs polish 7; Needs redesign 5; Missing but backend-supported 15; Blocked by missing backend 3; Deferred 3. Full row evidence: `route-inventory.md`.

## Baseline

| Command | Result |
|---|---|
| `npm run test:run` | PASS: 12 files, 68 tests |
| `npm run lint` | PASS |
| `npm run typecheck` | PASS |
| `npm run build` | PASS: Next.js 16.2.12; 20 app routes listed including 6 API handlers |
| `git diff --check` | PASS; line-ending warnings only on pre-existing modified files |
| `git status --short` | Pre-existing modifications in 6 backend/test files and 2 audit docs; four F0 docs added by this work |

PowerShell initially blocked `npm.ps1`; baseline used equivalent `npm.cmd run ...`. Commands themselves were unchanged.

## Area findings

1. **Global design system:** strong token/primitives start; legacy aliases and hand-built controls duplicate styles. Missing page-state, dialog, form-error, layout, bidi, and typography contracts.
2. **Navbar/mobile navigation:** responsive and active-state aware. Desktop/mobile models duplicate logic; no matches/owner entry; English aria labels; logout drops locale because form omits query.
3. **Landing:** real courts only; marketing content static and legitimate. Error/empty exist, retry/loading route absent. No production imagery required, but current framework SVGs add no value.
4. **Authentication:** login/register work. Screens and form copy are English-only, network exceptions are uncaught, raw backend detail can surface, register returns to login, reciprocal links/autocomplete/error focus absent.
5. **Profile:** real `/users/me`, but read-only because backend has no update. Any load error redirects to login. Owner role has no owner navigation.
6. **Courts:** list/detail use real API. Missing supported review/rating data and existing court fields such as image, price, capacity. Errors collapse to generic/not-found; no retry or skeleton.
7. **Availability:** real date/slots proxy, loading/error/retry/empty/select states and 44px targets. No min date, stale request cancellation, timezone explanation, skeleton, or deep keyboard/RTL tests.
8. **Booking flow:** real slot recheck, hold, confirmation. Backend remains price authority. Missing price quote, hold status/countdown, cancel-hold, expiry recovery, and status-gated confirmation.
9. **My Bookings:** real list/detail. Missing grouping/filtering, cancellation action despite endpoint/proxy support, retry, and route tests.
10. **Community matches:** match detail is mature and tested. All discovery/create/mine/join-code/management routes absent despite backend. Organizer request load failure is swallowed into false empty.
11. **Join requests:** detail supports create/withdraw/approve/reject. No global requested-match view despite `/matches/me/join-requests`.
12. **Owner pages:** entirely absent; backend has dashboard, courts, schedules, closures, pricing and bookings management.
13. **Reviews:** frontend API client defines reads but no UI calls them. Backend supports court list/summary, create, own list, edit/delete, and owner response.
14. **Error/loading routes:** only match detail loading. Two English hardcoded not-found files; pages do not call `notFound()`. No localized global error/not-found/loading/unauthorized boundaries.
15. **Arabic/English:** root/layout direction works; copy object covers booking/match/home/courts. Auth/profile/footer/brand aria/not-found/navigation aria/API fallback copy remain English. Dynamic dates, IDs, email, currency and ranges lack bidi isolation.
16. **Mobile/tablet:** bottom nav and responsive grids exist. No viewport tests; long content, action rows, tables-to-come, auth mobile hierarchy, safe keyboard viewport, and 320px overflow unverified.
17. **Accessibility:** visible focus, reduced motion, semantic primitives, match error focus are positives. Missing skip link, error summaries, async error announcements, `<time>`, bidi, autocomplete/input modes, automated axe and full keyboard journeys.
18. **Performance:** server fetches are mostly sensible, but court list is unpaginated, match detail makes serial conditional fetches, no request dedupe/abort in availability, many screens lack skeletons, and no image/metadata/bundle/Web Vitals budgets exist.
19. **Tests:** 68 unit/component tests pass. Gaps: every server page, API route handlers, proxy middleware, auth network exception/error focus, profile, courts routes, booking routes/states, all missing feature routes, E2E, axe, visual/RTL/viewport/performance.
20. **Production assets:** only favicon plus unused Next/Vercel placeholder SVGs. No approved logo/social/manifest/fallback assets. Do not invent court photos.

## Fake, hardcoded, unsupported audit

- No fake product records found.
- Hardcoded user copy exists heavily in auth/profile/layout/not-found and English aria labels.
- Static homepage “how/why” text is marketing copy, not fake data.
- Existing buttons map to real routes/endpoints. No unsupported business action found.
- One misleading state: success page can render any fetched booking status under success heading.

## Risk priorities

**P0:** build shared localized state/form/dialog/bidi patterns; stop error-status collapse; complete auth translation. **P1:** finish booking lifecycle and supported community routes. **P1:** deliver owner console because largest backend-supported omission. **P2:** full review management, production assets, performance/visual regression hardening.

## Required confirmation

- Runtime code changed: **No**.
- Backend code or API contract changed: **No**.
- Fake data added: **No**.
- Commit or push: **No**.
