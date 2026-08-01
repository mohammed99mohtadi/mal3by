# Design-system gap analysis

## Current foundation

`globals.css` defines dark surfaces, semantic colors, radii, shadows, motion, page width, safe-area bottom padding, focus ring, and reduced-motion handling. Shared primitives exist for Button, Input, Select, Textarea, Checkbox, Radio, Alert, EmptyState, FieldError/Label/Hint, ProgressBar, Skeleton, Spinner, StatusBadge, and Surface. Cairo/Poppins load through `next/font`. `html` correctly sets localized `lang` and `dir`.

## Gaps

| Area | Evidence | Risk | F1 deliverable |
|---|---|---|---|
| Token duplication | New tokens coexist with backward aliases and legacy `.surface`, `.brand-button`, `.muted`, `.status-*` | Drift and inconsistent states | Deprecation map; migrate consumers to primitives/tokens |
| Component bypass | `auth-form`, profile, layout footer, links, and not-found pages hand-roll fields/buttons/cards | Focus, disabled, size, and spacing diverge | Form/Card/Link patterns using existing primitives |
| Typography | No named display/heading/body scale; arbitrary Tailwind sizes/weights | Inconsistent hierarchy, Arabic metrics | Bilingual type scale and line-height tokens |
| Spacing/layout | Page-specific arbitrary gaps; one `page-wrap` only | Harder tablet consistency | Container, section, stack, cluster patterns |
| State patterns | No shared PageHeader, PageSkeleton, ErrorState/Retry, Unauthorized, NotFound | Routes collapse distinct failures | Standard localized state components |
| Forms | No form group/error summary/password field/date-time field | Auth and owner forms likely duplicate | Accessible form composition; error focus contract |
| Feedback | No toast/dialog/confirmation pattern | Cancel/delete workflows unsafe | Accessible dialog plus inline mutation status |
| Navigation | Desktop and mobile define active logic separately | Route drift; matches/owner absent | Shared nav model and role-aware destinations |
| Directionality | No `dir="ltr"`/`bdi` utility for email, IDs, currency, date/time | RTL punctuation/order defects | Bidi isolation utility and tests |
| Icons/assets | Inline SVGs repeated; brand is letter tile; public contains Next defaults only | Weak production identity; icon consistency | Small internal icon set; approved logo/empty artwork only if supplied |
| Color/contrast | Token values look plausible but no automated WCAG evidence | Muted text/status contrast unknown | Contrast audit; AA token adjustments |
| Motion | Reduced motion exists; no consistent loading/transition spec | Uneven perceived performance | Motion/loading guidance |
| Responsive | Breakpoints and grids are page-local | Tablet and 320px regressions | 320/375/768/1024/1440 matrix |
| Content | `copy.ts` is monolithic; route files contain English | Translation omissions and copy drift | Typed namespaces or equivalent completeness test |

## State contract

Every data route must implement: initial loading/skeleton, success, empty where meaningful, typed 401/403/404, recoverable error with retry, mutation pending/success/error, and stale/conflict recovery. Never convert every backend error into “not found.” Keep backend messages out of user copy unless explicitly safe and localized.

## Accessibility contract

- One visible `h1`; landmarks and skip link.
- 44px pointer targets; full keyboard completion; visible focus.
- Inputs with programmatic labels, autocomplete/input mode, descriptions, inline error, error-summary focus.
- Async state announced without duplicate speech; destructive operations use named confirmation dialog and restore focus.
- `<time dateTime>` for dates; `bdi` or LTR isolation for IDs, email, phone, codes, currency/time ranges.
- Automated axe checks plus manual keyboard, screen-reader smoke, 200% zoom, reduced-motion and contrast review.

## Production assets

Current `public/` contains only unused framework placeholders: `file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, `window.svg`. Favicon exists, but no verified app logo, court imagery fallback, manifest, social image, or metadata image. F9 must remove unused placeholders and add only approved assets; never fabricate venue photos.
