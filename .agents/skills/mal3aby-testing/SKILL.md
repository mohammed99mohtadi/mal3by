---
name: mal3aby-testing
description: Plan and execute MAL3ABY verification across Vitest, Testing Library, Playwright, pytest, PostgreSQL concurrency, lint, type checking, builds, responsive visuals, and accessibility. Use for implementation test plans, regressions, quality gates, or completion reviews.
---

# MAL3ABY Testing

- Use TDD for features/fixes: write one behavior test, observe the expected failure, implement minimally, verify green, then refactor.
- Use systematic debugging for unexpected failures: reproduce, trace root cause, compare working patterns, test one hypothesis, then add a regression.
- Preserve existing tests and add the smallest layer-appropriate coverage that fails on regression.
- Use Vitest/Testing Library for helpers, components, routes, adapters, forms, navigation, localization, states, keyboard behavior, and accessible roles/names.
- Prefer observable behavior over implementation details; mock only genuine external boundaries.
- For substantial frontend changes run `npm run lint`, `npm run typecheck`, `npm run test:run`, and `npm run build`.
- Use Playwright for real flows, responsive screenshots, focus, navigation, and visual comparison.
- Verify UI at 390px, 320px, 430px, 768px, and desktop; test affected Arabic RTL and English LTR flows.
- Use pytest for schemas, services, endpoints, auth, ownership, transactions, and domains. Run focused tests then full suite when practical.
- Use PostgreSQL concurrency tests for locking/exclusion changes; SQLite cannot prove production race safety.
- Migration checks include one head, upgrade, safe downgrade/re-upgrade, constraints, indexes, and data preservation.
- Definition of Done: required states work; tests failed first then pass; lint/typecheck/tests/build and relevant backend checks pass; responsive, bidi, keyboard, focus, announcements, contrast, reduced motion, touch, loading/empty/error states are verified; references were inspected/compared; diff is scoped; results and skipped checks are reported honestly.
