# MAL3ABY Skill Installation Plan

Prepared for Prompt 2. Do not duplicate generic skills inside project-specific skills.

## Current local inventory

- Project: `caveman` only.
- User: `find-skills`, `caveman`, Codex system creation/installation skills.
- Plugin equivalents: `control-in-app-browser` for browser control and `review-agent` for defect-first code review.
- Missing locally: general web-design, React/Next.js practices, testing, Playwright, security, and systematic-debugging skills.

## Install trusted generic skills first

Review upstream contents before installation, then install at user level:

```powershell
npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines -g -y
npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices -g -y
npx skills add https://github.com/openai/skills --skill playwright -g -y
npx skills add https://github.com/openai/skills --skill security-best-practices -g -y
npx skills add https://github.com/obra/superpowers --skill systematic-debugging -g -y
npx skills add https://github.com/obra/superpowers --skill test-driven-development -g -y
```

Keep the installed `review-agent`; do not add a duplicate code-review skill unless a later workflow specifically requires review-request orchestration.

## Create four project-scoped skills

Create these under `D:\mal3by\.agents\skills` after the generic skills are installed:

1. `mal3by-design-system`: MAL3ABY brand, approved logo usage, tokens, surfaces, typography, iconography, and component invariants.
2. `mal3by-mobile-ux`: mobile-first viewport, safe-area, keyboard, touch-target, short-height, navigation, and RTL/LTR acceptance checks.
3. `mal3by-frontend`: repository routes, API-preservation rules, auth/session boundaries, component conventions, commands, and page-by-page change scope.
4. `mal3by-accessibility`: MAL3ABY-specific bilingual semantics, focus order, announcements, bidi values, contrast, and manual acceptance checklist.

These skills should reference installed generic skills rather than repeat their guidance. Initialize each with the Codex `skill-creator` scripts, add only required references/assets, then run `quick_validate.py` for every skill. Brand assets must come from approved project files; do not invent or redraw the logo.
