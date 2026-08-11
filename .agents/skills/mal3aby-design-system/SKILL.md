---
name: mal3aby-design-system
description: Apply and review MAL3ABY visual identity, design tokens, shared UI primitives, and state patterns. Use for UI implementation, component styling, visual reviews, branding, approved reference-image work, or changes to globals.css and frontend UI components.
---

# MAL3ABY Design System

- Spell the product `MAL3ABY`. Treat other spellings in legacy code as debt, not approved identity.
- Inspect every approved reference image before implementation. Treat it as visual truth while preserving backend contracts and working behavior.
- Use an approved repository logo unchanged. No verified logo asset currently exists; `BrandLogo` and `AuthBrand` are provisional code marks. Keep replacement isolated and never redraw or claim approval.
- Read `frontend/src/app/globals.css`, affected primitives, and `docs/frontend/design-system-gap-analysis.md` first.
- Preserve the dark-first sports identity: `--bg-app`, layered `--surface-*`, semantic text, borders, focus, status colors, and electric `--brand` green.
- Use shared tokens for color, typography, spacing, radii, shadows, motion, layout, touch size, and safe areas. Add reusable semantic tokens; do not scatter one-off values.
- Keep Arabic and English typography metrics intentional. Use logical CSS properties and the shared spacing scale.
- Reuse UI primitives for buttons, inputs, cards/surfaces, dialogs/drawers, statuses, skeletons, empty states, and errors. Extend repeated behavior; do not abstract trivial markup.
- Cover default, hover, active, focus-visible, disabled, loading, error, and success states where applicable.
- Use cards and elevation for hierarchy, a coherent icon family, and mirrored directional icons in RTL.
- Prefer stable skeletons, compact action spinners, honest empty states, and localized recoverable errors.
- Keep motion restrained and respect `prefers-reduced-motion`.
- Verify hierarchy, typography, spacing, controls, CTA placement, safe areas, RTL/LTR, overflow, and vertical balance. Capture comparable screenshots when a reference exists.
- Pair with `mal3aby-mobile-ux`, `mal3aby-frontend`, `mal3aby-accessibility`, `web-design-guidelines`, and `vercel-react-best-practices` as applicable.
