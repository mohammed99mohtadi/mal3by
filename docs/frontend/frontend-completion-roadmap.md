# Frontend completion roadmap

Rules for every sprint: no API contract changes, no fake data, no unsupported controls. Add frontend proxies only for existing endpoints. Each screenshot set must include Arabic/English and desktop/mobile at minimum; tablet where layout changes.

## F1 Design System

- Pages: all existing localized routes as migration consumers.
- Components: `ui/*`, new shared PageHeader, AsyncState/ErrorState, form composition, confirmation dialog, bidi utility; retire legacy CSS consumers.
- Backend dependencies: none.
- Visual deliverables: type/spacing/state/controls reference page or test fixture; token contrast report.
- Tests: primitive interaction, axe, focus, RTL, reduced motion, visual snapshots.
- Exit: one canonical pattern per control/state; AA contrast; no legacy component bypass in touched routes.
- Blockers: approved brand assets not required; defer imagery.
- Screenshots: controls/states in ar/en at 375, 768, 1440.

## F2 Navigation and Layout

- Pages: layout, landing, global loading/error/not-found/unauthorized surfaces.
- Components: Header, HeaderNav, BottomNavigation, BottomNavItems, BrandLogo, LocaleSwitcher, home sections, footer, skip link.
- Backend dependencies: session cookie; `GET /courts`.
- Visual deliverables: role-aware desktop/mobile nav; stable footer; complete route states.
- Tests: active destinations, locale preservation including query, logout locale, keyboard order, landmark/axe, home API failure/retry.
- Exit: no duplicated nav model; 320–1440 no overflow; global localized state coverage.
- Blockers: owner/match destinations enabled only as their routes land.
- Screenshots: home/nav logged-out and player/owner logged-in, ar/en, 375/768/1440; offline/error/not-found.

## F3 Authentication UI V2

- Pages: login, register, profile.
- Components: AuthForm, PasswordField, form error summary, profile surface.
- Backend dependencies: existing register/login/me only. Password reset and profile editing remain blocked.
- Visual deliverables: fully localized auth/profile, reciprocal links, clear pending/error/session-expired states.
- Tests: network failure, 401/422, safe return path, autocomplete, error focus, keyboard, RTL, route guards.
- Exit: zero English hardcoding in Arabic; no raw unsafe backend error; auth completes keyboard-only.
- Blockers: reset/edit endpoints absent.
- Screenshots: login/register/profile ar/en desktop/mobile; validation/server/network/session-expired.

## F4 Booking Experience

- Pages: courts list/detail, booking new/confirm/success/list/detail.
- Components: Availability, BookingForm, BookingConfirm, court/booking cards, review summary placeholder only when real response loaded, cancellation dialog.
- Backend dependencies: courts, available slots, price quote, booking hold/detail/me/hold-status/confirm/cancel/cancel-hold. Add allowlisted frontend proxies.
- Visual deliverables: court decision data, responsive slot picker, hold countdown/expiry recovery, booking grouping, supported cancel flow.
- Tests: route states and status matrix, concurrent slot loss, hold expiry, cancel confirm/failure, 401/403/404, RTL dates/currency, 320px overflow, axe.
- Exit: every booking lifecycle state has correct action/state; no generic not-found masking; retry works; backend remains pricing authority.
- Blockers: none for listed work; court image may be absent and must use neutral non-fake fallback.
- Screenshots: courts list/detail; slots loading/empty/error/selected; new/confirm/expired/success; booking list/detail/cancel, ar/en, 375/768/1440.

## F5 Community UI

- Pages: matches index/new/me/join/detail; court reviews section; new review; own reviews; edit review.
- Components: MatchExperience split into detail/action/request list; match cards/forms; ReviewList/Summary/Form/OwnerResponse.
- Backend dependencies: all existing match endpoints; court reviews/summary; review CRUD/response endpoints. Frontend proxies required.
- Visual deliverables: discover/create/join/manage matches; verified review presentation and allowed review actions only.
- Tests: filters, create validation, join policies, invite code, participant/request state matrix, review eligibility/API errors, keyboard/axe/RTL/responsive.
- Exit: all player/community endpoints have reachable UI; hidden request-load errors become recoverable; no unsupported social actions.
- Blockers: owner review response belongs here or F6; endpoint already exists.
- Screenshots: match discovery/create/mine/code/detail states; organizer requests; review summary/list/form/response, ar/en desktop/mobile.

## F6 Owner UI

- Pages: owner dashboard; owner courts/list/new/detail; availability; pricing; owner bookings/list/detail.
- Components: OwnerShell, dashboard cards, CourtForm, WorkingHoursEditor, AvailabilityRulesForm, ClosuresList, PricingRules/Overrides, OwnerBookingTable/Card.
- Backend dependencies: existing `/owner/*`, `/sports`, and price-quote endpoints; strict role errors; frontend proxies required.
- Visual deliverables: owner navigation and real operational CRUD; safe confirmations; mobile card alternative for tables.
- Tests: role guard, CRUD success/error/conflict, status transition options from backend, money/date validation, keyboard dialog, RTL, overflow, axe.
- Exit: every owner endpoint maps to reachable UI or documented non-UI maintenance operation; destructive actions confirmed; 403 distinct from 401.
- Blockers: dashboard response schema must be consumed as-is; no invented metrics.
- Screenshots: dashboard, courts, edit/new, hours/closures, pricing, bookings/detail/dialogs, ar/en at 375/768/1440.

## F7 Arabic, Mobile and Accessibility

- Pages/components: every delivered F1–F6 screen.
- Backend dependencies: none.
- Visual deliverables: bidi-safe Arabic, tablet/mobile layouts, 200% zoom, focus and error behavior.
- Tests: typed copy parity, no hardcoded user-facing English, Playwright viewport matrix, axe, keyboard journeys, reduced motion.
- Exit: no horizontal page overflow at 320px; complete ar/en; WCAG 2.2 AA target; critical flows keyboard-only.
- Blockers: manual Arabic copy review by fluent reviewer.
- Screenshots: route matrix ar/en at 320/375/768/1024/1440, long-content stress cases.

## F8 Tests and Performance

- Pages/components: every route; focus on server pages and proxies currently untested.
- Backend dependencies: stable local test API or contract fixtures derived from schemas, never product fake data.
- Visual deliverables: loading stability and performance evidence, not redesign.
- Tests: route integration/E2E for auth, booking, match, review, owner; proxy allowlists; axe; visual regressions; bundle and Web Vitals checks.
- Exit: critical E2E green in ar/en/mobile; no untested mutation proxy; agreed LCP/CLS/INP budgets pass.
- Blockers: deterministic test environment and seeded test-only backend fixtures.
- Screenshots: regression baselines plus slow-network loading states.

## F9 Production Review

- Pages: all routes, metadata, favicon, robots/manifest/social previews if product-approved.
- Components: final asset and copy cleanup.
- Backend dependencies: production API base/CORS/auth-cookie deployment configuration.
- Visual deliverables: final approval gallery; production asset inventory.
- Tests: clean install, test/lint/typecheck/build, E2E smoke against staging, broken-link and console-error scan, `git diff --check`.
- Exit: no placeholder framework assets, fake data, dead route, unsupported action, untranslated copy, console error, or critical accessibility issue; user signs off screenshots.
- Blockers: approved branding/assets, staging configuration, fluent Arabic and product review.
- Screenshots: signed-off gallery for every route and major state, ar/en desktop/mobile.

## Recommended first implementation sprint

Start F1. Auth, booking, community, and owner work would otherwise repeat form, async-state, dialog, bidi, and responsive patterns. Keep F1 bounded: tokens, shared states/forms/dialog/bidi, tests, and migration proof on one low-risk route; do not redesign business flows yet.
