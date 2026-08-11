# MAL3ABY skill usage

## Selection policy

Do not use every skill for every prompt. Select the skills that materially govern the work and read each selected `SKILL.md` before acting. Use at least four relevant skills for substantial MAL3ABY implementation prompts. Do not claim a skill was used unless its instructions were read and applied.

Typical UI batch:

- `mal3aby-design-system`
- `mal3aby-mobile-ux`
- `mal3aby-frontend`
- `mal3aby-accessibility`
- `web-design-guidelines`
- `vercel-react-best-practices`
- Add `playwright`, `mal3aby-testing`, and `test-driven-development` when implementing and verifying behavior.

Typical booking task:

- `mal3aby-booking`
- `mal3aby-backend`
- `mal3aby-database`
- `mal3aby-testing`
- Add `security-best-practices` for explicit security work and `systematic-debugging` when a defect or unexpected failure appears.

## Design-first workflow

For UI work, follow:

`DESIGN -> USER APPROVAL -> IMPLEMENTATION PROMPT -> IMPLEMENTATION -> TESTS -> VISUAL COMPARISON -> REVIEW -> COMMIT`

Inspect the approved reference image before implementation. Treat it as visual truth while current backend contracts and business/security behavior remain authoritative. Do not implement against a missing or unapproved reference when the task requires one.

## Five-prompt review

After every five implementation prompts, stop feature development and review:

- architecture, code quality, and duplication
- frontend consistency and design-system use
- mobile UX, RTL/LTR, and accessibility
- backend layering, database integrity, and API contracts
- security, performance, tests, and production build
- technical debt introduced or exposed

Fix meaningful regressions before continuing. Record review scope, evidence, fixes, deferred debt, and verification results.

## Ownership boundaries

- Visual identity and primitives: `mal3aby-design-system`
- Responsive/device behavior: `mal3aby-mobile-ux`
- Next.js integration: `mal3aby-frontend`
- Bilingual inclusive interaction: `mal3aby-accessibility`
- FastAPI layers and API behavior: `mal3aby-backend`
- Persistence and migrations: `mal3aby-database`
- Availability, pricing, holds, lifecycle, and overlap: `mal3aby-booking`
- Test matrix and Definition of Done: `mal3aby-testing`

Keep cross-cutting workflow here instead of copying it into every skill.
