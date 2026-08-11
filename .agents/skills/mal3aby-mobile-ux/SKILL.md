---
name: mal3aby-mobile-ux
description: Design, implement, and verify MAL3ABY mobile-first responsive experiences. Use for layouts, navigation, forms, sheets, dialogs, safe areas, virtual keyboards, scrolling, responsive density, PWA or offline UX, loading UX, performance, and viewport testing.
---

# MAL3ABY Mobile UX

- Design at 390px first; verify 320px minimum, 430px larger phone, 768px tablet, and desktop sanity.
- Build a sports-app experience, not a compressed desktop page. Inspect `globals.css`, product shell, bottom navigation, mobile action bar, and affected routes.
- Prevent horizontal overflow in RTL and LTR. Use logical properties, `100dvh`, and `env(safe-area-inset-*)`.
- Preserve the 44px `--touch-target`; keep adjacent targets separable.
- Let short screens scroll. Never trap primary actions below the fold or beneath fixed navigation.
- Keep forms usable with the virtual keyboard: no rigid height, no remount while typing, correct autocomplete/input modes, and visible focused fields.
- Use bottom navigation only for primary application destinations and hide it on focused entry/auth flows.
- Use Drawer for compact secondary tasks and Dialog for decisions. Preserve focus trap, Escape, background blocking, and trigger-focus restoration.
- Adapt content density and action layout at breakpoints; do not merely shrink typography.
- Provide stable loading, actionable retry, and honest offline/network states.
- Minimize mobile JavaScript, avoid waterfalls and layout shift, and use approved local assets for critical flows.
- Treat manifest, installability, service worker, and offline caching as unimplemented until repository evidence exists.
- Verify long Arabic/English copy, short height, zoom, keyboard, reduced motion, touch size, safe areas, overlays, and scroll.
- Use Playwright for required real-browser flows/screenshots and pair with design-system and accessibility skills.
